# -*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

from odoo import models, fields


class hr_payroll_structure_template(models.Model):
    """
    Salary structure used to defined
    - Basic
    - Allowances
    - Deductions
    """
    _name = 'hr.payroll.structure.template'
    _description = 'Salary Structure'

    name = fields.Char('Name', size=256, required=True, translate=True)
    code = fields.Char('Reference', size=64, required=True)
    note = fields.Text('Description')
    parent_id = fields.Many2one('hr.payroll.structure.template', 'Parent')
    children_ids = fields.One2many('hr.payroll.structure.template', 'parent_id', 'Children')
    rule_ids = fields.Many2many('hr.salary.rule.template', 'hr_structure_salary_rule_rel_template', 'struct_id',
                                'rule_id', 'Salary Rules')
    chart_template_id = fields.Many2one('account.chart.template', 'Chart Template')


class hr_contribution_register_template(models.Model):
    '''
    Contribution Register
    '''

    _name = 'res.partner.template'
    _description = 'Contribution Register'

    name = fields.Char('Name', size=256, required=True, readonly=False, translate=True)
    note = fields.Text('Description')


class hr_salary_rule_category_template(models.Model):
    """
    HR Salary Rule Category
    """

    _name = 'hr.salary.rule.category.template'
    _description = 'Salary Rule Category Template'

    name = fields.Char('Name', size=64, required=True, readonly=False, translate=True)
    code = fields.Char('Code', size=64, required=True, readonly=False)
    parent_id = fields.Many2one('hr.salary.rule.category.template', 'Parent',
                                help="Linking a salary category to its parent is used only for the reporting purpose.")
    children_ids = fields.One2many('hr.salary.rule.category.template', 'parent_id', 'Children')
    note = fields.Text('Description')


class hr_rule_input_template(models.Model):
    '''
    Salary Rule Input Template
    '''

    _name = 'hr.rule.input.template'
    _description = 'Salary Rule Input'

    name = fields.Char('Description', size=256, required=True, translate=True)
    code = fields.Char('Code', size=52, required=True, help="The code that can be used in the salary rules")
    assing_value = fields.Boolean('Assing Value in Contract', default=False)
    input_id = fields.Many2one('hr.salary.rule.template', 'Salary Rule Input', required=True)
    chart_template_id = fields.Many2one('account.chart.template', 'Chart Template')

    
class hr_rule_input(models.Model):
    _name = 'hr.rule.input'
    _description = 'Salary Rule Input'

    assing_value = fields.Boolean('Assing Value in Contract', default=False)
    name = fields.Char(string='Description', required=True, translate=True)
    code = fields.Char(required=True, help="The code that can be used in the salary rules")
    input_id = fields.Many2one('hr.salary.rule', string='Salary Rule Input', required=True)

class hr_salary_rule_template(models.Model):
    _name = 'hr.salary.rule.template'
    _description = 'HR Salary Rule Template'

    name = fields.Char('Name', size=256, required=True, readonly=False, translate=True)
    code = fields.Char('Code', size=64, required=True,
                       help="The code of salary rules can be used as reference in computation of other rules. In that case, it is case sensitive.")
    sequence = fields.Integer('Sequence', required=True, help='Use to arrange calculation sequence', index=True,
                              default=5)
    quantity = fields.Char('Quantity', size=256,
                           help="It is used in computation for percentage and fixed amount.For e.g. A rule for Meal Voucher having fixed amount of 1€ per worked day can have its quantity defined in expression like worked_days.WORK100.number_of_days.",
                           default=1)
    category_id = fields.Many2one('hr.salary.rule.category.template', 'Category', required=True)
    active = fields.Boolean('Active',
                            help="If the active field is set to false, it will allow you to hide the salary rule without removing it.",
                            default=True)
    appears_on_payslip = fields.Boolean('Appears on Payslip', help="Used to display the salary rule on payslip.",
                                        default=True)
    parent_rule_id = fields.Many2one('hr.salary.rule.template', 'Parent Salary Rule', index=True)
    condition_select = fields.Selection([('none', 'Always True'), ('range', 'Range'), ('python', 'Python Expression')],
                                        "Condition Based on", required=True, default='none')
    condition_range = fields.Char('Range Based on', size=1024, readonly=False,
                                  help='This will be used to compute the % fields values; in general it is on basic, but you can also use categories code fields in lowercase as a variable names (hra, ma, lta, etc.) and the variable basic.',
                                  default='contract.wage')
    condition_python = fields.Text('Python Condition', required=True, readonly=False,
                                   help='Applied this rule for calculation if condition is true. You can specify condition like basic > 1000.',
                                   default='''
# Available variables:
#----------------------
# payslip: object containing the payslips
# employee: hr.employee object
# contract: hr.contract object
# rules: object containing the rules code (previously computed)
# categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
# worked_days: object containing the computed worked days
# inputs: object containing the computed inputs

# Note: returned value have to be set in the variable 'result'

result = rules.NET > categories.NET * 0.10''')
    condition_range_min = fields.Float('Minimum Range', required=False,
                                       help="The minimum amount, applied for this rule.")
    condition_range_max = fields.Float('Maximum Range', required=False,
                                       help="The maximum amount, applied for this rule.")
    amount_select = fields.Selection([
        ('percentage', 'Percentage (%)'),
        ('fix', 'Fixed Amount'),
        ('code', 'Python Code')
    ], 'Amount Type', index=True, required=True, help="The computation method for the rule amount.", default='fix')
    amount_fix = fields.Float('Fixed Amount', digits='Payroll', default=0)
    amount_percentage = fields.Float('Percentage (%)', digits='Payroll Rate',
                                     help='For example, enter 50.0 to apply a percentage of 50%', default=0)
    amount_python_compute = fields.Text('Python Code', default=''' # Available variables:
#----------------------
# payslip: object containing the payslips
# employee: hr.employee object
# contract: hr.contract object
# rules: object containing the rules code (previously computed)
# categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
# worked_days: object containing the computed worked days.
# inputs: object containing the computed inputs.

# Note: returned value have to be set in the variable 'result'

result = contract.wage * 0.10''')
    amount_percentage_base = fields.Char('Percentage based on', size=1024, required=False, readonly=False,
                                         help='result will be affected to a variable')
    child_ids = fields.One2many('hr.salary.rule.template', 'parent_rule_id', 'Child Salary Rule')
    register_id = fields.Many2one('res.partner', 'Contribution Register',
                                  help="Eventual third party involved in the salary payment of the employees.")
    input_ids = fields.One2many('hr.rule.input.template', 'input_id', 'Inputs')
    note = fields.Text('Description')
    account_tax_id = fields.Many2one('account.tax.template', 'Tax Template')
    account_debit = fields.Many2one('account.account.template', 'Debit Account')
    account_credit = fields.Many2one('account.account.template', 'Credit Account')
    chart_template_id = fields.Many2one('account.chart.template', 'Chart Template')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
