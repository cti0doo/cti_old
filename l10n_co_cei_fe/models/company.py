# -*- coding:utf-8 -*-
from odoo import models, api, _, fields
from odoo.exceptions import ValidationError, AccessError
import logging
import hashlib
import validators
import time

_logger = logging.getLogger(__name__)


class Company(models.Model):
    _inherit = 'res.company'

    fe_habilitar_facturacion = fields.Boolean(
        string='Habilitar Facturación electrónica'
    )