# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'budget_bom',
    'version': '13.0.0',
    'summary': 'budget_bom',
    'sequence': 120,
    'author': 'CTI Ltda',
    'contribuitor': 'Wilfredo Moreno',
    'description': """
    Create budget for bom
    """,
    'category': 'Accounting',
    'website': 'https://www.cti.com.co',
    'images': [],
    'depends': ['l10n_co_account_budget_additional_info'],
    'data': [
        'views/budget_bom_view.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
