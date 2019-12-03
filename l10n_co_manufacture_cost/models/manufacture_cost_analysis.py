# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# from odoo import api, fields, models, tools
# from odoo.fields import Datetime as fieldsDatetime
from odoo import models, fields, api
from odoo import tools


class CostManufacture(models.Model):
    _name = 'manufacture.cost.analysis'
    _description = 'Manufacture Cost Analysis'
    _auto = False

    mrp_id = fields.Many2one('mrp.production', string='Production')
    state = fields.Selection([('confirmed', 'Confirmed'),
                              ('planned', 'Planned'),
                              ('progress', 'Progress'),
                              ('cancel', 'Cancel'),
                              ('done', 'Done')
                              ])
    product = fields.Many2one('product.product', string='Product')
    # planned_uom = fields.Many2one('product.uom', string='Planned Uom')
    planned_qty = fields.Float(string='Planned qty', default=0)
    unit_cost = fields.Float(string='Unit cost', default=0)
    planned_cost_total = fields.Float(string='Planned cost total', default=0)

    cons_qty = fields.Float(string='Consumed qty', default=0.0)
    cons_cost_total = fields.Float(string='Consumed cost total', default=0.0)
    cost_wc = fields.Float(string='Cost workcenter', default=0.0)

    prod_qty = fields.Float(string='Produced qty', default=0.0)
    prod_cost = fields.Float(string='Product cost', default=0)
    prod_uom = fields.Many2one('uom.uom', string='UOM')
    prod_cost_total = fields.Float(string='Produced cost total', default=0.0)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        # groupby_fields = set([groupby] if isinstance(groupby, basestring) else groupby)
        # if groupby_fields.intersection(USER_PRIVATE_FIELDS):
        #    raise AccessError(_("Invalid 'group by' parameter"))
        return super(CostManufacture, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                       orderby=orderby, lazy=lazy)

    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'manufacture_cost_analysis')
        self.env.cr.execute("""CREATE OR REPLACE VIEW manufacture_cost_analysis AS (SELECT row_number() OVER () AS id,
    mp.id AS mrp_id,
    mp.state,
    rml.product_id AS product,
    rm.product_uom_qty AS planned_qty,
    abs(rm.price_unit) AS unit_cost,
    abs(rm.product_uom_qty::double precision * rm.price_unit) AS planned_cost_total,
    rml.qty_done AS cons_qty,
    abs(rm.price_unit) AS cons_cost_total,
    0 AS prod_qty,
    0 AS prod_cost,
    0 AS prod_cost_total,
    0 AS cost_wc,
    rml.product_uom_id AS prod_uom
   FROM mrp_production mp
     JOIN stock_move rm ON rm.raw_material_production_id = mp.id
     JOIN stock_move_line rml ON rml.move_id = rm.id
UNION
 SELECT row_number() OVER () AS id,
    mp.id AS mrp_id,
    mp.state,
    ptl.product_id AS product,
    pt.product_uom_qty AS planned_qty,
    abs(pt.price_unit) AS unit_cost,
    abs(pt.product_uom_qty::double precision * pt.price_unit) AS planned_cost_total,
    0 AS cons_qty,
    0 AS cons_cost_total,
    ptl.qty_done AS prod_qty,
    abs(pt.price_unit) AS prod_cost,
    abs(pt.price_unit) AS prod_cost_total,
    ( SELECT sum(costs_hour) AS sum
           FROM mrp_workcenter mw
          WHERE (mw.id IN ( SELECT mrp_routing_workcenter.workcenter_id
                   FROM mrp_routing_workcenter
                  WHERE mrp_routing_workcenter.routing_id = mr.id))) AS cost_wc,
    ptl.product_uom_id AS prod_uom
   FROM mrp_production mp
     JOIN stock_move pt ON pt.production_id = mp.id
     JOIN stock_move_line ptl ON ptl.move_id = pt.id
     LEFT JOIN mrp_routing mr ON mr.id = mp.routing_id)""")
