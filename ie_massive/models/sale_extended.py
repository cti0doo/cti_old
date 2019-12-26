from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, values):
        if values.get('partner_id') and not values.get('fiscal_position_id'):
            partner_id = self.env['res.partner'].browse(values.get('partner_id', False))
            values['fiscal_position_id'] = partner_id.property_account_position_id.id
        return super(SaleOrder, self).create(values)


# class SaleOrderLineExtended(models.Model):
#     _inherit = 'sale.order.line'
#     
#     @api.onchange('product_id')
#     def product_id_change(self):
#         if not self.product_id:
#             return {'domain': {'product_uom': []}}
#
#         vals = {}
#         domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
#         if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
#             vals['product_uom'] = self.product_id.uom_id
#             vals['product_uom_qty'] = 1.0
#
#         product = self.product_id.with_context(
#             lang=self.order_id.partner_id.lang,
#             partner=self.order_id.partner_id.id,
#             quantity=vals.get('product_uom_qty') or self.product_uom_qty,
#             date=self.order_id.date_order,
#             pricelist=self.order_id.pricelist_id.id,
#             uom=self.product_uom.id
#         )
#
#         result = {'domain': domain}
#
#         title = False
#         message = False
#         warning = {}
#         if product.sale_line_warn != 'no-message':
#             title = _("Warning for %s") % product.name
#             message = product.sale_line_warn_msg
#             warning['title'] = title
#             warning['message'] = message
#             result = {'warning': warning}
#             if product.sale_line_warn == 'block':
#                 self.product_id = False
#                 return result
#
#         name = product.name_get()[0][1]
#         if product.description_sale:
#             name += '\n' + product.description_sale
#         vals['name'] = name
#
#         self._compute_tax_id()
#
#         if self.order_id.pricelist_id and self.order_id.partner_id:
#             vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(
#                 self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
#
#         price, rule_id = self.order_id.pricelist_id.get_product_price_rule(
#             self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id)
#         new_list_price, currency_id = self._get_real_price_currency(product, rule_id,
#                                                                     self.product_uom_qty,
#                                                                     self.product_uom,
#                                                                     self.order_id.pricelist_id.id)
#
#         if new_list_price != 0:
#             if self.order_id.pricelist_id.currency_id.id != currency_id.id:
#                 # we need new_list_price in the same currency as price, which is in the SO's pricelist's currency
#                 new_list_price = currency_id.compute(
#                     new_list_price, self.order_id.pricelist_id.currency_id.id)
#             discount = (new_list_price - price) / new_list_price * 100
#             if discount > 0:
#                 vals['discount'] = discount
#
#         self.update(vals)
#
#         return result
#
#     @api.model
#     def _prepare_add_missing_fields(self, values):
#         """ Deduce missing required fields from the onchange """
#         res = {}
#         onchange_fields = ['name', 'price_unit', 'product_uom', 'tax_id', 'discount']
#         if values.get('order_id') and values.get('product_id') and any(f not in values for f in onchange_fields):
#             line = self.new(values)
#             line.product_id_change()
#             for field in onchange_fields:
#                 if field not in values:
#                     res[field] = line._fields[field].convert_to_write(line[field], line)
#         return res
