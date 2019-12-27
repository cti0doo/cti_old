from odoo import api, fields, models, _


# class PurchaseOrder(models.Model):
#     _inherit = 'purchase.order'
#
#     @api.model
#     def create(self, values):
#         if values.get('partner_id') and not values.get('fiscal_position_id'):
#             partner_id = self.env['res.partner'].browse(values.get('partner_id', False))
#             values['fiscal_position_id'] = partner_id.property_account_position_id.id
#         # res = super(PurchaseOrder, self).create(values)
#         # res.map_tax()
#         return super(PurchaseOrder, self).create(values)


class PurchaseOrderLineExtended(models.Model):
    _inherit = 'purchase.order.line'

    @api.model
    def create(self, values):
        if values.get('product_id'):
            product_id = self.env['product.product'].browse(values.get('product_id', False))
            data = {'product_uom': 'uom_po_id',
                    'price_unit': 'standard_price',
                    'name': 'display_name',
                    'taxes_id': 'supplier_taxes_id'}
            taxes = []
            for key in data:
                if not values.get(key):
                    if key in ('product_uom'):
                        values[key] = product_id[data.get(key)].id
                    elif key in ('taxes_id'):
                        values['taxes_id'] = [(6, 0, product_id[data.get(key)].ids)]
                    else:
                        values[key] = product_id[data.get(key)]
        res = super(PurchaseOrderLineExtended, self).create(values)
        # res.write({'fiscal_position_id': res.partner_id.property_account_position_id.id})
        res.order_id.onchange_partner_id()
        res._compute_tax_id()
        return res


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def create(self, values):
        if values.get('partner_id') and not values.get('fiscal_position_id'):
            partner_id = self.env['res.partner'].browse(values.get('partner_id', False))
            values['fiscal_position_id'] = partner_id.property_account_position_id.id
        # res = super(PurchaseOrder, self).create(values)
        # res.map_tax()
        return super(PurchaseOrder, self).create(values)
