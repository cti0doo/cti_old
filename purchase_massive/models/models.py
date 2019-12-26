# -*- coding: utf-8 -*-

import logging

from odoo.exceptions import UserError

from odoo import models, fields, api, SUPERUSER_ID, _

# Get the logger
_logger = logging.getLogger(__name__)


class MassivePurchase(models.Model):
    _name = 'massive.purchase'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Massive purchase"
    _order = 'name asc'

    def _get_date(self):
        return fields.Datetime.now()

    name = fields.Char(string='Number', default='New', readonly=True, copy=False)
    picking_type_id = fields.Many2one('stock.picking.type', string='Picking type',
                                      index=True)
    product_id = fields.Many2one('product.product', string='Product',
                                 domain="[('purchase_ok','=',True)]",
                                 required=True, index=True)
    purchase_id = fields.Many2one('purchase.order', string='Transport order',
                                  index=True, copy=False,
                                  readonly=True)
    line_ids = fields.One2many('massive.purchase.lines', 'massive_purchase_id',
                               string="Lines", copy=True)
    date = fields.Datetime(string='Date', readonly=False, required=True,
                           copy=False, default=_get_date)
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirm'), ('closed', 'Closed'),
         ('cancel', 'Cancel')], default='draft', string='State'
    )
    transport_id = fields.Many2one('res.partner', string='Transport', index=True, required=True)
    product_transport_id = fields.Many2one('product.product', string='Product transport',
                                           domain="[('landed_cost_ok','=',True)]", index=True,
                                           required=True)
    fare = fields.Float(string='Fare', required=True, default=0)
    description = fields.Text(string='Description')
    average = fields.Float(compute='_get_average', string='Average', store=True)
    price_total = fields.Float(compute='_get_average', string='Price total', store=True)
    quantity = fields.Float(compute='_get_average', string='Quantity', store=True)

    @api.onchange('product_transport_id')
    def onchange_product_transport_id(self):
        self.fare = self.product_transport_id.standard_price

    
    @api.depends('line_ids')
    def _get_average(self):
        quantity = 0
        total = 0
        for x in self.line_ids:
            quantity += x.quantity
            total += x.price_total
        self.average = total / (quantity or 1)
        self.quantity = quantity
        self.price_total = total

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') != 'New':
            vals['name'] = 'New'
        vals['name'] = self.env['ir.sequence'].next_by_code('massive.purchase') or '/'
        return super(MassivePurchase, self).create(vals)

    def create_po(self, product, lines, order_id, transport):
        po = self.env['purchase.order']
        purchase_order = True
        if not product.landed_cost_ok:
            picking_batch = self.env['stock.picking.batch'].create({'name': self.name})
        for line in lines:
            if not transport:
                partner = line.partner_id
                quantity = line.quantity
            else:
                partner = line
                quantity = 1
            if quantity >= 1:
                product_lang = product.with_context({
                    'lang': partner.lang,
                    'partner_id': partner.id,
                })
                product_name = product_lang.display_name
                if product_lang.description_purchase:
                    product_name += '\n' + product_lang.description_purchase
                fpos = partner.property_account_position_id
                taxes = None
                if self.env.uid == SUPERUSER_ID:
                    company_id = self.env.user.company_id.id
                    taxes = fpos.map_tax(
                        product.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id))
                else:
                    taxes = fpos.map_tax(product.supplier_taxes_id)

                products = product.seller_ids.filtered(
                    lambda r: r.name.id == partner.id and r.price)
                if products:
                    if products[0].product_name:
                        product_name = products[0].product_name

                # price = products[0].price if products else product.standard_price
                if transport:
                    price = self.fare
                else:
                    price = line.price_unit or product.standard_price

                # Purchase order per line
                purchase_order = po.create({
                    'partner_id': partner.id,
                    'date_order': order_id.date,
                    'picking_type_id': self.picking_type_id.id,
                    'origin': self.name,
                    'order_line': [(0, 0, {
                        'product_id': product.id,
                        'name': product_name,
                        'date_planned': order_id.date,
                        'product_qty': quantity,
                        'product_uom': product.uom_po_id.id or product.uom_id.id,
                        'price_unit': price,
                        'taxes_id': [(4, x.id) for x in taxes],
                    })]
                })
                order = order_id if transport else line
                order.write({'purchase_id': purchase_order.id})
                purchase_order.button_confirm()
                if not product.landed_cost_ok:
                    for picking in purchase_order.picking_ids:
                        bacth_id = self.env['stock.picking.to.batch'].create(
                            {'batch_id': picking_batch.id}
                        )
                        bacth_id.with_context({'active_ids': picking.id}).attach_pickings()
        return purchase_order

    def generate_po(self):
        # Purchase order lines
        self.create_po(self.product_id, self.line_ids, self, False)
        # Purchase order transport
        self.create_po(self.product_transport_id, [self.transport_id], self, True)
        self.state = 'closed'
        return True

    
    def unlink(self):
        for purchase in self:
            if not purchase.state == 'draft':
                raise UserError(
                    _('In order to delete a massive purchase, you must draft it first.')
                )
        return super(MassivePurchase, self).unlink()

    def confirm(self):
        self.state = 'confirm'
        return True

    def cancel(self):
        self.state = 'cancel'
        return True

    def to_draft(self):
        self.state = 'draft'
        return True


class MassivePurchaseLines(models.Model):
    _name = 'massive.purchase.lines'
    _description = 'Massive Purchase Lines'

    massive_purchase_id = fields.Many2one('massive.purchase',
                                          string='Massive purchase',
                                          required=True,
                                          index=True,
                                          ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Partner', required=True, index=True)
    purchase_id = fields.Many2one('purchase.order', string='Purchase order',
                                  required=False, index=True, copy=False,
                                  readonly=True)
    quantity = fields.Integer(string='Quantity', default=0.0, required=True, copy=False)
    description = fields.Text(string='Description')
    price_unit = fields.Float(string='Price unit')
    price_total = fields.Float(compute='_get_total', string='Price total', store=True)

    
    @api.depends('price_unit', 'quantity')
    def _get_total(self):
        self.price_total = self.price_unit * self.quantity

    @api.onchange('partner_id')
    def onchange_partner(self):
        products = self.massive_purchase_id.product_id.seller_ids.filtered(
            lambda r: r.name.id == self.partner_id.id and r.price
        )
        price = products[0].price if products else self.massive_purchase_id.product_id.standard_price
        if not price:
            price = self.massive_purchase_id.product_id.standard_price
        self.price_unit = price


class StockPickingToBatch(models.TransientModel):
    _inherit = 'stock.picking.to.batch'

    
    def attach_pickings(self):
        # use active_ids to add picking line to the selected batch
        # self.ensure_one()
        picking_ids = self.env.context.get('active_ids')
        return self.env['stock.picking'].browse(picking_ids).write({'batch_id': self.batch_id.id})


class PurchaseOrderLineExtended(models.Model):
    _inherit = 'purchase.order.line'

    picking_type_id = fields.Many2one('stock.picking.type', string='Picking type', index=True)
    stock_holder = fields.Selection([('sh', 'Stock holder'), ('nsh', 'Not Stock holder')],
                                    'Stock holder', default='nsh', required=True)

    @api.model
    def create(self, vals):
        if vals.get('order_id'):
            order_id = self.env['purchase.order'].browse(vals.get('order_id'))
            vals['picking_type_id'] = order_id.picking_type_id.id
            vals['stock_holder'] = order_id.partner_id.stock_holder
        return super(PurchaseOrderLineExtended, self).create(vals)

    
    def write(self, vals):
        for record in self:
            if record.order_id:
                order_id = record.order_id
                vals['picking_type_id'] = order_id.picking_type_id.id
                vals['stock_holder'] = order_id.partner_id.stock_holder
        return super(PurchaseOrderLineExtended, self).write(vals)
