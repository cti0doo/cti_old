# -*- coding: utf-8 -*-
{
    'name': "Facturación electrónica Colombia",

    'summary': """
        Law compliant electronic invoicing for Colombia.""",

    'description': """ 
        Add-on for electronic invoicing generation that meets the 
        requirements of the resolution issued by DIAN.
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
    'depends': ['base', 'account', 'l10n_co', 'contacts', 'mail', 'l10n_co_cei_fe'],

    # always loaded
    'data': [
        # initial data
        'data/tercero_config_fe_details.xml',
        'data/company_config_fe_details.xml',
        'data/sucursal_config_fe_details.xml',
        'data/tercero_config_fe.xml',
        'data/company_config_fe.xml',
        'data/sucursal_config_fe.xml',
        'data/cron_envio_a_dian.xml',
        'data/paper_format.xml',
        'data/account_tax_type.xml',
        #'data/account_tax.xml',
        'data/account_payment_mean.xml',
        'data/ir_config_parameter.xml',
        'data/ir_sequence.xml',
        # reports
        'reports/invoice_custom.xml',
        'reports/invoice_custom_email.xml',
        # views
        'views/company_resolucion.xml',
        'views/config_fe.xml',
        'views/company_resolucion.xml',
        'views/account_invoice.xml',
        'views/res_company.xml',
        'views/res_currency.xml',
        'views/approve_invoice_fe_email_pages.xml',
        'views/envio_fe_view.xml',
        'views/factura_proveedor.xml',
        'views/tax_view.xml',
        'views/payment_mean_view.xml',
        'views/payment_term_view.xml',
        'views/account_journal.xml',
        'views/ir_sequence_view.xml',
        'views/tax_type.xml',
        # emails
        'data/approve_invoice_fe_email.xml',
        # security
        'security/ir.model.access.csv',
        'security/ir.rule.csv',
        # registration rules
        'data/regla_registro_fe_enviadas.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
