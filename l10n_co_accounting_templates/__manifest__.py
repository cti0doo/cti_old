# -*- coding: utf-8 -*-
{
    'name': "Accounting Templates",

    'summary': """
        Accounting Templates""",

    'description': """
        Puc and Taxes and fiscal position and fiscal position tax for each chart
        template and company fiscal position
    """,

    'author': "CTI Ltda",
    'contributor': 'Carlos Martinez and Wilfredo Moreno',
    'website': "http://www.cti.com.co",
    'category': 'Localization',
    'version': '13.0.0',
    'sequence': 110,
    # any module necessary for this one to work correctly
    'depends': ['account'],

    # always loaded
    'data': [
        'data/account.tax.group.csv',
        'data/account.account.type.xml',
        'data/account.group.csv',
        'data/account.account.tag.csv',
        'data/account.chart.template.csv',
        'data/account.account.template.csv',
        'data/account.tax.template.csv',
        'data/account.fiscal.position.template.csv',
        'data/account.fiscal.position.tax.template.csv',
        'data/account.fiscal.position.account.template.csv',
        'data/l10n_co_chart_post_data.xml',
        'views/chart_account_apply_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
