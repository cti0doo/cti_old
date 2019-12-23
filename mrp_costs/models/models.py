# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MrpProduction(models.Model):
    _inherit = 'mrp.production'


    original_product_price = fields.Float()

    real_cost = fields.Float(compute='_compute_real_cost')
    real_cost_cal = fields.Boolean(default=False)

    @api.depends('state')
    def _compute_real_cost(self):
        if not self.real_cost_cal:
            if self.state == "done":
                self.real_cost = 666.666
                self.real_cost_cal = True
            else:
                self.real_cost = 0.0


    @api.model
    def create(self, values):
        if not values.get('name', False) or values['name'] == _('New'):
            picking_type_id = values.get('picking_type_id') or self._get_default_picking_type()
            picking_type_id = self.env['stock.picking.type'].browse(picking_type_id)
            if picking_type_id:
                values['name'] = picking_type_id.sequence_id.next_by_id()
            else:
                values['name'] = self.env['ir.sequence'].next_by_code('mrp.production') or _('New')
        prod_cost = values.get('product_id')
        prod_cost = self.env['product.product'].browse(prod_cost)
        values['original_product_price'] = prod_cost.standard_price
        if not values.get('procurement_group_id'):
            values['procurement_group_id'] = self.env["procurement.group"].create({'name': values['name']}).id
        return super(MrpProduction, self).create(values)


