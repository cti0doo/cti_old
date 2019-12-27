# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from odoo.exceptions import UserError
import pandas as pd

from odoo import models, fields

_logger = logging.getLogger(__name__)


class MagneticMediaWizard(models.TransientModel):
    _name = 'magnetic.media.wizard'
    _description = 'Magnetic Media Wizard'

    date_from = fields.Date(string='Date from', required=True)
    date_to = fields.Date(string='Date to', required=True)

    def export(self):
        id = self.env.context.get('active_id')
        report = self.env['magnetic.media'].browse(id)
        sql = str(report.query).format(id=id, date_from=self.date_from,
                                       date_to=self.date_to)
        _logger.info(report.query)
        self.env.cr.execute(sql)
        datas = self.env.cr.dictfetchall()
        if not datas:
            raise UserError('''There is no information to display. Check the parameters.''')

        actual = str(datetime.now()).replace('-', '').replace(':', '').replace('.', '').replace(' ', '')
        data_attach = {
            'name': report.name + '_' + self.env.user.company_id.name + self.env.user.name + '_' + actual + '.xlsx',
            'datas': '.',
            'datas_fname': report.name + '_' + self.env.user.company_id.name + self.env.user.name + '_' + actual + '.xlsx',
            'res_model': 'magnetic.media', 'res_id': id}

        # elimina adjuntos del usuario
        self.env['ir.attachment'].search(
            [('res_model', '=', self.env.context.get('model')), ('company_id', '=', self.env.user.company_id.id),
             ('name', 'like', '%' + report.name + '%' + self.env.user.name + '%')]).unlink()

        # crea adjunto en blanco
        attachments = self.env['ir.attachment'].create(data_attach)
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') + '/web/content/%s?download=true' % str(
            attachments.id)

        # Create a Pandas dataframe from the data.
        df = pd.DataFrame(data=datas, columns=datas[0].keys())
        # Create a Pandas Excel writer using XlsxWriter as the engine.
        writer = pd.ExcelWriter(attachments._full_path(attachments.store_fname), engine='xlsxwriter')

        # Convert the dataframe to an XlsxWriter Excel object.
        df.to_excel(writer, sheet_name=report.name)
        writer.save()
        return {'type': 'ir.actions.act_url', 'url': str(url), 'target': 'self'}


class MagneticMedia(models.Model):
    _name = 'magnetic.media'
    _description = 'Magnetic Media'

    code = fields.Char('Code', required=True, help='Code for magnetic media format')
    name = fields.Char('Name', required=True, help='Name for magnetic media format')
    smaller_amount = fields.Char('Minor amounts', default=0.0, help='The value must be indicated for minor amounts')
    line_ids = fields.One2many('magnetic.media.lines', 'magnetic_id', string='Lines')
    query = fields.Text(string='Query')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('cancel', 'Cancel')], name='State',
                             default='draft')

    def confirm(self):
        self.state = 'confirm'

    def cancel(self):
        self.state = 'cancel'

    def to_draft(self):
        self.state = 'draft'

    def export(self):
        return {'type': 'ir.actions.act_window',
                'res_model': 'magnetic.media.wizard',
                'res_id': '',  # int(params.get('activeId')),
                'views': [[False, 'form']],
                'target': 'new',
                }


class MagneticMediaLines(models.Model):
    _name = 'magnetic.media.lines'
    _description = 'Magnetic Media Lines'

    code = fields.Char('Code', required=True, help='Code for magnetic media format')
    name = fields.Char(string='Line name', required=True,
                       help='The name of the line must be indicated for each concept of magnetic media')
    magnetic_id = fields.Many2one('magnetic.media', string='Magnetic media')
    concept_ids = fields.One2many('magnetic.media.lines.concepts', 'line_id', string='Concepts')


class MagneticMediaLinesConcepts(models.Model):
    _name = 'magnetic.media.lines.concepts'
    _description = 'Magnetic Media Lines Concepts'

    sequence = fields.Char(string='Sequence',
                           help='You must indicate the sequence as it will be shown in the media format')
    name = fields.Char(string='Concept name', required=True,
                       help='The name of the concepts of magnetic media')
    type = fields.Selection([('d', 'Debit'), ('c', 'Credit'), ('sf', 'Saldo final')], string='Type', required=True)
    account_ids = fields.Many2many('account.account', string='Accounts',
                                   help='You must select the accounts that apply to this concept')
    tag_ids = fields.Many2many('account.account.tag', 'magnetic_media_lines_concepts_account_account_tag',
                               'concept_ids',
                               'tag_ids', string='Account Tags',
                               help='You must select the account tags that apply to this concept')
    line_id = fields.Many2one('magnetic.media.lines', string='Magnetic media')
