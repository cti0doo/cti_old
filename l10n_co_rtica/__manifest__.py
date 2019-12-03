# -*- coding: utf-8 -*-
{
    'name': "l10n_co_rtica",

    'summary': "Colombian ICA",

    'description': """""",
    'author': "CTI Ltda",
    # 'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'res_partner',
    'version': '13.0.1',
    'sequence': 30,
    # any module necessary for this one to work correctlyi
    'depends': ['l10n_co_account_uvt', 'sale','l10n_co_account_extended'],
    # always loaded
    'data': [
        # security
        'security/ir.model.access.csv',
        # data
        'data/res.partner.industry.xml',  #Problems with the ids
        'data/res.partner.industry.csv',
        'data/account.ciiu.csv',
        # views
        'views/account_ciiu_view.xml',
        'views/account_move_view.xml',
        # 'views/account_tax_view.xml',
        #'views/account_journal_view.xml',
        'views/product_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
