# -*- coding:utf-8 -*-
from odoo import models, api, _, fields
from odoo.exceptions import ValidationError
import logging
import hashlib
import validators

_logger = logging.getLogger(__name__)


class Company(models.Model):
    _inherit = 'res.company'

    facturacion_electronica_id = fields.Char(
        string="ID para facturación electrónica"
    )
    company_resolucion_ids = fields.One2many(
        'l10n_co_cei.company_resolucion',
        'company_id',
        string='Resoluciones'
    )
    fe_informacion_cuenta_bancaria = fields.Text(
        string='Información de cuenta bancaria'
    )
    responsabilidad_actividad_economica = fields.Char(
        string='Responsabilidad y actividad económica',
    )
    fe_certificado = fields.Binary(
        string='Certificado'
    )
    fe_certificado_password = fields.Char(
        string='Contraseña del certificado'
    )
    view_fe_certificado_password = fields.Char(
        string='Contraseña del certificado'
    )
    fe_software_id = fields.Char(
        string='ID de software'
    )
    fe_software_pin = fields.Char(
        string='PIN de software'
    )
    view_fe_software_pin = fields.Char(
        string='PIN de software'
    )
    fe_url_politica_firma = fields.Char(
        string='URL Política de firma'
    )
    fe_archivo_polica_firma = fields.Binary(
        string='Archivo de política de firma'
    )
    fe_descripcion_polica_firma = fields.Char(
        string='Descripción política de firma'
    )
    fe_tipo_ambiente = fields.Selection(
        selection = [
            ('1', 'Producción'),
            ('2', 'Pruebas Con Conteo DIAN'),
            ('3', 'Pruebas Sin Conteo DIAN')
        ],
        string='Ambiente de destino',
        default='2'
    )
    fe_test_set_id = fields.Char(
        string='ID para set de pruebas'
    )

    @staticmethod
    def validate_url(values):
        if 'fe_url_politica_firma' in values:
            if not validators.url(values['fe_url_politica_firma']):
                raise ValidationError('La URL para política de firma ingresada es inválida.')

    def hash_passwords(self, values):
        if self.fe_habilitar_facturacion:
            if not 'fe_habilitar_facturacion' in values or not values['fe_habilitar_facturacion']:
                return values
            else:
                if ('view_fe_certificado_password' in values and len(
                        values['view_fe_certificado_password']) != 0) or self.view_fe_certificado_password:
                    # sha256 = hashlib.sha256()
                    # sha256.update(values['view_fe_certificado_password'].encode('utf-8'))
                    values['fe_certificado_password'] = values['view_fe_certificado_password']
                    values['view_fe_certificado_password'] = None

                if ('view_fe_software_pin' in values and len(
                        values['view_fe_software_pin']) != 0) or self.view_fe_software_pin:
                    if not 'fe_software_id' in values and not self.fe_software_id:
                        raise ValidationError(
                            'El ID del Software es requerido si desea registrar un PIN.'
                        )

                    # software_id = self.fe_software_id if self.fe_software_id else values['fe_software_id']
                    software_id = values['fe_software_id'] if 'fe_software_id' in values else self.fe_software_id

                    # sha384 = hashlib.sha384()
                    # sha384.update((software_id + values['view_fe_software_pin']).encode('utf-8'))
                    # values['fe_software_pin'] = sha384.hexdigest()
                    values['fe_software_pin'] = values['view_fe_software_pin']
                    values['view_fe_software_pin'] = None

                return values
        elif 'fe_habilitar_facturacion' in values and values['fe_habilitar_facturacion']:
            if ('view_fe_certificado_password' in values and len(
                    values['view_fe_certificado_password']) != 0) or self.view_fe_certificado_password:
                # sha256 = hashlib.sha256()
                # sha256.update(values['view_fe_certificado_password'].encode('utf-8'))
                values['fe_certificado_password'] = values['view_fe_certificado_password']
                values['view_fe_certificado_password'] = None

            if ('view_fe_software_pin' in values and len(
                    values['view_fe_software_pin']) != 0) or self.view_fe_software_pin:
                if not 'fe_software_id' in values and not self.fe_software_id:
                    raise ValidationError(
                        'El ID del Software es requerido si desea registrar un PIN.'
                    )

                # software_id = self.fe_software_id if self.fe_software_id else values['fe_software_id']
                software_id = values['fe_software_id'] if 'fe_software_id' in values else self.fe_software_id

                # sha384 = hashlib.sha384()
                # sha384.update((software_id + values['view_fe_software_pin']).encode('utf-8'))
                # values['fe_software_pin'] = sha384.hexdigest()
                values['fe_software_pin'] = values['view_fe_software_pin']
                values['view_fe_software_pin'] = None

            return values
        else:
            return values

    @api.model
    def create(self, values):
        if self.fe_habilitar_facturacion:
            self.validate_url(values)
        values = self.hash_passwords(values)
        return super(Company, self).create(values)

    def write(self, values):
        if self.fe_habilitar_facturacion:
            self.validate_url(values)
        values = self.hash_passwords(values)
        return super(Company, self).write(values)