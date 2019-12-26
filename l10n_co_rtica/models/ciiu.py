# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from odoo import models, fields, api
from odoo.tools.float_utils import float_compare
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class ciiu(models.Model):
    _name = 'account.ciiu'
    _description = 'Account CIIU'

    name = fields.Char(string='Code', required=True)
    description = fields.Char(string='Description', required=True)
    line_ids = fields.One2many('account.ciiu.lines', 'ciiu_id', string='lines')

    
    def name_get(self):
        result = []
        for record in self:
            if record.name and record.description:
                result.append((record.id, record.name + ' - ' + record.description))
            if record.name and not record.description:
                result.append((record.id, record.name))
        return result


class ciiuLines(models.Model):
    _name = 'account.ciiu.lines'
    _description = 'Account CIIU Lines'

    tax_id = fields.Many2one('account.tax', string='Tax', required=False)
    city_id = fields.Many2one('res.country.state.city', string='City', required=False)
    ciiu_id = fields.Many2one('account.ciiu', string='CIIU', required=True)


class resPartnerCIIU(models.Model):
    _inherit = 'res.partner'

    ciiu_id = fields.Many2one('account.ciiu', string='CIIU')


class AccountFiscalPositionCIIU(models.Model):
    _inherit = 'account.fiscal.position'

    @api.model  # noqa
    def map_tax(self, taxes, product=None, partner=None, type=None):
        result = self.env['account.tax']
        if not partner:
            partner = self.env['res.partner'].browse(self.env.context.get('partner_id'))
        if partner:
            ciiu = partner.ciiu_id or partner.parent_id.ciiu_id
            if ciiu:
                new_tax = False
                generic_tax = False
                for lines in ciiu.line_ids:
                    _logger.info('=======')
                    _logger.info(lines.tax_id.type_tax_use)
                    _logger.info(partner.name)
                    if not lines.city_id:
                        generic_tax = lines.tax_id
                    if lines.city_id == partner.city_id and (
                            (type == 'in_invoice' and lines.tax_id.type_tax_use == 'purchase') or (
                            (type == 'out_invoice' and lines.tax_id.type_tax_use == 'sale'))):
                        new_tax = lines.tax_id
                if new_tax:
                    taxes |= new_tax
                    # _logger.info(lines.tax_id.type_tax_use)
                elif generic_tax:
                    taxes |= generic_tax

            for tax in taxes:
                tax_count = 0
                for t in partner.property_account_position_id.tax_ids:
                    if t.tax_src_id == tax:
                        tax_count += 1
                        if t.tax_dest_id:
                            result |= t.tax_dest_id
                if not tax_count:
                    result |= tax
        else:
            result = super(AccountFiscalPositionCIIU, self).map_tax(taxes, product=product, partner=partner)
        return result
