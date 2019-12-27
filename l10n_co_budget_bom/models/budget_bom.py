# -*- coding: utf-8 -*-

import logging

from odoo.exceptions import UserError

from odoo import models, fields

_logger = logging.getLogger('BUDGET')


class BudgetBom(models.Model):
    _inherit = 'crossovered.budget'

    budget_id = fields.Many2one('crossovered.budget', string='Origin')

    def create_budget_for_bom(self):
        bom = False
        for line in self.crossovered_budget_line:
            if not line.bom_id:
                bom = self.env['mrp.bom'].search([('product_id', '=', line.product_id.id)])
                if len(bom) > 1:
                    raise UserError("The product has more than one bill of materials")
                else:
                    bom = line.bom_id
        budget = {'creating_user_id': self.env.user.id,
                  'date_from': self.date_from,
                  'date_to': self.date_to,
                  'company_id': self.company_id.id,
                  'budget_id': self.id,
                  'message_follower_ids': False,
                  'name': 'PURCHASE BUDGET - GENERATE FROM ' + self.name
                  }
        bg = self.create(budget)
        if not bom:
            raise UserError('''This product does not have a bill of materials.
                model: (product.variant)''')
        for bom_line in bom.bom_line_ids:
            cost = bom_line.product_id.standard_price
            qty = line.planned_quantity / bom_line.bom_id.product_qty * bom_line.product_qty
            bg.write({
                'crossovered_budget_line': [(0, 0, {
                    'general_budget_id': line.general_budget_id.id,
                    'product_id': bom_line.product_id.id,
                    'planned_amount': cost * qty,
                    'planned_quantity': qty,
                    'analytic_account_id': line.analytic_account_id.id,
                    'date_from': line.date_from,
                    'date_to': line.date_to,
                    'paid_date': line.paid_date,
                    'company_id': line.company_id.id
                })]
            })


class BudgetBomLines(models.Model):
    _inherit = 'crossovered.budget.lines'

    bom_id = fields.Many2one('mrp.bom', string='Bom', domain="[('product_id','=',product_id)]")
