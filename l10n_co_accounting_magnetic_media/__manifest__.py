# -*- coding: utf-8 -*-
{
    'name': "Magnetic media",

    'summary': """
        Add report magnetic media.""",

    'description': """
        Add report magnetic media
    """,

    'author': "CTI Ltda",
    'contribuitor': 'Wilfredo Moreno',
    'website': "http://www.cti.com",
    'category': 'Accounting & Finance',
    'version': '13.0.0',
    'sequence': 30,
    'depends': ['l10n_co_accounting_templates'],
    'data': [
        # security
        'security/ir.model.access.csv',

        # data
        # NACIONALES
        'data/1001.xml',
        'data/1003.xml',
        'data/1004.xml',
        'data/1005.xml',
        'data/1006.xml',
        'data/1007.xml',
        'data/1008.xml',
        'data/1009.xml',
        'data/1010.xml',
        'data/1011.xml',
        'data/1012.xml',
        'data/2276.xml',
        # DISTRITALES
        'data/art_2.xml',
        'data/art_4.xml',
        'data/art_6.xml',

        #'data/magnetic.media.lines.csv', #CSV_Duplicates
        #'data/magnetic.media.lines.concepts.csv', #CSV_Duplicates
        # views
        'views/magnetic_media_views.xml',
    ],
    'demo': [],
    'installable': True,  # Tiene problemas con las referencias a cuentas contables
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
