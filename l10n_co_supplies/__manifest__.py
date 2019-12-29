# -*- coding: utf-8 -*-
{
    'name': "Supplies",

    'summary': """  """,

    'description': """
        Long description of module's purpose
    """,

    'author': "CTI Ltda",
    'website': "www.cti.com.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Inventory',
    'version': '13.0.0',
    'sequence': 110,
    # any module necessary for this one to work correctly
    'depends': ['sale_stock','sale_renting'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
