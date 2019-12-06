# -*- coding: utf-8 -*-

import logging
import math
from collections import defaultdict

from odoo.exceptions import UserError

from odoo import models, fields, api

_logger = logging.getLogger('COSTMANUFACTURE')


class QualityChecksExtended(models.Model):
    _inherit = 'quality.check'

    title = fields.Char(related='point_id.title', readonly=True)


class ProductProductExtended(models.Model):
    _inherit = 'product.product'

    cost_special = fields.Boolean(string='Cost Special', default=False)


class ProductAttributeExtended(models.Model):
    _inherit = 'product.attribute'

    fat = fields.Boolean(string='Fat', default=False)


# class MRPRoutingWorkCenterCostExpected(models.Model):
#     _inherit = 'mrp.routing.workcenter'
#
#     @api.depends('default_cost', 'default_cost_per_labor')
#     def _get_total(self):
#         self.total_cost = self.default_cost + self.default_cost_per_labor
#
#     default_cost = fields.Float(string='Estimated cost')
#     default_cost_per_labor = fields.Float(string='Estimated cost per labor')
#     total_cost = fields.Float(compute='_get_total', string='Total cost', store=False)


# class MRPWorkCenter(models.Model):
#     _inherit = 'mrp.workcenter'
#
#     cost_start = fields.Float(string='Cost start (minutes)')
#     cost_stop = fields.Float(string='Cost stop (minutes)')


# class MRPWorkorderCost(models.Model):
#     _inherit = 'mrp.workorder'
#
#     
#     def button_finish(self):
#         self.ensure_one()
#         self.end_all()
#         self.real_cost = self.default_cost * self.duration
#         self.real_cost_per_labor = self.default_cost_per_labor * self.duration
#         self.total_cost = (self.default_cost * self.duration) + (self.default_cost_per_labor * self.duration)
#         self.write({'state': 'done', 'date_finished': fields.Datetime.now()})
#
#     default_cost = fields.Float(string='Estimated cost')
#     default_cost_per_labor = fields.Float(string='Estimated cost per labor')
#     real_cost = fields.Float(string='Real cost', required=True, default=0)
#     real_cost_per_labor = fields.Float(string='Real cost per labor', required=True, default=0)
#     total_cost = fields.Float(string='Total cost')


class CostManufacture(models.Model):
    _inherit = 'mrp.production'

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.product_uom_id = self.product_id.uom_po_id

    sng = fields.Float(string='SNG', default=0.0)
    st = fields.Float(string='ST', default=0.0)
    density = fields.Float(string='Density', default=0.0)
    ov = fields.Float(string='OV', default=1000)
    price_base = fields.Float(string='Price base', default=0.0)
    ov1 = fields.Float(string='OV1', default=0.0)
    sng_percentage = fields.Float(string='SNG (%)', default=0.0)
    st_percentage = fields.Float(string='ST (%)', default=0.0)
    gr_sl = fields.Float(string='GR S-L', default=0.0)
    standard_price = fields.Float(string='Cost', default=0.0)
    quality_ids = fields.One2many('quality.check', 'production_id', string='Quality checks')

    
    def _get_quantity(self, product_id, quantity, factor, sp):
        if self.product_id.cost_special:
            gin, gout, gbpout = 0, 0, 0
            if not self.quality_ids:
                bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', self.product_id.id)], limit=1)
                self.bom_id = bom.id
                query = []
                for condition in ['qp.fat', 'qp.density', 'qp.sng']:
                    query.append(''' SELECT * FROM (select qc.id from quality_check  qc
                                                            inner join quality_point qp on qp.id = qc.point_id
                                                            where {condition} is true 
                                                            and qc.product_id in ({product_id})
                                                            and qc.quality_state = 'pass'
                                                            order by qc.write_date desc limit 1) as a'''.format(condition=condition,product_id=','.join(str(x.product_id.id) for x in self.bom_id.bom_line_ids)))
                self.env.cr.execute(' union '.join([x for x in query]))
                data = self.env.cr.dictfetchall()
                self.quality_ids = [(3, x.get('id')) for x in data]
                self.quality_ids = [(4, x.get('id')) for x in data]
                if not self.quality_ids:
                    raise UserError('Must be indicate quality check for {product}'.format(product=self.product_id.name))
            for prod in self:
                # fat in
                for il in prod.quality_ids:
                    if il.point_id.fat:
                        gin = il.measure / 100

                for att in self.product_id.attribute_value_ids:
                    if att.attribute_id.fat:
                        # fat out
                        gout = float(att.name.replace(',', '.')) / 100

                for bom in self.bom_id:
                    for bl in bom.sub_products:
                        for att in bl.product_id.attribute_value_ids:
                            if att.attribute_id.fat:
                                gbpout = float(att.name.replace(',', '.')) / 100

            quantity = -1 * (self.product_qty * (gout - gin)) / ((gbpout - gin) or 1)
            if not sp:
                quantity += self.product_qty
        return quantity / factor

    def _generate_raw_move(self, bom_line, line_data):
        quantity = self._get_quantity(bom_line.product_id, line_data['qty'], 1, False)
        # alt_op needed for the case when you explode phantom bom and all the lines will be consumed in the operation given by the parent bom line
        alt_op = line_data['parent_line'] and line_data['parent_line'].operation_id.id or False
        if bom_line.child_bom_id and bom_line.child_bom_id.type == 'phantom':
            return self.env['stock.move']
        if bom_line.product_id.type not in ['product', 'consu']:
            return self.env['stock.move']
        if self.bom_id.routing_id and self.bom_id.routing_id.location_id:
            source_location = self.bom_id.routing_id.location_id
        else:
            source_location = self.location_src_id
        original_quantity = self.product_qty - self.qty_produced
        data = {
            'name': self.name,
            'date': self.date_planned_start,
            'date_expected': self.date_planned_start,
            'bom_line_id': bom_line.id,
            'product_id': bom_line.product_id.id,
            'product_uom_qty': quantity,
            'product_uom': bom_line.product_uom_id.id,
            'location_id': source_location.id,
            'location_dest_id': self.product_id.property_stock_production.id,
            'raw_material_production_id': self.id,
            'company_id': self.company_id.id,
            'operation_id': bom_line.operation_id.id or alt_op,
            'price_unit': bom_line.product_id.standard_price,
            'procure_method': 'make_to_stock',
            'origin': self.name,
            'warehouse_id': source_location.get_warehouse().id,
            'group_id': self.procurement_group_id.id,
            'propagate': self.propagate,
            'unit_factor': quantity / original_quantity,
        }
        return self.env['stock.move'].create(data)

    def _create_byproduct_move(self, sub_product):
        Move = self.env['stock.move']
        for production in self:
            source = production.product_id.property_stock_production.id
            product_uom_factor = production.product_uom_id._compute_quantity(
                production.product_qty - production.qty_produced, production.bom_id.product_uom_id)
            qty1 = self._get_quantity(sub_product.product_id, sub_product.product_qty, product_uom_factor, True)
            qty1 *= product_uom_factor / production.bom_id.product_qty
            data = {
                'name': 'PROD:%s' % production.name,
                'date': production.date_planned_start,
                'product_id': sub_product.product_id.id,
                'product_uom_qty': qty1,
                'product_uom': sub_product.product_uom_id.id,
                'location_id': source,
                'location_dest_id': production.location_dest_id.id,
                'operation_id': sub_product.operation_id.id,
                'production_id': production.id,
                'origin': production.name,
                'unit_factor': qty1 / (production.product_qty - production.qty_produced),
                'subproduct_id': sub_product.id
            }
            move = Move.create(data)
            move._action_confirm()

    
    def post_inventory(self):
        self.CalculateCost()
        result = super(CostManufacture, self).post_inventory()

    
    def button_mark_done(self):
        # self.CalculateCost()
        self.ensure_one()
        for wo in self.workorder_ids:
            if wo.time_ids.filtered(lambda x: (not x.date_end) and (x.loss_type in ('productive', 'performance'))):
                raise UserError(_('Work order %s is still running') % wo.name)
        self.post_inventory()

        moves_to_cancel = (self.move_raw_ids | self.move_finished_ids).filtered(
            lambda x: x.state not in ('done', 'cancel'))
        moves_to_cancel._action_cancel()
        self.write({'state': 'done', 'date_finished': fields.Datetime.now()})
        # self.env["procurement.order"].search([('production_id', 'in', self.ids)]).check()
        self.write({'state': 'done'})

    def _workorders_create(self, bom, bom_data):
        """
        :param bom: in case of recursive boms: we could create work orders for child
                    BoMs
        """
        workorders = self.env['mrp.workorder']
        bom_qty = bom_data['qty']

        # Initial qty producing
        if self.product_id.tracking == 'serial':
            quantity = 1.0
        else:
            quantity = self.product_qty - sum(self.move_finished_ids.mapped('quantity_done'))
            quantity = quantity if (quantity > 0) else 0

        for operation in bom.routing_id.operation_ids:
            # create workorder
            cycle_number = math.ceil(bom_qty / operation.workcenter_id.capacity)  # TODO: float_round UP
            duration_expected = (operation.workcenter_id.time_start +
                                 operation.workcenter_id.time_stop +
                                 cycle_number * operation.time_cycle * 100.0 / operation.workcenter_id.time_efficiency)
            workorder = workorders.create({
                'name': operation.name,
                'production_id': self.id,
                'workcenter_id': operation.workcenter_id.id,
                'operation_id': operation.id,
                'duration_expected': duration_expected,
                'state': len(workorders) == 0 and 'ready' or 'pending',
                'qty_producing': quantity,
                # 'default_cost': operation.default_cost,  # / duration_expected,
                # 'default_cost_per_labor': operation.default_cost_per_labor,  # / duration_expected,
                'capacity': operation.workcenter_id.capacity,
            })
            if workorders:
                workorders[-1].next_work_order_id = workorder.id
            workorders += workorder
            # assign moves; last operation receive all unassigned moves (which case ?)
            moves_raw = self.move_raw_ids.filtered(lambda move: move.operation_id == operation)
            if len(workorders) == len(bom.routing_id.operation_ids):
                moves_raw |= self.move_raw_ids.filtered(lambda move: not move.operation_id)
            moves_finished = self.move_finished_ids.filtered(
                lambda move: move.operation_id == operation)  # TODO: code does nothing, unless maybe by_products?
            # moves_raw.mapped('move_lot_ids').write({'workorder_id': workorder.id})
            moves_raw.mapped('move_line_ids').write({'workorder_id': workorder.id})
            (moves_finished + moves_raw).write({'workorder_id': workorder.id})

            workorder._generate_lot_ids()
        return workorders

    def CalculateCost(self):
        if self.product_id.cost_special:
            if not self.quality_ids:
                raise UserError(
                    'The finished product is configured as a special cost, so you must indicate an inspection.')
            fat_general, self.st, self.ov1, self.sng_percentage, self.st_percentage, self.gr_sl = 0, 0, 0, 0, 0, 0
            # Grasa producto terminado
            for att in self.product_id.attribute_value_ids:
                if att.attribute_id.fat:
                    fat_general = float(att.name.replace(',', '.'))
            # Valores materia prima
            sng, fat, fatc, density = 0, 0, 0, 0
            for ins in self.quality_ids:
                if ins.point_id.sng:
                    sng = float(ins.measure)
                if ins.point_id.density:
                    density = float(ins.measure)
                if ins.point_id.fat:
                    fat = float(ins.measure)
                    fatc += fat
            if not fat_general or not sng or not density or not fat:
                raise UserError(
                    'Must verify product attributes and quality control\n fat_general: {fat_general}, sng: {sng}, fat: {fat}'.format(
                        fat_general=fat_general, sng=sng, fat=fat))
            self.st += float(fat + sng)
            _logger.debug("ST: %s" % self.st)
            # ov1
            if self.st > 0:
                for lines in self.move_raw_ids:
                    self.ov1 += lines.product_id.standard_price / ((density * self.st / 100) or 1)
                # sng_percentage
                try:
                    self.sng_percentage += (sng * self.ov / 100) / (self.ov - (fat - fat_general) * self.ov / 100) * 100
                except ZeroDivisionError:
                    self.sng_percentage += 0.0
                # st_percentage
                self.st_percentage += self.sng_percentage + fat_general
                # gr_sl
                self.gr_sl += density * self.st_percentage / 100
                cost = 0
                for bl in self.bom_id.bom_line_ids:
                    if bl.product_id.standard_price:
                        cost += bl.product_id.standard_price
                fats = 0
                for sp in self.bom_id.sub_products:
                    for att in sp.product_id.attribute_value_ids:
                        if att.attribute_id.fat:
                            fat = float(att.name.replace(',', '.')) / 100
                            fats += fat
                qty = abs((self.product_qty * (fat_general - fatc)) / (fats * 100 - fatc))
                for fi in self.move_finished_ids:
                    price = 0
                    if fi.product_id.id == self.product_id.id:  # producto terminado
                        price = self.gr_sl * self.ov1
                    else:  # byproduct
                        price = (cost / (self.st / 100)) * fat
                    fi.price_unit = price
                    fi.product_id.standard_price = price  # fi.write({'price_unit': price})

            else:
                raise UserError('The inspection has not been defined FAT and SNG')
        return True


class StockMoveCostManufacture(models.Model):
    _inherit = 'stock.move'

    
    def product_price_update_before_done(self):
        _logger.info('product_price_update_before_done')
        tmpl_dict = defaultdict(lambda: 0.0)
        # adapt standard price on incomming moves if the product cost_method is 'average'
        for move in self.filtered(lambda move: move.location_id.usage in ['supplier',
                                                                          'production'] and move.product_id.cost_method == 'average'):
            product_tot_qty_available = move.product_id.qty_available + tmpl_dict[move.product_id.id]

            # if the incoming move is for a purchase order with foreign currency, need to call this to get the same value that the quant will use.
            if product_tot_qty_available <= 0:
                new_std_price = move._get_price_unit()
            else:
                # Get the standard price
                amount_unit = move.product_id.standard_price
                new_std_price = ((amount_unit * product_tot_qty_available) + (
                        move._get_price_unit() * move.product_qty)) / (product_tot_qty_available + move.product_qty)

            tmpl_dict[move.product_id.id] += move.product_qty
            # Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
            move.product_id.with_context(force_company=move.company_id.id).write({'standard_price': new_std_price})
