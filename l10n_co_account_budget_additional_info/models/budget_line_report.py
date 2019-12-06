# -*- coding: utf-8 -*-

##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, tools


class budget_line_report(models.Model):
    _name = 'budget.line.report'
    _description = 'View for budget line report'
    _auto = False

    analytic_account_id = fields.Many2one('account.analytic.account',
                                          string='Analytic Account',
                                          index=True, readonly=True)
    account_id = fields.Many2one('account.account', string='Financial Account',
                                 readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    date = fields.Date('Date', required=True, index=True, readonly=True)
    date_from = fields.Date('Date from', required=True, index=True, readonly=True)
    date_to = fields.Date('Date to', required=True, index=True, readonly=True)
    paid_date = fields.Date('Paid date', required=True, index=True, readonly=True)
    amount = fields.Monetary(currency_field='company_currency_id', string='Practical amount',
                             readonly=True)
    planned_amount = fields.Monetary(currency_field='company_currency_id',
                                     string='Planned amount', readonly=True)
    planned_quantity = fields.Float('Planned Quantity', default=0.0, readonly=True)
    unit_amount = fields.Float('Practical quantity', default=0.0, readonly=True)
    amount_percentage = fields.Monetary(currency_field='company_currency_id',
                                        string='Amount percentage', readonly=True)
    quantity_percentage = fields.Float('Quantity percentage', default=0.0, readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    company_currency_id = fields.Many2one('res.currency', readonly=True,
                                          related='company_id.currency_id',
                                          help='Utility field to express amount currency')

    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'budget_line_report')
        self.env.cr.execute("""CREATE OR REPLACE VIEW budget_line_report AS
                SELECT c.id, c.create_date, c.create_uid, c.write_date, c.write_uid, c.company_id,
                       c.analytic_account_id, a.general_account_id as account_id, a.partner_id, a.product_id, a.date,
                       c.date_from, c.date_to, c.paid_date, c.planned_amount, c.planned_quantity,
                       SUM(a.amount) as amount, SUM(a.unit_amount) as unit_amount,
                       SUM(a.amount)/(case c.planned_amount when 0 then null else c.planned_amount end) * 100 as amount_percentage,
                       SUM(a.unit_amount)/(case c.planned_quantity when 0 then null else c.planned_quantity end) * 100 as quantity_percentage
                  FROM crossovered_budget_lines c
                  LEFT JOIN account_analytic_line a ON c.analytic_account_id = a.account_id
                        AND (a.partner_id = c.partner_id or c.partner_id is null)
                        AND (a.product_id = c.product_id or c.product_id is null)
                  WHERE a.partner_id is not null
                    AND a.product_id is not null
                  GROUP BY c.id, c.create_date, c.create_uid, c.write_date, c.write_uid,
                           a.company_id, c.analytic_account_id, a.general_account_id, a.partner_id, a.product_id, a.date,
                           c.partner_id, c.product_id, c.date_from, c.date_to, c.paid_date,
                           c.planned_amount, c.planned_quantity """)

