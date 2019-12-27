# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MrpProduction(models.Model):
    _inherit = 'mrp.production'


    std_cost = fields.Float(default=0.0, string='Standard cost')

    prod_cost = fields.Float(default=0.0, string='Production cost')

    adjusted_cost = fields.Float(default=0.0, string='Adjusted real cost')
 
    def get_report_values(self, proid):
        productions = self.env['mrp.production'].search([('id', 'in', (proid,)), ('state', '=', 'done')])
        res = self.env['report.mrp_account_enterprise.mrp_cost_structure'].get_lines(productions)
        return res

    #To-Do: Report get_lines() only get the original cost of the products.
    def update_monthly_cost(self):
        productions = self.env['mrp.production'].search([('state', '=', 'done')])
        for prod in productions:
            report_values = self.get_report_values(prod.id)
            unit_cost = []
            for line in report_values:
                total_cost = line['total_cost']
                mo_qty = line['mo_qty']
                operations = line['operations']
                opcost = 0.0

                for row in operations:
                    opcost = opcost + row[3] * row[4]
                
                unit_cost.append((total_cost + opcost) / mo_qty)
            if unit_cost:
                prod.adjusted_cost = unit_cost[0]

    def write(self, values):

        if self.prod_cost <= 0.0 and self.state == 'done':

            report_values = self.get_report_values(self.id)
            unit_cost = []
            for line in report_values:
                total_cost = line['total_cost']
                mo_qty = line['mo_qty']
                operations = line['operations']
                opcost = 0.0

                for row in operations:
                    opcost = opcost + row[3] * row[4]
                
                unit_cost.append((total_cost + opcost) / mo_qty)
            
            if unit_cost:
                values['prod_cost'] = unit_cost[0]

        res = super(MrpProduction, self).write(values)
        return res


    @api.model
    def create(self, values):
     
        #New
        prod_cost = values.get('product_id')
        prod_cost = self.env['product.product'].browse(prod_cost)
        values['std_cost'] = prod_cost.standard_price
        
        res = super(MrpProduction, self).create(values)
        return res


