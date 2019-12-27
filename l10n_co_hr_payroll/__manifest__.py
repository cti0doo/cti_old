#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
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
{
    'name': 'Employee Colombia',
    'version': '13.0.0',
    'category': 'Human Resources',
    'description': """
Add all information on the employee Colombia.
=============================================================

    * Social Security
    * Social Security type

You can assign several contracts per employee.
    """,
    'author': 'CTI Ltda',
    'website': 'http://www.cti.com.co',
    'images': ['images/hr_contract.jpeg'],
    'sequence': 120,
    'depends': [
        'l10n_co_accounting_templates',
        'hr_payroll_account',
        'date_range'
    ],
    'data': [
        #'security/ir.model.access.csv',

        # views
        'views/hr_employee_view.xml',
        'views/hr_payroll_account_view.xml',
        'views/hr_payslip_view.xml',
        'views/hr_apply_template_view.xml',
        'views/hr_leave_view.xml',

        # data
        'data/hr_leave_data.xml',
        'data/resource_calendar.xml',
        'data/hr_contribution_register.xml',
        'data/hr.deductible.type.csv',
        #'data/hr.diagnosis.csv',                   #Duplicate data
        'data/hr_salary_rule_category.xml',
        'data/hr_salary_rule_template_comercial.xml',
        'data/hr_salary_rule_template_comercial_extra.xml',
        'data/hr_salary_rule_template_comercial_integral.xml',
        'data/hr_salary_rule_template_niif_solidario.xml',
        'data/hr_salary_rule_template_niif_solidario_extra.xml',
        'data/hr_salary_rule_template_niif_solidario_integral.xml',
        'data/hr_payroll_structure_template_comercial.xml',
        #'data/ir_translation.xml',      #ToDo - Fix translations
    ],
    'demo': [],
    'css': ['static/src/css/partner_rules.css'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
