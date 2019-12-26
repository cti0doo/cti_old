# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MrpProduction(models.Model):
    _inherit = 'mrp.production'


    original_product_price = fields.Float(default=0.0)

    real_cost = fields.Float(default=0.0)

    def get_report_values(self, proid):
        productions = self.env['mrp.production'].search([('product_id', 'in', (proid,)), ('state', '=', 'done')])
        res = self.env['report.mrp_account_enterprise.mrp_cost_structure'].get_lines(productions)
        return res

    def write(self, values):

        if self.real_cost <= 0.0 and self.state == 'done':

            report_values = self.get_report_values(self.id)
            unit_cost = []
            for line in report_values:
                total_cost = line['total_cost']
                mo_qty = line['mo_qty']
                operations = line['operations']
                opcost = 0.0

                for row in operations:
                    optcost = opcost + row[3] * row[4]
                
                unit_cost.append((total_cost + opcost) / mo_qty)

            values['real_cost'] = unit_cost[0]

        res = super(MrpProduction, self).write(values)
        return res


    @api.model
    def create(self, values):
     
        #New
        prod_cost = values.get('product_id')
        prod_cost = self.env['product.product'].browse(prod_cost)
        values['original_product_price'] = prod_cost.standard_price
        
        res = super(MrpProduction, self).create(values)
        return res


