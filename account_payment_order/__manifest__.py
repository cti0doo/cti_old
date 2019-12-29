# -*- coding: utf-8 -*-
{
    'name': "Account payment order",

    'summary': """
        Account payment order""",

    'description': """
        Account payment order
    """,

    'author': "CTI Ltda",
    'website': "http://www.cti.com.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '13.0.1',

    # any module necessary for this one to work correctly
    'depends': ['l10n_co_location', 'payment'],

    # always loaded
    'data': [
        # security
        'security/ir.model.access.csv',

        # data
        'data/res.bank.xml',
        'data/res.bank.conf.csv',
        'data/res.bank.statement.conf.lines.csv',

        # views
        'views/views.xml',
        'views/bank_view.xml',
        'views/account_bank_statement_import_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
