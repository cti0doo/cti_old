# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ChartAccountTaxTemplate(models.Model):
    _inherit = 'account.fiscal.position.tax.template'

    company_fiscal_position_id = fields.Many2one('account.fiscal.position.template', string='Fiscal position')

class ChartAccountTax(models.Model):
    _inherit = 'account.fiscal.position.tax'

    company_fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal position')


class ChartAccountAccountTemplate(models.Model):
    _inherit = 'account.fiscal.position.account.template'

    company_fiscal_position_id = fields.Many2one('account.fiscal.position.template', string='Fiscal position')

class ChartAccountAccount(models.Model):
    _inherit = 'account.fiscal.position.account'

    company_fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal position')


class ChartAccountApply(models.Model):
    _inherit = 'account.chart.template'

    
    def generate_fiscal_position(self, tax_template_ref, acc_template_ref, company):
        """ This method generate Fiscal Position, Fiscal Position Accounts and Fiscal Position Taxes from templates.

            :param chart_temp_id: Chart Template Id.
            :param taxes_ids: Taxes templates reference for generating account.fiscal.position.tax.
            :param acc_template_ref: Account templates reference for generating account.fiscal.position.account.
            :param company_id: company_id selected from wizard.multi.charts.accounts.
            :returns: True
        """
        self.ensure_one()
        res_conf = self.env['res.config.settings'].search([('company_id', 'in', [self.env.user.company_id.id])],
                                                          limit=1, order='create_date DESC')
        #if not res_conf.company_fiscal_position_id:
        #    raise UserError("You must define the fiscal position of the company")
        positions = self.env['account.fiscal.position.template'].search([('chart_template_id', '=', self.id)])
        for position in positions:
            new_fp = self.create_record_with_xmlid(self.env.user.company_id, position, 'account.fiscal.position',
                                                   {'company_id': self.env.user.company_id.id, 'name': position.name,
                                                    'note': position.note})
            for tax in position.tax_ids:
                if tax.company_fiscal_position_id.id == res_conf.company_fiscal_position_id.id:
                    self.create_record_with_xmlid(self.env.user.company_id, tax, 'account.fiscal.position.tax', {
                        'tax_src_id': tax_template_ref[tax.tax_src_id.id],
                        'tax_dest_id': tax.tax_dest_id and tax_template_ref[tax.tax_dest_id.id] or False,
                        'position_id': new_fp
                    })
            for acc in position.account_ids:
                if acc.company_fiscal_position_id.id == res_conf.company_fiscal_position_id.id:
                    self.create_record_with_xmlid(self.env.user.company_id, acc, 'account.fiscal.position.account', {
                        'account_src_id': acc_template_ref[acc.account_src_id.id],
                        'account_dest_id': acc_template_ref[acc.account_dest_id.id],
                        'position_id': new_fp
                    })
        return True


class AccountConfigSettingsExtended(models.TransientModel):
    _inherit = 'res.config.settings'

    company_fiscal_position_id = fields.Many2one('account.fiscal.position.template', string='Fiscal position',
                                                 config_parameter='company_fiscal_position_id')

    
    def generate_fiscal_position(self):
        return self.env.user.company_id.chart_template_id.generate_fiscal_position({}, {})

class AccountTax(models.Model):
    _inherit = 'account.tax'

    account_id = fields.Many2one('account.account', domain=[('deprecated', '=', False)], string='Tax Account', ondelete='restrict',
        help="Account that will be set on invoice tax lines for invoices. Leave empty to use the expense account.")
    refund_account_id = fields.Many2one('account.account', domain=[('deprecated', '=', False)], string='Tax Account on Credit Notes', ondelete='restrict',
        help="Account that will be set on invoice tax lines for credit notes. Leave empty to use the expense account.")

class AccountTaxTemplate(models.Model):
    _inherit = 'account.tax.template'

    account_id = fields.Many2one('account.account.template', string='Tax Account', ondelete='restrict',
        help="Account that will be set on invoice tax lines for invoices. Leave empty to use the expense account.")
    refund_account_id = fields.Many2one('account.account.template', string='Tax Account on Refunds', ondelete='restrict',
        help="Account that will be set on invoice tax lines for refunds. Leave empty to use the expense account.")


