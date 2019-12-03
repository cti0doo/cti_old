# -*- coding: utf-8 -*-
{
    'name': "Import/Export massive",

    'summary': """  """,
    'description': """Import/Export massive""",

    'author': "CTI Ltda",
    'website': "www.cti.com.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'All',
    'version': '13.0.3',
    'sequence': 110,
    # any module necessary for this one to work correctly

    'depends': ['sale','purchase','l10n_co_rtica'],
    # always loaded
    'data': [
        'data/ie.massive.filter.csv',
        'data/ie.massive.csv',
        'data/ie.massive.lines.csv', #CSV_Duplicates
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/massive_views.xml',
        'views/conf_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
