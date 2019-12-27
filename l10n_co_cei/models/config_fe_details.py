# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ConfigFEDetails(models.Model):
    _name = 'l10n_co_cei.config_fe_details'

    name = fields.Char(string='Nombre del campo')
    description = fields.Char(string='Descripción del campo')
    tipo = fields.Char(string='Tipo de dato')
    # ciudad_nombre
    # departamento_nombre
    # direccion
    # first_name
    # first_lastname
    # middle_name
    # tipo_documento
    # is_company

