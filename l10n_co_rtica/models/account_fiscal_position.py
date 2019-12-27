# -*- coding: utf-8 -*-

from odoo import models, api


class AccountFiscalPositionCIIU(models.Model):
    _inherit = 'account.fiscal.position'

    @api.model  # noqa
    def map_tax(self, taxes, product=None, partner=None, type=None):
        result = self.env['account.tax']
        if partner:
            ciiu = product and product.categ_id.ciiu_id or self.env.user.company_id.partner_id.commercial_partner_id.ciiu_id
            if type == 'in_invoice':
                ciiu = partner.commercial_partner_id.ciiu_id

            if ciiu and partner.commercial_partner_id.retention_apply != 'na':
                move_id = self.env.context.get('move_id')
                if move_id:
                    # services
                    city = move_id.partner_shipping_id.city_id
                    condition = move_id.partner_shipping_id.city_id == city
                    if type == 'out_invoice' and ciiu.industry_id.type == 'mrp':
                        city = move_id.journal_id.city_mrp_id
                        condition = move_id.partner_id.city_id == city
                    elif ciiu.industry_id.type != 'srv':
                        city = move_id.journal_id.city_id
                        condition = move_id.partner_id.city_id == city
                    new_tax = self.env['account.tax']
                    generic_tax = ciiu.industry_id.default_tax_id
                    lines = ciiu.line_ids + ciiu.industry_id.line_ids
                    for line in lines:
                        if line.city_id == city and (
                                (type == 'in_invoice' and line.tax_id.type_tax_use == 'purchase')
                                or ((type == 'out_invoice' and line.tax_id.type_tax_use == 'sale'))):
                            if condition:
                                new_tax += line.tax_id
                    if new_tax:
                        taxes |= new_tax
                    elif generic_tax and partner.commercial_partner_id.retention_apply == 'fa':
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
