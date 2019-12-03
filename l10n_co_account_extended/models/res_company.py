# -*- coding: utf-8 -*-

import logging

from odoo import models, fields

# from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class ResCompanyTaxes(models.Model):
    _inherit = 'res.company'

    retention = fields.Boolean(string='Apply UVT rule', default=False,
                               help='this option allows to indicate if the company applies withholding to the rest of the third party')
