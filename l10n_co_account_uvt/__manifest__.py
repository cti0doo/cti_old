# -*- coding: utf-8 -*-
{
    'name': "l10n_co_account_uvt",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "CTI Ltda",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '13.0.0',

    # any module necessary for this one to work correctly
    'depends': ['account', 'date_range','l10n_co_accounting_templates'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/company_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}