# -*- coding: utf-8 -*-

import base64
import logging
import pandas as pd
import re
from datetime import datetime
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ResBankExtended(models.Model):
    """Bank model extension."""

    _inherit = 'res.bank'

    header_ids = fields.One2many('res.bank.conf', 'bank_h_id', string='Header Configuration', index=True)
    conf_ids = fields.One2many('res.bank.conf', 'bank_id', string='Configuration', index=True)
    statement_ids = fields.One2many('res.bank.statement.conf.lines', 'bank_id', string='Extract statement')
    valid_line = fields.Char(string='Valid line?')
    separator_columns = fields.Char(string='Separator columns')
    footer_ids = fields.One2many('res.bank.conf', 'bank_f_id', string='Footer Configuration', index=True)

class ResPartnerBankExtended(models.Model):
    """Partner Bank model extension."""

    _inherit = 'res.partner.bank'

    type = fields.Selection(
        [('S', 'Saving'), ('D', 'Current'), ('C', 'Accountant')],
        string='Type Extended'
    )

    _sql_constraints = [
        ('acc_number_uniq', 'unique (acc_number)',
         "The account number must be unique, this one is already assigned to another partner.")
    ]


class ResBankConfLines(models.Model):
    """Bank Configuration Lines model extension."""

    _name = 'res.bank.conf'
    _description = 'Bank Configuration Lines'
    bank_id = fields.Many2one('res.bank', string='Bank', required=False)
    bank_h_id = fields.Many2one('res.bank', string='Bank Header', required=False)
    bank_f_id = fields.Many2one('res.bank', string='Bank Footer', required=False)
    sequence = fields.Integer('Sequence', required=True, index=True,
                              help='Use to arrange calculation sequence',
                              default=5)
    name = fields.Char(string='Name', size=256, required=True, index=True)
    type = fields.Selection([('p', 'Python'), ('t', 'Text')],
                            string='Type', required=True, default='p')
    size = fields.Integer(string='Size', required=True, index=True)
    adjust = fields.Selection([('l', 'Left'), ('r', 'Right')],
                              string='Adjust', required=True, default='r')
    character = fields.Char(string='Character fill', index=True)
    function = fields.Char(string='Function', required=False, index=True)
    format = fields.Char(string='Format')
    type_format = fields.Selection([('date', 'Date'), ('money', 'Money')], string='Type format')


class ResBankConfExtractLines(models.Model):
    _name = 'res.bank.statement.conf.lines'
    _description = 'Banks Statements Configuration'

    bank_id = fields.Many2one('res.bank', string='Bank', required=False)
    bank_h_id = fields.Many2one('res.bank', string='Bank', required=False)
    sequence = fields.Integer('Sequence', required=True)
    name = fields.Char(string='Name', required=True, index=True)
    field = fields.Char(string='Field', required=False, index=True)
    position = fields.Char(string='Position', required=True)
    parse = fields.Text(string='Parse')


class AccountBankStatementImport(models.TransientModel):
    _inherit = "account.bank.statement.import"

    
    def import_file(self):
        data = base64.decodestring(self.data_file).decode('latin-1').split('\r\n')
        if len(data) == 1:
            data = data[0].split('\n')
        journal_id = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_id'))
        datas = []
        lines = []
        for x in data:
            if len(x) > 0:
                datas.append(x)
        for line in datas:
            line = line.strip()
            record = {}
            if eval(journal_id.bank_id.valid_line):
                if journal_id.bank_id.separator_columns:
                    columns = re.split(eval(journal_id.bank_id.separator_columns), line)
                    for conf in journal_id.bank_id.statement_ids:
                        result = columns[int(conf.position)].strip()
                        if result:
                            if conf.parse:
                                res = eval(conf.parse)
                            else:
                                res = result
                            record[conf.field] = res
                lines.append((0, 0, record))
        abs_id = self.env['account.bank.statement'].create(
            {'journal_id': journal_id.id, 'date': fields.Date.today(), 'line_ids': lines})
        return abs_id.get_formview_action()
