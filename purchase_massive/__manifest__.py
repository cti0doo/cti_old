# -*- coding: utf-8 -*-
{
    'name': "Massive purchase",

    'summary': """
        Module that allows to register massive purchases of the same product to several
        suppliers in a simple form
    """,

    'description': """
       Massive purchase
    """,

    'author': "CTI Ltda",
    'website': "http://www.cti.com.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Purchase',
    'version': '13.0.1.',

    # any module necessary for this one to work correctly
    'depends': ['account', 'purchase', 'stock_landed_costs', 'stock_picking_batch'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'reports/purchase_line_pivot.xml',
        'data/sequence.xml',
        'reports/purchase_templates.xml',
        'reports/purchase_massive_reports.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
