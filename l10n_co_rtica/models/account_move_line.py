# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.tools.float_utils import float_compare


class AccountMoveLines(models.Model):
    _inherit = "account.move.line"

    @api.onchange('account_id')
    def _onchange_account_id(self):
        if not self.account_id:
            return
        if not self.product_id:
            fpos = self.move_id.fiscal_position_id
            self.tax_ids = fpos.with_context(move_id=self.move_id).map_tax(self.account_id.tax_ids,
                                                                                              None, self.partner_id,
                                                                                              self.move_id.type).ids
        elif not self.price_unit:
            self._set_taxes()

    def _set_taxes(self):
        """ Used in on_change to set taxes and price."""
        if self.move_id.type in ('out_invoice', 'out_refund'):
            taxes = self.product_id.taxes_id or self.account_id.tax_ids
        else:
            taxes = self.product_id.supplier_taxes_id or self.account_id.tax_ids

        # Keep only taxes of the company
        company_id = self.company_id or self.env.user.company_id
        taxes = taxes.filtered(lambda r: r.company_id == company_id)
        self.tax_ids = fp_taxes = self.move_id.fiscal_position_id.with_context(
            move_id=self.move_id).map_tax(taxes, self.product_id,
                                                self.move_id.partner_id,
                                                self.move_id.type)
        fix_price = self.env['account.tax']._fix_tax_included_price
        if self.move_id.type in ('in_invoice', 'in_refund'):
            prec = self.env['decimal.precision'].precision_get('Product Price')
            if not self.price_unit or float_compare(self.price_unit, self.product_id.standard_price,
                                                    precision_digits=prec) == 0:
                self.price_unit = fix_price(self.product_id.standard_price, taxes, fp_taxes)
        else:
            self.price_unit = fix_price(self.product_id.lst_price, taxes, fp_taxes)
