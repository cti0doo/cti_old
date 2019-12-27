# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Manufacture cost',
    'version': '13.0.0',
    'summary': 'Manufacture cost',
    'sequence': 110,
    'author': 'CTI Ltda',
    'contribuitor': 'Wilfredo Moreno',
    'description': "Manufacture cost by bom and work center",
    'category': 'MRP',
    'website': 'https://www.cti.com.co',
    'images': [],
    'depends': ['l10n_co_quality', 'mrp', 'stock_account', 'quality_control'],
    'data': [
        'views/cost_manufacture_view.xml',
        'views/manufacture_cost_analysis.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
