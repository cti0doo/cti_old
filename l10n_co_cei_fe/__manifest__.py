# -*- coding: utf-8 -*-
{
    'name': "Habilitación de FE",

    'summary': """
        Este modulo permite habilitar o des habilitar FE en colombia""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Pragmatic S.A.S.",
    'website': "https://www.pragmatic.com.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Invoicing & Payments',
    'version': '13.3.3.0',
    'license': 'OPL-1',
    'support': 'soporte.fe@pragmatic.com.co',
    'price': '99',
    'currency': 'EUR',
    'images': ['static/description/splasher.jpg'],

    # any module necessary for this one to work correctly
    'depends': ['base', 'contacts', 'mail'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_company.xml',
        'data/res_groups.xml',
    ],
}