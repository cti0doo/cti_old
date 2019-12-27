# -*- coding: utf-8 -*-
import logging
import base64
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ArchivosFE(models.Model):
    _name = 'l10n_co_cei.fe_archivos_email'

    invoice_id = fields.Many2one(
        'account.move',
        string='Factura'
    )
    nombre_archivo_envio = fields.Char(
        required=True,
        string='Nombre de fichero'
    )
    archivo_envio = fields.Binary(
        required=True,
        string='Archivo envío',
        attachment=True
    )


    @api.depends('archivo_envio')
    def compute_nombre_del_archivo(self):
        for invoice in self:
            dato = invoice.archivo_envio
            if dato:
                print('entro')
            else:
                print('else')

