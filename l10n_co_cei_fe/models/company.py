# -*- coding:utf-8 -*-
from odoo import models, api, _, fields
from odoo.exceptions import ValidationError
import logging
import hashlib
import validators

_logger = logging.getLogger(__name__)


class Company(models.Model):
    _inherit = 'res.company'

    fe_habilitar_facturacion = fields.Boolean(
        string='Habilitar Facturación electrónica'
    )

    def write(self,values):
        if 'company_id' in values:
            company_id = self.env['res.company'].search([('id','=',int(values['company_id']))])
            values.update({
                    'in_group_'+str(self.env.ref('l10n_co_cei_fe.group_electronic_billing_manager').id): company_id.fe_habilitar_facturacion
                })
        return super(Company, self).write(values)