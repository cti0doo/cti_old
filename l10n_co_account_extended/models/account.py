# -*- coding: utf-8 -*-

import logging
from odoo.tools.safe_eval import safe_eval
from datetime import datetime
from odoo import models, fields, api
from odoo.tools.float_utils import float_compare
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProductTemplateTaxtope(models.Model):
    _inherit = 'product.template'

    tope_retention = fields.Float(string='Tope retention', default=0.0,
                                  help='Indicate the value that will be applied in taxes with cap for this product (UVT).')


class ProductCategoryTaxtope(models.Model):
    _inherit = 'product.category'

    tope_retention = fields.Float(string='Tope retention', default=0.0,
                                  help='Indicate the value that will be applied in taxes with cap for this product (UVT).')


class accountJournal(models.Model):
    _inherit = 'account.journal'

    resolution = fields.Text(string='Resolution')
    city_id = fields.Many2one('res.country.state.city', string='City', required=False)
    city_mrp_id = fields.Many2one('res.country.state.city', string='City (MRP)', required=False)


class contabilidad(models.Model):
    _inherit = 'account.account.template'

    parent_id = fields.Many2one('account.account.template', string='Parent ID')


class AccountInvoice(models.Model):
    _inherit = "account.move"

    invoice_date = fields.Date(default=lambda self: fields.Date.context_today(self))


class AccountInvoiceLines(models.Model):
    _inherit = "account.move.line"



class AccountTaxTemplate(models.Model):
    _inherit = 'account.tax.template'

    limit = fields.Boolean(string='Limit', default=False,
                           help='This option allows to indicate that this tax has a cap indicated in the product category.')


class AccountTaxUVT(models.Model):
    _inherit = 'account.tax'

    limit = fields.Boolean(string='Limit', default=False,
                           help='This option allows to indicate that this tax has a cap indicated in the product category.')
    