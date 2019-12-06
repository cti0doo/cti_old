# -*- coding: utf-8 -*-

import logging

from odoo import models, fields

# from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    firstname = fields.Char(string='Firstname')
    other_name = fields.Char(string='Other name')
    lastname = fields.Char(string='Lastname')
    other_lastname = fields.Char(string='Other lastname')
