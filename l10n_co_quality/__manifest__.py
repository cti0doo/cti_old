# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Quality',
    'version': '13.0.0',
    'summary': 'quality',
    'sequence': 110,
    'author': 'CTI Ltda',
    'contribuitor': 'Wilfredo Moreno G.',
    'description': """Quality control""",
    'category': 'MRP',
    'website': 'https://www.cti.com.co',
    'images': [],
    'depends': ['account', 'quality_control','mrp','l10n_co_account_uvt','l10n_co_account_extended'],
    'data': [
        'security/ir.model.access.csv',
        'data/concepts_quality_data.xml',
        'views/quality_move.xml',
        'reports/report_quality_invoice.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
