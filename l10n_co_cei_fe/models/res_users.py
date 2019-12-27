#-*- coding:utf-8 -*-
from odoo import models, api, tools, fields
from odoo.exceptions import ValidationError
import logging


class Users(models.Model):
    _inherit = "res.users"

    def write(self,values):
        if 'company_id' in values:
            company_id = self.env['res.company'].search([('id','=',int(values['company_id']))])
            values.update({
                    'in_group_'+str(self.env.ref('l10n_co_cei_fe.group_electronic_billing_manager').id): company_id.fe_habilitar_facturacion
                })
        return super(Users, self).write(values)

