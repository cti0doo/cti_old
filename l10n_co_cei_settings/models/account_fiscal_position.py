# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    fe_codigo_dian = fields.Selection(
        selection=[
            ('00', 'Simplificado'),
            ('02', 'Común'),
            ('03', 'No aplicable'),
            ('04', 'Simple'),
            ('05', 'Ordinario')
        ],
        string='Código DIAN',
        required=False
    )

    fe_habilitada_compania = fields.Boolean(
        string='FE Compañía',
        compute='compute_fe_habilitada_compania',
        store=False,
        copy=False
    )

    @api.depends('fe_codigo_dian')
    def compute_fe_habilitada_compania(self):
        for record in self:
            if record.company_id:
                record.fe_habilitada_compania = record.company_id.fe_habilitar_facturacion
            else:
                record.fe_habilitada_compania = self.env.company.fe_habilitar_facturacion