# -*- coding: utf-8 -*-

##############################################################################
#
#    odoo, Open Source Management Solution
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

from datetime import datetime
from odoo import api, models, fields, _

from odoo.exceptions import UserError


class crossovered_budget_lines(models.Model):
    _inherit = 'crossovered.budget.lines'

    
    def _compute_prac_qty(self):
        result = 0.0
        for line in self:
            acc_ids = [x.id for x in line.general_budget_id.account_ids]
            if not acc_ids:
                raise UserError(
                    _("Budget '{}' has no accounts!").format(line.general_budget_id.name)
                )
            date_to = self.env.context.get('wizard_date_to') or line.date_to
            date_from = self.env.context.get('wizard_date_from') or line.date_from
            if line.analytic_account_id.id:
                sql_params = {
                    "analytic_account_id": line.analytic_account_id.id,
                    "date_from": date_from,
                    "date_to": date_to,
                    "account_id": acc_ids,
                    "partner_id": line.partner_id.id,
                    "product_id": line.product_id.id,
                }
                sql = ("SELECT SUM(unit_amount) "
                       "FROM  budget_line_report "
                       "WHERE analytic_account_id = %(analytic_account_id)s "
                       "AND (date BETWEEN to_date('%(date_from)s','yyyy-mm-dd') "
                       "    AND to_date('%(date_to)s','yyyy-mm-dd')) "
                       "AND account_id = ANY(array%(account_id)s) ")
                sql += "AND {}".format(
                    "partner_id = %(partner_id)s " if line.partner_id else "partner_id IS NULL "
                )
                sql += "AND {}".format(
                    "product_id = %(product_id)s " if line.product_id else "product_id IS NULL "
                )

                self.env.cr.execute(sql % sql_params)
                result = self.env.cr.fetchone()[0]
            if result is None:
                result = 0.00
            line.practical_quantity = result

    
    def _compute_perc_qty(self):
        for line in self:
            if line.theoretical_quantity != 0.00:
                line.percentage_quantity = float((line.practical_quantity or 0.0) /
                                                 line.theoretical_quantity) * 100
            else:
                line.percentage_quantity = 0.00

    
    def _compute_theo_qty(self):
        for line in self:
            today = datetime.now().date()
            # Used for the report
            if self.env.context.get('wizard_date_from') and self.env.context.get('wizard_date_to'):
                date_from = self.env.context.get('wizard_date_from')
                date_to = self.env.context.get('wizard_date_to')
                if date_from < line.date_from:
                    date_from = line.date_from
                elif date_from > line.date_to:
                    date_from = False

                if date_to > line.date_to:
                    date_to = line.date_to
                elif date_to < line.date_from:
                    date_to = False

                if date_from and date_to:
                    line_timedelta = line.date_to - line.date_from
                    elapsed_timedelta = date_to - date_from
                    if elapsed_timedelta.days > 0:
                        theo_qty = (
                                           elapsed_timedelta.total_seconds() / line_timedelta.total_seconds()
                                   ) * line.planned_quantity
            else:
                if line.paid_date:
                    if line.date_to <= line.paid_date:
                        theo_qty = 0.00
                    else:
                        theo_qty = line.planned_quantity
                else:

                    line_timedelta = line.date_to - line.date_from
                    elapsed_timedelta = today - line.date_from

                    if elapsed_timedelta.days < 0:
                        # If the budget line has not started yet, theoretical amount should be zero
                        theo_qty = 0.00
                    elif line_timedelta.days > 0 and today < line.date_to:
                        # If today is between the budget line date_from and date_to
                        # from pudb import set_trace; set_trace()
                        theo_qty = (
                                           elapsed_timedelta.total_seconds() / line_timedelta.total_seconds()
                                   ) * line.planned_quantity
                    else:
                        theo_qty = line.planned_quantity

            line.theoretical_quantity = theo_qty

    product_id = fields.Many2one('product.product', string='Product')
    partner_id = fields.Many2one('res.partner', string='Partner')
    planned_quantity = fields.Float('Planned Quantity', required=True, digits=0, default=0.0)
    practical_quantity = fields.Float(compute="_compute_prac_qty", string='Practical Quantity')
    theoretical_quantity = fields.Float(
        compute="_compute_theo_qty", string='Theoretical Quantity')
    percentage_quantity = fields.Float(
        compute="_compute_perc_qty", string='Achievement Quantity')

    
    def _compute_practical_amount(self):
        for line in self:
            acc_ids = line.general_budget_id.account_ids
            date_to = self.env.context.get('wizard_date_to') or line.date_to
            date_from = self.env.context.get('wizard_date_from') or line.date_from

            if line.analytic_account_id.id:
                query_obj = self.env['account.analytic.line']
                field = "SUM(amount)"

                domain = [
                    ('account_id', '=', line.analytic_account_id.id),
                    ('date', '>=', date_from),
                    ('date', '<=', date_to),
                ]

                if line.partner_id:
                    domain += [('partner_id', '=', line.partner_id.id)]
                if line.product_id:
                    domain += [('product_id', '=', line.product_id.id)]
                if acc_ids:
                    domain += [('general_account_id', 'in', acc_ids.ids)]
            else:
                query_obj = self.env['account.move.line']
                field = "SUM(credit)-SUM(debit)"

                domain = [
                    ('account_id', 'in', line.general_budget_id.account_ids.ids),
                    ('date', '>=', date_from),
                    ('date', '<=', date_to)
                ]

                if line.partner_id:
                    domain += [('partner_id', '=', line.partner_id.id)]
                if line.product_id:
                    domain += [('product_id', '=', line.product_id.id)]

            where_query = query_obj._where_calc(domain)
            query_obj._apply_ir_rules(where_query, 'read')
            from_clause, where_clause, where_clause_params = where_query.get_sql()

            select = "SELECT {field} FROM {from_clause} WHERE {where_clause}".format(
                field=field,
                from_clause=from_clause,
                where_clause=where_clause
            )

            self.env.cr.execute(select, where_clause_params)
            line.practical_amount = self.env.cr.fetchone()[0] or 0.0
