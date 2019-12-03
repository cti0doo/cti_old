# -*- coding: utf-8 -*-
{
    'name': "account_budget_additional_info",

    'summary': """
        Add partner & product to budget """,

    'description': """
        Add partner and product to budget entries lines and informs
    """,

    'author': "CTI Ltda",
    'contribuitor': 'Carlos Martinez',
    'website': "http://www.cti.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting & Finance',
    'version': '13.0.0',
    'sequence': 30,
    # any module necessary for this one to work correctly
    'depends': ['account_budget'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/crossovered_budget_view.xml',
        'views/crossovered_budget_lines_view.xml',
        'views/report_line_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
