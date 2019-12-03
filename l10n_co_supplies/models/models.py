# -*- coding: utf-8 -*-

import logging

from lxml import etree

from odoo import models, fields, api, _

_logger = logging.getLogger('SUPPLIES')


class PartnerSupplies(models.Model):
    _inherit = 'res.partner'

    supply = fields.Boolean(string='Supplies')


class OrdersSupplies(models.Model):
    _inherit = 'sale.order'

    supplies = fields.Boolean(string='Supplies')

    @api.model
    def create(self, vals):
        if vals.get('supplies', False):
            vals['name'] = self.env['ir.sequence'].next_by_code('supplies.order') or _('New')
            _logger.debug(vals['name'])
        res = super(OrdersSupplies, self).create(vals)
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        context = self._context or {}
        res = super(OrdersSupplies, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                          toolbar=toolbar, submenu=False)
        if context.get('supplies'):
            if res.get('fields').get('partner_id'):
                res.get('fields').get('partner_id')['string'] = 'Applicant'
            if res.get('fields').get('state'):
                res.get('fields').get('state').get('selection')[0] = ('draft', 'Draft')
                res.get('fields').get('state').get('selection')[1] = ('sent', 'Sent')
                res.get('fields').get('state').get('selection')[2] = ('sale', 'Confirmed')
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='partner_id']"):
                node.set('domain', "[('supply', '=', True)]")
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res


class OrdersSuppliesLines(models.Model):
    _inherit = 'sale.order.line'

    def _get_domain(self):
        domain = "[('sale_ok','=',True)]"
        if self.env.context.get('supplies'):
            domain = "[('purchase_ok','=',True),('can_be_expensed','=',True),('type','=','product')]"
        _logger.info(domain)
        return domain

    product_id = fields.Many2one('product.product', string='Producto', domain=_get_domain)
