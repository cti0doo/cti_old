# -*- coding: utf-8 -*-
{
    'name': "l10n_co_account_extended",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.odoo.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "CTI Ltda",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '13.0.1',

    # any module necessary for this one to work correctly
    'depends': ['account', 'l10n_co_location', 'date_range'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/account_journal_view.xml',
        'views/company_view.xml',
        'views/partner_view.xml',
        'views/product_view.xml',
        'views/account_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}
