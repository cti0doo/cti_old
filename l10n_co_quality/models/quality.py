# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta

from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

from odoo import models, fields, api

_logger = logging.getLogger('MILK INOVICE')


class RESPartnerDistance(models.Model):
    _inherit = 'res.partner'

    distance = fields.Float(string='Distance')


class QualityCheck(models.Model):
    _inherit = 'quality.check'

    partner_id = fields.Many2one('res.partner', string='Partner',
                                 index=True, required=False)
    move_id = fields.Many2one('account.move', string='Invoice',
                                 index=True, required=False)
    production_id = fields.Many2one('mrp.production', string='Production',
                                    index=True, required=False)

    
    def name_get(self):
        result = []
        for record in self:
            if record.name and record.title:
                result.append((record.id, record.name + ' - ' + record.title))
            if record.name and not record.title:
                result.append((record.id, record.name))
        return result


class QualityPoint(models.Model):
    _inherit = 'quality.point'

    hygienic_quality = fields.Boolean(string='Hygienic quality', default=False)
    temperature = fields.Boolean(string='Temperature', default=False)
    sanitary_quality = fields.Boolean(string='Sanitary quality', default=False)
    certificate = fields.Boolean(string='Certificate', default=False)
    distance = fields.Boolean(string='Distance', default=False)
    transport = fields.Boolean(string='Transport', default=False)

    fat = fields.Boolean(string='Fat', default=False)
    protein = fields.Boolean(string='Protein', default=False)
    sng = fields.Boolean(string='SNG', default=False)
    st = fields.Boolean(string='Solidos totales', default=False)
    density = fields.Boolean(string='Density', default=False)

    
    def name_get(self):
        result = []
        for record in self:
            if record.name and record.title:
                result.append((record.id, record.name + ' - ' + record.title))
            if record.name and not record.title:
                result.append((record.id, record.name))
        return result


class MonthlyInventoryMovements(models.Model):
    _name = "monthly.inventory.movements"
    _description = "Monthly Inventory Movements"

    move_id = fields.Many2one('account.move', string='Invoice')
    m1 = fields.Float(string='January', default=0.0)
    m2 = fields.Float(string='February', default=0.0)
    m3 = fields.Float(string='March', default=0.0)
    m4 = fields.Float(string='April', default=0.0)
    m5 = fields.Float(string='May', default=0.0)
    m6 = fields.Float(string='June', default=0.0)
    m7 = fields.Float(string='July', default=0.0)
    m8 = fields.Float(string='August', default=0.0)
    m9 = fields.Float(string='September', default=0.0)
    m10 = fields.Float(string='October', default=0.0)
    m11 = fields.Float(string='November', default=0.0)
    m12 = fields.Float(string='December', default=0.0)
    accumulated = fields.Float(string='Accumulated', default=0.0)


class CompositionalInformation(models.Model):
    _name = "compositional.information"
    _description = "Compositional Information"

    move_id = fields.Many2one('account.move', string='Invoice')
    quality_id = fields.Many2one('quality.check', string='Quality check')
    product_id = fields.Many2one('product.product', string='Product')
    point_id = fields.Many2one('quality.point', string='Quality point')
    title = fields.Char(string='Quality')
    qna1 = fields.Float(string='Fortnight 1', default=0.0)
    qna2 = fields.Float(string='Fortnight 2', default=0.0)
    qna3 = fields.Float(string='Fortnight 3', default=0.0)
    avg = fields.Float(string='Average', default=0.0)


class ConceptsQuality(models.Model):
    _name = "concepts.quality"
    _description = "Concepts Quality"

    code = fields.Char(string='Code')
    name = fields.Char(string='Name')
    amount = fields.Float(string='Amount')
    code_python = fields.Text(string='Calc')


class DailyReception(models.Model):
    _name = "daily.reception"
    _description = "daily.reception"

    move_id = fields.Many2one('account.move', string='Invoice')
    value = fields.Float(string='Value', default=0.0)
    d1 = fields.Integer(string='Day 1', default=0)
    d2 = fields.Integer(string='Day 2', default=0)
    d3 = fields.Integer(string='Day 3', default=0)
    d4 = fields.Integer(string='Day 4', default=0)
    d5 = fields.Integer(string='Day 5', default=0)
    d6 = fields.Integer(string='Day 6', default=0)
    d7 = fields.Integer(string='Day 7', default=0)
    d8 = fields.Integer(string='Day 8', default=0)
    d9 = fields.Integer(string='Day 9', default=0)
    d10 = fields.Integer(string='Day 10', default=0)
    d11 = fields.Integer(string='Day 11', default=0)
    d12 = fields.Integer(string='Day 12', default=0)
    d13 = fields.Integer(string='Day 13', default=0)
    d14 = fields.Integer(string='Day 14', default=0)
    d15 = fields.Integer(string='Day 15', default=0)
    d16 = fields.Integer(string='Day 16', default=0)
    total_value = fields.Float(string='Total value', default=0.0)
    total = fields.Float(string='Total', default=0.0)


class MRPInvoice(models.Model):
    _inherit = 'account.move'

    base = fields.Float(string='Base', default=0.0)
    mim_id = fields.One2many('monthly.inventory.movements', 'move_id',
                             string='Monthly Inventory Movements')
    ci_id = fields.One2many('compositional.information', 'move_id',
                            string='Compositional Information')
    dr_id = fields.One2many('daily.reception', 'move_id',
                            string='Daily Reception')
    cq_id = fields.Many2many('concepts.quality', 'invoice_quality_rel',
                             'move_id', 'cq_id', 'Concepts quality')
    amount_quality = fields.Float(string='Amount quality', readonly=True)
    type_test = fields.Selection([('1', 'Protein & Fat'), ('2', 'Total solids')],
                                 string='Type of test')
    quality_ids = fields.One2many('quality.check', 'move_id',
                                  string='Quality checks')

    @api.onchange('partner_id')
    def partner_order_change(self):
        if self.partner_id:
            purchase_ids = self.env['purchase.order'].search([
                ('partner_id', 'child_of', self.partner_id.id),
                ('invoice_status', '=', 'to invoice'),
                ('state', 'in', ['done', 'purchase']),
                ('date_order', '<=', self.invoice_date)
            ])
            self.invoice_line_ids = False
            for purchase in purchase_ids:
                new_lines = self.env['account.move.line']
                for line in purchase.order_line:
                    data = self._prepare_invoice_line_from_po_line(line)
                    new_line = new_lines.new(data)
                    new_line._set_additional_fields(self)
                    new_lines += new_line

                self.invoice_line_ids += new_lines
                self.payment_term_id = purchase.payment_term_id
                self.env.context = dict(self.env.context, from_purchase_order_change=True)
                self.purchase_id = False
        return {}

    def calculate(self):
        self.amount_quality = 0
        price = 0
        for concepts in self.cq_id:
            if concepts.code != '999':
                localdict = {}
                localdict['result'] = 0
                localdict['invoice'] = self
                safe_eval(concepts.code_python, localdict, mode='exec', nocopy=True)
                concepts.amount = localdict.get('result', 0)
                self.amount_quality += concepts.amount
        c = 0
        for products in self.invoice_line_ids:
            price += products.price_unit
            c += 1
        diff = (price / (c or 1)) - self.amount_quality
        self.amount_quality += diff
        for concepts in self.cq_id:
            if concepts.code == '999':
                concepts.code_python = 'result = %s' % diff
                concepts.amount = diff

    def invoice_calculate(self, vals=None):
        _logger.info('mrp_invoice')
        mim, dr, ci, drt = {}, {}, {}, {}
        invoice_date = None
        data = self.env['quality.check'].search([('partner_id', '=', self.partner_id.id), (
            'product_id', 'in', [x.product_id.id for x in self.invoice_line_ids])])
        _logger.info(data)
        self.quality_ids = [(3, x.id) for x in data]
        self.quality_ids = [(4, x.id) for x in data]
        if not self.invoice_date and vals:
            invoice_date = vals.get('invoice_date')
        if not invoice_date:
            invoice_date = datetime.today()
            vals['invoice_date'] = invoice_date
        product = []
        for line in self.invoice_line_ids:
            if line.product_id.id not in product:
                product.append(line.product_id.id)

        # monthly.inventory.movements
        move = self.env['stock.move'].search([
            ('product_id', 'in', product),
            ('state', '=', 'done')
        ])
        for mov in move:
            if mov.picking_id.picking_type_id.code == 'incoming':
                # account move for month
                if not self.invoice_date:
                    self.invoice_date = datetime.today()
                if str(self.invoice_date)[0:4] == str(mov.date_expected)[0:4]:
                    if 'm' + str(int(str(mov.date_expected)[5:7])) not in mim.keys():
                        mim['m' + str(int(str(mov.date_expected)[5:7]))] = mov.product_uom_qty
                        mim['c' + str(int(str(mov.date_expected)[5:7]))] = 1
                    else:
                        mim['m' + str(int(str(mov.date_expected)[5:7]))] += mov.product_uom_qty
                        mim['c' + str(int(str(mov.date_expected)[5:7]))] += 1
        # generar promedios
        mim['accumulated'] = 0.0
        for x in range(1, 13):
            mim['m' + str(x)] = mim.get('m' + str(x), 0) / (mim.get('c' + str(x), 1))
            mim['accumulated'] += mim['m' + str(x)]
        purchase = False
        if self.origin:
            origin = self.origin.split(', ')
            purchase = self.env['purchase.order'].search([('name', 'in', origin)])

        if purchase:
            for po in purchase:
                for line in po.order_line:
                    if 'd' + str(int(str(line.date_planned)[8:10])) not in drt.keys():
                        drt['d' + str(int(str(line.date_planned)[8:10]))] = line.product_qty
                    else:
                        drt['d' + str(int(str(line.date_planned)[8:10]))] += line.product_qty

        for x in sorted(drt, reverse=True):
            for y in sorted(range(1, 17), reverse=True):
                if 'd' + str(y) not in dr.keys():
                    dr['d' + str(y)] = drt[x]
                    break
        tlts = 0
        if purchase:
            for ddrl in dr:
                tlts += float(dr[ddrl])
            if not dr.get('value'):
                dr['value'] = line.product_id.standard_price
            if not dr.get('total_value'):
                dr['total_value'] = tlts
            if not dr.get('total'):
                dr['total'] = tlts * line.product_id.standard_price
        if not self.partner_id.state_id:
            raise UserError("Debe indicar el departamento/estado del tercero.")
        # compositional.information
        if not self.invoice_date and purchase:
            raise UserError("Debe indicar la fecha de la factura")
        elif purchase:
            invoice_date = None
            if not invoice_date:
                # TODO: Usar librarias de fechas , no str
                invoice_date = str(
                    datetime.strptime(str(self.invoice_date or datetime.now())[0:10], '%Y-%m-%d')
                    - timedelta(days=45)
                )[0:10]
            # get max control_date quality_check
            qc_data = self.env['quality.check'].search([
                ('partner_id', '=', self.partner_id.id),
                ('product_id', 'in', [x.product_id.id for x in self.invoice_line_ids]),
            ])
            for qc in qc_data:
                _logger.info(qc)
                # TODO: hallar la diferencia usando fechas
                diff = (datetime.strptime(str(self.invoice_date)[0:10], '%Y-%m-%d')
                        - datetime.strptime(str(qc.control_date)[0:10], '%Y-%m-%d')).days + 1
                if qc.point_id.title not in ci.keys():
                    ci[qc.point_id.title] = {'product_id': line.product_id.id,
                                             'point_id': qc.point_id,
                                             'quality_id': qc,
                                             'title': qc.point_id.title,
                                             'qna1': 0, 'qna2': 0,
                                             'qna3': 0, 'avg': 0}
                if diff > 0 and diff <= 15:
                    ci[qc.point_id.title]['qna3'] += float(qc.measure)
                elif diff > 15 and diff <= 30:
                    ci[qc.point_id.title]['qna2'] += float(qc.measure)
                elif diff > 30 and diff <= 45:
                    ci[qc.point_id.title]['qna1'] += float(qc.measure)
                ci[qc.point_id.title]['avg'] = (ci[qc.point_id.title]['qna1']
                                                + ci[qc.point_id.title]['qna2']
                                                + ci[qc.point_id.title]['qna3']) / 3

            self.cq_id = None
            self.mim_id = None
            self.dr_id = None
            self.ci_id = None
            self.mim_id = [(0, 0, mim)]
            self.dr_id = [(0, 0, dr)]
            self.ci_id = [(0, 0, ci[x]) for x in ci]
            # create default concepts quality
            cq = self.env['concepts.quality'].search([])
            self.cq_id = [(6, 0, [x.id for x in cq])]
            # calculate amount quality
            self.amount_quality = 0
            for quality in self.cq_id:
                self.amount_quality += quality.amount
            self.calculate()
