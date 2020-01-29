# -*- coding: utf-8 -*-
{
    'name': "Configuración Ciudades DIAN Colombia",

    'summary': """
        Crea un modelo para gestión de ciudades. Adicona un campo para el código del DANE""",

    'description': """
        Crea un modelo para gestión de ciudades. Adicona un campo para el código del DANE.
        Se modifica la vista de Res Partner
    """,

    'author': "Pragmatic SAS",
    'website': "http://www.pragmatic.com.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Invoicing & Payments',
    'version': '13.3.3.0',
    'license': 'OPL-1',
    'support': 'soporte.fe@pragmatic.com.co',

    # any module necessary for this one to work correctly
    'depends': ['base', 'l10n_co_cei_settings'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/country.xml',
        'views/state.xml',
        'views/cities.xml',
        'views/menu.xml',
        'views/res_partner.xml',
        'data/cities.xml',


    ],
}
