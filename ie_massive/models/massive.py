#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
import base64
import csv
import logging

import ssl
import xlrd
import xlwt
import xmlrpc.client as xmlrpclib
from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger('IE MASSIVE V13')
SOCK = False
DB = False
UID = False
PASSWORD = False


class ImportExportMassive(models.Model):
    _name = 'ie.massive'
    _description = 'IE Massive'

    name = fields.Char(string='Import/Export name', copy=False)
    line_ids = fields.One2many('ie.massive.lines', 'massive_id', string='Models', copy=True)
    url = fields.Char(string='Url')
    port = fields.Char(string='Port')
    user = fields.Char(string='User')
    password = fields.Char(string='Password')
    database = fields.Char(string='Database')
    services = fields.Char(string="Services")

    def getFilter(self):
        filters = {}
        for fil in self.env['ie.massive.filter'].search([]):
            filters[fil.model_id.model] = fil.filter
        return filters

    def connectOdooWebServices(self):
        ssl._create_default_https_context = ssl._create_unverified_context
        self.database = self.env.cr.dbname if not self.database else self.database
        self.user = self.env.user.login if not self.user else self.user
        self.url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') if not self.url else self.url
        sock_common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(self.url))
        uid = sock_common.authenticate(self.database, self.user, self.password, {})

        if not uid:
            raise UserError(_('Invalid username or password.'))

        return xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(self.url)), uid, self.database, self.password

    def export_action(self):
        global SOCK, UID, DB, PASSWORD
        SOCK, UID, DB, PASSWORD = self.connectOdooWebServices()
        for line in self.line_ids.filtered(lambda x: x.process):
            FIELDS_RECORDS = SOCK.execute_kw(DB, UID, PASSWORD, 'ir.model.fields', 'search_read',
                                             [[['readonly', '=', False], ['model_id', '=', line.model_id.id]]],
                                             {'fields': ['field_description', 'name', 'relation', 'readonly', 'ttype']})

            MY_FIELD_RECORDS = {}
            for record in FIELDS_RECORDS:
                MY_FIELD_RECORDS[record['name']] = record
            ATTRIBUTES = list(MY_FIELD_RECORDS.keys())
            ATTRIBUTES.insert(0, 'id')

            IDS_RECORDS = SOCK.execute_kw(
                DB, UID, PASSWORD, line.model_id.model, 'search', eval(line.condition))

            READ_RECORDS = SOCK.execute_kw(DB, UID, PASSWORD, line.model_id.model, 'read',
                                           [IDS_RECORDS], {'fields': ATTRIBUTES})
            filters = self.getFilter()
            mapp = {}
            for record in READ_RECORDS:
                for field in FIELDS_RECORDS:
                    fields = [x[0] for x in eval(filters.get(field.get('relation')))] if filters.get(
                        field.get('relation')) else False
                    if field.get('relation') and field.get('name') in record.keys() and record.get(
                            field.get('name')) and fields:
                        nval = False
                        for x in mapp.get(field.get('name')) or []:
                            if x[0] == record[field.get('name')]:
                                nval = x[1]
                        if not nval:
                            id = record.get(field.get('name'))[0] if type(
                                record.get(field.get('name'))) == list else record.get(field.get('name'))
                            READ_RELATIONS = SOCK.execute_kw(DB, UID, PASSWORD, field.get('relation'), 'read',
                                                             [id], {'fields': fields})
                            if READ_RELATIONS:
                                if field.get('name') not in mapp.keys():
                                    mapp[field.get('name')] = []
                                mapp[field.get('name')].append([record[field.get('name')], nval])
                                nlj = []
                                for f in fields:
                                    nd = READ_RELATIONS[0].get(f)
                                    if type(READ_RELATIONS[0].get(f)) == list:
                                        nd = READ_RELATIONS[0].get(f)[
                                            1]  # TODO pendiente cambiar logica para que use los filtros del modelo padre
                                    nlj.append(str(nd))
                                nval = '|'.join(nlj)
                        if nval:
                            record[field.get('name')] = nval

            path = '/tmp/' + line.model_id.model + '.csv'
            line.write({'file': False})
            with open(path, 'w') as csvfile:
                fieldnames = ATTRIBUTES
                writer = csv.DictWriter(
                    csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for record in READ_RECORDS:
                    writer.writerow(record)
            line.write(
                {'filename': 'export_file_' + line.filename or line.description + '.txt',
                 'file': base64.b64encode(open(path, 'rb').read())})

    def import_action(self):
        global SOCK, UID, DB, PASSWORD
        SOCK, UID, DB, PASSWORD = self.connectOdooWebServices()
        errors = None
        for line in self.line_ids:
            if line.process:
                errors = line.migrate()
        return errors


class ImportExportMassiveLines(models.Model):
    _name = 'ie.massive.lines'
    _description = 'IE Massive Lines'

    massive_id = fields.Many2one('ie.massive', string='Massive', ondelete='cascade')
    model_id = fields.Many2one('ir.model', string='Model', required=True)
    file = fields.Binary(string='File', copy=False, required=False)
    filename = fields.Char(string='Filename')
    time_real = fields.Float(string='Time real')
    record_quantity = fields.Float(string='Record qty')
    create_quantity = fields.Float(string='Create qty')
    write_quantity = fields.Float(string='Write qty')
    time_record = fields.Float(string='Time record')
    errors = fields.Text(string='Errors', readonly=True)
    errors_file = fields.Binary(string='Errors file', readonly=True)
    errors_filename = fields.Char(string='Errors filename')
    to_load = fields.Boolean(string='Load', default=True)
    to_update = fields.Boolean(string='Write', default=True)
    to_create = fields.Boolean(string='Create', default=False)
    map_ids = fields.One2many('ie.massive.map', 'import_id', string='Map', copy=True)
    description = fields.Char(string='Description')
    condition = fields.Char(string='Condition', default="[[[1,'=',1]]]")
    process = fields.Boolean(string='Process', default=True)

    def getFilterDefault(self):
        return '''[('name','=','{}')]'''

    def getFilter(self):
        filters = {}
        for f in self.env['ie.massive.filter'].search([]):
            filters[f.model_id.model] = f.filter
        return filters

    @api.onchange('to_create')
    def set_load(self):
        self.to_load = False

    @api.onchange('to_load')
    def set_create(self):
        self.to_create = False

    def get_headers(self, first_line):
        for x in first_line:
            if '/' in x:
                first_line.pop(first_line.index(x))
                self.get_headers(first_line)
        return first_line

    def getId(self, model, index, record, recordn, attributes, field, title, map, filters):
        id = False
        for z in map:
            id = False
            if z[1] == record and index == z[0]:
                id = z[2]
                break
        fnp = ''
        if not id:
            condition, escape = [], True
            filters = filters.get(model)
            if not filters:
                filters = self.getFilterDefault()
            record = []
            if filters.count('{}') > 1 and field:  # filtros compuestos
                for f in eval(filters):
                    for attr in attributes:
                        if field + '/' + f[0] in attr:  # TODO pendiente de pasar a expr
                            fnp = attr
                            index = attributes.index(attr)
                            record.append(recordn[index])
            else:
                record = [recordn[index]]
            if not len(record):
                raise UserError(_(' Verify titles titles: {}, filters: {}').format(str(record),str(filters)))
            if filters.count('{}') != len(record):
                record = [record] if type(record) == str else record
                record *= filters.count('{}')
            condition.append(list(eval(filters.format(*record))))
            try:
                id = SOCK.execute_kw(DB, UID, PASSWORD,
                                     model, 'search',
                                     condition)
            except:
                pass
            if not id and title and type(record) == str:
                record = record.title()
                self.getId(model, index, record, recordn, attributes, False,
                           True, False, filters)
            if id:
                map.append((index, record[0], id[0]))
        return (id, fnp) if type(id) == list else ([id], fnp)

    def getValue(self, model, index, record, title, map, filters):
        value = False
        if not value:
            condition, escape = [], True
            filters = filters.get(model)
            record = [x.strip() for x in str(record).split('|')] if '|' in str(record) else str(record)
            if filters.count('{}') != len(record):
                record = [record] if type(record) == str else record
                record *= filters.count('{}')
            condition.append(list(eval(filters.format(*record))))
            if not condition:
                condition.append([eval(self.getFilterDefault()[0].format(record))])
            try:
                id = SOCK.execute_kw(DB, UID, PASSWORD,
                                     model, 'search',
                                     condition)
            except:
                pass
            if not id and title and type(record) == str:
                record = record.title()
                self.getId(model, index, record, False, False, False,
                           True, False, filters)
        return id if type(id) == list else [id]

    def mapRecord(self, record, map, attributes_final):
        w = 0
        ind = []
        for m in map:
            try:
                index = attributes_final.index(m.fields)
                if index > -1:
                    ind.append(index)
            except ValueError:
                pass
        for x in record:
            if w in list(set(ind)):
                for y in map:
                    if y.origin == x and w == attributes_final.index(y.fields):
                        record[attributes_final.index(y.fields)] = y.destination
                        break
            w += 1
        return record

    def getErrors(self, errors):
        errors_global, message, moreinfo, domain = '', '', '', ''
        if type(errors) == dict:
            for x in errors.get('messages', ''):
                try:
                    message = str(x.get('message', ''))
                    moreinfo = str(x.get('moreinfo', ''))
                    domain = str(moreinfo.get('domain', ''))
                    domain = str(domain.pop()[2] or '')
                except:
                    pass
                errors_global += message + ' moreinfo: ' + moreinfo + ' domain: ' + domain + '\n'

        return errors_global

    def getFieldType(self, model, fields):
        return SOCK.execute_kw(DB, UID, PASSWORD, 'ir.model.fields', 'search_read',
                               [[['model_id.model', '=', model],
                                 ['name', 'in', fields]]],
                               {'fields': ['name', 'ttype', 'relation']})

    def getIndex(self, att, ft):
        return att[len(ft.get('name')) + 1:]

    def deleteRecord(self, record, positions):
        for delete in positions:
            record.pop(delete)
        return record

    def setAttributes(self, attributes_final):
        for atr in attributes_final:
            index = attributes_final.index(atr)
            if '_ids' not in attributes_final[index] and '/' not in attributes_final[index]:
                attributes_final[index] = attributes_final[index].replace('/.id', '').replace('_id', '_id/.id')
        return attributes_final

    def getUpdate(self, line, position, record, condition):
        condition_final = []
        if str(condition).count('{}') >= len(position):
            position *= str(condition).count('{}')
        condition_final.append(list(eval(str(condition).format(*[record[x] for x in position]))))
        id_record = SOCK.execute_kw(DB, UID, PASSWORD, line.model_id.model, 'search_read', condition_final,
                                    {'fields': ['name']})
        to_update = True if len(id_record) > 0 else False
        return to_update, id_record

    def setConvertIds(self, to_update, recordn, field_type, attributes,
                      attributes_final, filters, map, position):
        dele = False
        errors_record = ''
        tl = False
        record = recordn.copy()
        for cd in attributes:
            for ft in field_type:
                if ((ft.get('name') == cd and cd != tl) or (
                        cd.startswith(ft.get('name')) and '/' in cd and not tl)) and ft.get('ttype') in ['many2one',
                                                                                                         'one2many']:
                    model = ft.get('relation')
                    if ft.get('ttype') in ['one2many']:
                        model = self.getFieldType(model, [cd.replace(ft.get('name') + '/', '')])[0].get('relation')

                    if not model:
                        break

                    index = attributes.index(cd)
                    if not record[index]:
                        break
                    id, fnp = self.getId(model, index, record[index], recordn, attributes_final, ft.get('name'),
                                         False, map, filters)
                    if id:
                        id = id.pop()
                        if fnp:
                            tl = fnp.replace('/', '')
                            if tl not in attributes:
                                attributes_final.append(tl)
                                attributes.append(tl)
                                index = attributes_final.index(tl)
                                position.insert(0, index)
                            recordn.append(int(id))
                            record.append(int(id))
                        else:
                            if '.id' not in attributes_final[index] and not to_update:
                                attributes_final[index] = attributes[index] + '/.id'
                            record[index] = int(id)
                        # map.append((index, recordn[index], id))
                        break
                    elif model:
                        # errors_record += 'Not found record for {} (column {}).\n'.format(record[index], attributes_final[index])
                        errors_record += 'Not found record for,{},{}\n'.format(attributes_final[index], record[index])
                        dele = True
        return record, dele, errors_record

    def getPositionToDelete(self, field_type, attributes, attrs_correct=[], positions_real=[]):
        positions = []
        fields = []
        if not attrs_correct:
            for field_not_find in field_type:
                if field_not_find.get('ttype') == 'one2many':  # search fields o2m
                    for attr in attributes:
                        if attr.startswith(field_not_find.get('name')):
                            fields.append(attr.replace(field_not_find.get('name') + '/', ''))
                    for field in self.getFieldType(field_not_find.get('relation'), fields):
                        if field.get('name') in fields:
                            attrs_correct.append(field_not_find.get('name') + '/' + field.get('name'))
                else:
                    attrs_correct.append(field_not_find.get('name'))
        for field_attr in attributes:
            if (field_attr not in attrs_correct or field_attr.strip() == '') and not len(
                    list(filter(lambda x: x, [x.startswith(field_attr) for x in attrs_correct]))):
                positions.append(attributes.index(field_attr))
        attributes = self.deleteRecord(attributes, sorted(list(set(positions)), reverse=True))
        positions_real += positions
        if '' in attributes:
            self.getPositionToDelete(field_type, attributes, attrs_correct, positions_real)
        return attributes, sorted(list(set(positions_real)), reverse=True)

    def create_record(self, attributes_final, datos):
        def _update_data(data_lines, datas, global_datas):
            if data_lines:
                datas.update({key: [(0, 0, x) for x in data_lines]})
            if datas:
                global_datas.append(datas)
            return datas, global_datas
        titles = []
        for title in attributes_final:
            titles.append(title.replace('/.id', ''))
        # convert to dict
        data_lines = []
        parent = False
        datas = {}
        global_datas = []
        key = False
        for data in datos:
            lines = {}
            if not parent or (parent != data[0] and data[0] != ''):
                parent = data[0]
                datas, global_datas = _update_data(data_lines, datas, global_datas)
                lines, datas, data_lines = {}, {}, []

            for title in titles:
                index = titles.index(title)
                if '/' in title:
                    lines[title[title.find('/') + 1:]] = data[index]
                    key = title[:title.find('/')]
                elif data[0] != '':
                    datas[title] = data[index]
            if lines:
                data_lines.append(lines)
        datas, global_datas = _update_data(data_lines, datas, global_datas)
        return global_datas

    def _get_model(self, n, field_type):
        for f in field_type:
            if f.get('ttype') not in ['many2one', 'one2many', 'many2many']:
                if f.get('name') == n:
                    break
                else:
                    continue
            if f.get('name') == n:
                return f.get('relation')
        return False

    def _get_field_for_model(self, field_type, model):
        fpos = ''
        for f in field_type:
            if f.get('relation') == model:
                fpos = f.get('name')
                break
        return fpos

    def addIdModelRelational(self, ndr, record, record_with_fields_filter, attributes_final, filters):
        errors_record = ''
        positions = []
        model = self.model_id.model
        field_type = self.getFieldType(model, list(ndr.keys()))
        for n in ndr.keys():
            if self._get_model(n, field_type):
                model = self._get_model(n, field_type)
            next = True
            if filters.get(model):
                for x in eval(filters.get(model)):
                    # if n in n + '.'.x or x.startswith(n):
                    ndr_list = []
                    if type(ndr.get(n)) == dict:
                        ndr_list = list(ndr.get(n, {}).keys())
                    if x[0] in ndr_list or x[0].startswith(n):
                        next = False
                        break
            if next:
                continue
            nd = ndr.get(n)
            if type(nd) == dict:
                for j in nd:
                    positions.append(nd.get(j))
            else:
                positions.append(nd)
        if not filters.get(model):
            raise UserError('No found filter for model {}'.format(model))
        condition = list(eval(str(filters.get(model)).format(*[record_with_fields_filter[x] for x in positions])))
        id = SOCK.execute_kw(DB, UID, PASSWORD, model, 'search', [condition])
        if id:
            [id] = id
            fpos = self._get_field_for_model(field_type, model)
            if fpos:
                x = attributes_final.index(fpos + '/.id')
                record.insert(x, id)
            else:
                record.append(id)
        else:
            errors_record += 'Not found record for {} \n'.format(
                '-'.join([record_with_fields_filter[x] for x in positions]))
        return errors_record, record

    def migrate(self):
        # TODO pendiente pasar parametros a contexto en metodos como getValue, getId, ConvertIsd, etc..
        errors_global, datos, attributes, records, position, header, c, l, start, errors, limit = '', [], [], [], [], 0, 1, 0, datetime.now(), '', 0
        ext = self.filename.split('.')[-1:]
        if len(ext):
            ext = ext[0]
        if ext in ['xlsx', 'xls']:  # xlsx
            book = xlrd.open_workbook(file_contents=base64.b64decode(self.file))
            shl = book._sheet_list[0]
            records = shl._cell_values
        elif ext in ['csv']:  # csv
            string_document = base64.b64decode(self.file).decode("utf-8")
            rows = string_document.split('\r\n') if '\r\n' in string_document else string_document.split('\n')
            for row in rows:
                if row:
                    records.append(row.split(','))
        else:
            raise UserError(
                _('''The file to be imported has an unsupported format. Supported formats: xlsx, xls and csv.'''))
        self.errors = errors
        parent = False
        map = []  # list value search informed
        header = 0
        condition = []
        positions = []
        ndr = {}
        mapp = False
        max = False
        totals = len(records)
        data_write = {}
        filters = self.getFilter()
        for record in records:
            if len(record) <= 1:
                raise UserError(_('Row {} has a length of {}. Please verify.').format(str(c), str(len(record))))
            max = len(record) if not max else max
            if len(record) != max:
                raise UserError(
                    _('''there is a file row that has iterma length greater than the maximum {}. Line: {}''').format(
                        str(max), str(c)))

            _logger.info(_(
                '''{c}/{len} => {porc:.2f}% (Estimated time of preparation: {time:.2f} min, accumulated time: {time2:.2f}) min''').format(
                c=str(c), len=str(totals), porc=c / totals * 100,
                time=((datetime.now() - start).total_seconds() / c * (totals - c)) / 60,
                time2=(datetime.now() - start).total_seconds() / 60)
            )
            to_update = False
            if header < 1:
                attributes = record[:]
                if not attributes:
                    raise UserError(_('A column of titles was detected, please check the file separator.'))
                if list(filter(lambda x: type(x) != str, attributes)):
                    raise UserError(_('Columns must be a string of characters.'))
                first_line_field = list(set([x[:x.find('/') if x.find('/') > 0 else len(x)] for x in attributes]))
                field_type = self.getFieldType(self.model_id.model, first_line_field)
                attributes, positions = self.getPositionToDelete(field_type, attributes, [], [])

                filters2 = filters.get(self.model_id.model)
                if not filters2:
                    filters2 = self.getFilterDefault()

                # agregar titulos compuestos para luego reemplazar el campo por el id que corresponde segun los filtros
                # TODO verificar que el campo sea parte del filtro, para evitar que se envíen campos con . y no existan en el modelo
                for f in record:
                    if '.' in f:
                        k, k2 = f.split('.')
                        if k not in ndr.keys():
                            ndr[k] = {}
                        ndr[k][k2] = record.index(f)
                        if k not in attributes:
                            attributes.append(k)
                if ndr.keys():
                    for k in record:
                        if '.' not in k and k not in ndr.keys():
                            ndr[k] = record.index(k)
                condition = filters2 = eval(filters2)
                position = []
                filter_correct = True
                for x in filters2:
                    if x[0] in record:
                        position.append(record.index(x[0]))

                if not filter_correct:
                    raise UserError(_(
                        '''the filter of model {} contains a field that does not exist in the title of the file''').format(
                        self.model_id.model))

                attributes_final = attributes[:]
                first_line = attributes_final[:]
                mapp = self.map_ids
                headers = self.get_headers(first_line)
                header += 1
            else:
                c += 1
                self.record_quantity += c
                self.time_real = (datetime.now() - start).total_seconds() / 60

                attributes_final = self.setAttributes(attributes_final)
                record_with_fields_filter = record[:]
                record = self.deleteRecord(record, positions)
                record_with_fields_filter = self.mapRecord(record_with_fields_filter, mapp,
                                                           attributes) if mapp else record_with_fields_filter
                record_old = self.mapRecord(record, mapp, attributes) if mapp else record
                record, dele, errors_record = self.setConvertIds(to_update, record_old, field_type,
                                                                 attributes, attributes_final,
                                                                 filters, map, position)
                if ndr.keys():
                    errors_record, record = self.addIdModelRelational(ndr, record,
                                                                      record_with_fields_filter,
                                                                      attributes_final, filters)

                if errors_record:
                    errors_global += errors_record
                    continue
                if not dele and position:
                    to_update, id_record = self.getUpdate(self, position, record_with_fields_filter, condition)
                    if not to_update and (self.to_load or self.to_create):
                        if not parent or parent != record[0]:
                            parent = record[0]
                        elif attributes != headers:
                            for x in attributes:
                                if x in headers:
                                    i = attributes.index(x)
                                    record[i] = ''

                    if not dele:
                        if to_update and self.to_update:
                            my_id = id_record[0]['id']
                            new_data = {}
                            for i in range(0, len(record)):
                                new_data[attributes[i]] = record[i]
                            data_write[my_id] = new_data
                        elif (self.to_load or self.to_create) and not to_update:
                            datos.append(record)

        _logger.info(_('Preparation finished:') + str(datetime.now() - start))
        if datos:
            if self.to_create:
                global_datas = self.create_record(attributes_final, datos)
                for data in global_datas:
                    errors = SOCK.execute_kw(DB, UID, PASSWORD, self.model_id.model, 'create',
                                             [data])
            elif self.to_load:
                datas = []
                # TODO pendiente quitas esta lógica para hacer el importador generico
                if self.model_id.model == 'account.move':
                    i = attributes_final.index('line_ids/partner_id/.id')
                    partner_id = datos[0][i] if datos[0][i] else False
                    kpos = []
                    filters = eval(filters.get(self.model_id.model)) if filters.get(self.model_id.model) else eval(
                        self.getFilterDefault())
                    for x in filters:
                        if x[0] not in attributes:
                            raise UserError(
                                _('The {} attribute is not found within the titles of the file to be imported'.format(
                                    x[0])))
                        kpos.append(attributes.index(x[0]))

                    if datos:
                        key = '-'.join([str(datos[0][x]) for x in kpos])

                    debit, credit = 0, 0
                    ai = attributes_final.index(
                        'line_ids/analytic_account_id/.id') if 'line_ids/analytic_account_id/.id' in attributes_final else False
                    ni = attributes_final.index(
                        'line_ids/partner_id/.id') if 'line_ids/partner_id/.id' in attributes_final else False

                    di = attributes_final.index('line_ids/debit')
                    ci = attributes_final.index('line_ids/credit')
                    if ai:
                        ai_first = SOCK.execute_kw(DB, UID, PASSWORD, 'account.analytic.account', 'search', [[]],
                                                   {'limit': 1})

                    for data in datos:
                        tkey = '-'.join([str(data[x]) for x in kpos])
                        if tkey != key and tkey and tkey.replace('-', '') != '':
                            # if self.model_id.model == 'account.move':
                            amount = debit - credit
                            if amount != 0:
                                nl = datas[len(datas) - 1].copy()
                                for f in first_line:
                                    nl[attributes.index(f)] = ''
                                if ai:
                                    nl[ai] = ai_first[0]
                                if ni:
                                    nl[ni] = partner_id  # self.env.user.company_id.partner_id.id
                                nl[di] = 0 if amount > 0 else -amount
                                nl[ci] = amount if amount > 0 else 0
                                datas.append(nl)
                            l += 1
                            errors = SOCK.execute_kw(DB, UID, PASSWORD, self.model_id.model, 'load',
                                                     [attributes_final, datas])
                            key = '-'.join([str(data[x]) for x in kpos])
                            datas = []
                            # if self.model_id.model == 'account.move':
                            debit, credit = 0, 0
                        datas.append(data)
                        # TODO por ajustar para que no sea hardcode
                        # if self.model_id.model == 'account.move':
                        if di or ci:
                            debit += float(data[attributes_final.index('line_ids/debit')] or 0.0)
                            credit += float(data[attributes_final.index('line_ids/credit')] or 0.0)
                    amount = debit - credit
                    if not self.env.user.company_id.currency_id.is_zero(amount):
                        nl = datas[len(datas) - 1].copy()
                        for f in first_line:
                            nl[attributes.index(f)] = ''
                        if ai:
                            nl[ai] = ai_first[0]
                        if ni:
                            nl[ni] = partner_id  # self.env.user.company_id.partner_id.id
                        nl[di] = 0 if amount > 0 else -amount
                        nl[ci] = amount if amount > 0 else 0
                        datas.append(nl)
                else:
                    datas = datos
                c += 1
                l += 1
                errors = SOCK.execute_kw(DB, UID, PASSWORD, self.model_id.model, 'load',
                                         [attributes_final, datas])
        w = 0
        if self.to_update:
            for dato in data_write:
                w += 1
                new = data_write.get(dato)
                new.pop('vat', None)
                _logger.info(_('Updated {} from {}').format(str(w), len(data_write)))
                SOCK.execute_kw(DB, UID, PASSWORD, self.model_id.model, 'write', [[int(dato)], new])
        errors_global += self.getErrors(errors)
        data = errors_global.split('\r\n') if '\r\n' in errors_global else errors_global.split('\n')
        if data:
            filename = 'errors.xls'
            path = '/tmp/' + filename

            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet('Errors')
            # titles
            f = 0
            col = 0
            for t in ['message', 'field', 'value']:
                worksheet.write(f, col, t)
                col += 1

            f += 1
            for r in data:
                col = 0
                for nr in r.split(','):
                    worksheet.write(f, col, nr)
                    col += 1
                f += 1
            workbook.save(path)
            self.write(
                {'errors_filename': filename, 'errors_file': base64.b64encode(open(path, 'rb').read())})

        self.record_quantity = c - 1
        self.create_quantity = l
        self.write_quantity = w
        self.time_record = self.time_real / (l + w) if l + w > 0 else 1
        self.errors = errors_global
        self.env.cr.commit()

        _logger.info(_('Import finished:') + str(datetime.now() - start))
        return True


class ImportExportMassiveLinesCondition(models.Model):
    _name = 'ie.massive.lines.condition'
    _description = 'IE Massive Lines Condition'

    field = fields.Char(string='Field', required=True)
    condition = fields.Char(string='Condition', required=True)
    line_id = fields.Many2one('ie.massive.lines', string='Lines')


class ImportExportMassiveMap(models.Model):
    _name = 'ie.massive.map'
    _description = 'IE Massive Map'

    origin = fields.Char(string='Origin', required=True)
    import_id = fields.Many2one('ie.massive.lines', string='Import')
    destination = fields.Char(string='Destination', required=True)
    fields = fields.Char(string='Fields', required=True)
