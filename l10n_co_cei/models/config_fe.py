# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ConfigFE(models.Model):
    _name = 'l10n_co_cei.config_fe'

    config_fe_detail_id = fields.Many2one(
        'l10n_co_cei.config_fe_details',
        string='Detalle Configuración',
        required=True
    )
    model_name = fields.Char(string='Nombre del modelo')
    field_name = fields.Text(string='Nombre del campo')
    
    @api.constrains('config_fe_detail_id')
    def _check_unique_config_fe_detail_id(self):
        config_fes = self.env['l10n_co_cei.config_fe'].search([])

        count = 0

        for config_fe in config_fes:
            if config_fe.config_fe_detail_id.id == self.config_fe_detail_id.id:
                count += 1

        if count > 1:
            raise ValidationError(
                "Solo es permitido un valor por detalle de configuración"
            )
    
    def get_value(self, field_name, obj_id, can_be_null=False):
        if not field_name:
            raise ValidationError("Parámetro 'field_name' no válido.")
        if not obj_id:
            raise ValidationError("Debe incluir un ID para la búsqueda.")

        config_fes = self.env['l10n_co_cei.config_fe'].search([])

        config_fe = None

        for conf in config_fes:
            if conf.config_fe_detail_id.name == field_name:
                config_fe = conf
                break
        
        if not config_fe:
            raise ValidationError("'field_name' (%s) no encontrado." % field_name)
        if not 'model_name' in config_fe:
            raise ValidationError("Nombre del modelo no configurado.")
        if not 'field_name' in config_fe:
            raise ValidationError("Nombre de campo no configurado.")
        
        obj = self.env[config_fe.model_name].search([('id', '=', obj_id)], limit=1)

        if not obj:
            raise ValidationError("No se encontraron registros con el ID propocionado.")

        attributes = config_fe.field_name.split('.')
        for attribute in attributes:
            is_function = False
            if '()' in attribute:
                attribute = attribute[:-2]
                is_function = True
            if attribute in dir(obj):
                obj = getattr(obj, attribute)() if is_function else getattr(obj, attribute)
            else:
                # raise ValidationError("Atributo %s no encontrado en objeto. Buscando %s" % (attribute, field_name))
                raise ValidationError(
                    'No se encontró el atributo {} en el objeto. Por favor '
                    'verifique que la información del campo {} sea correcta.'.format(attribute, field_name)
                )

        if not type(obj).__name__ == config_fe.config_fe_detail_id.tipo:
            if not can_be_null:
                raise ValidationError(
                    # "Atributo %s encontrado pero no coincide con el tipo de dato esperado (%s / %s / %s)."
                    # "El atributo {} existe y es de tipo {}, pero se requiere un tipo {}. "
                    "Por favor verifique que el valor del campo {} sea correcto."
                    .format(attributes[-1], type(obj).__name__, config_fe.config_fe_detail_id.tipo, field_name)
                    # %
                    # (attributes[-1], config_fe.config_fe_detail_id.tipo, type(obj).__name__, field_name)
                )
        return obj
