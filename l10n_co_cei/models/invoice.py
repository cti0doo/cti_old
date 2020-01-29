# -*- coding: utf-8 -*-
import datetime
from datetime import timedelta
import hashlib
import logging
import os
import pyqrcode
import zipfile
import pytz

from .amount_to_txt_es import amount_to_text_es
from .signature import *
from enum import Enum
from jinja2 import Template
from odoo.exceptions import ValidationError
from odoo import models, fields, api
from lxml import etree
from xml.sax import saxutils
from .helpers import WsdlQueryHelper

_logger = logging.getLogger(__name__)
urllib3_logger = logging.getLogger('urllib3')
urllib3_logger.setLevel(logging.ERROR)

fe_company = None
fe_tercero = None
fe_sucursal_data = None


class ConfigFE(Enum):
    company_ciudad = 'company_ciudad'
    company_departamento = 'company_departamento'
    company_direccion = 'company_direccion'
    company_nit = 'company_nit'
    company_digito_verificacion = 'company_digito_verificacion'
    company_tipo_documento = 'company_tipo_documento'
    company_email_from = 'company_email_from'
    company_tipo_regimen = 'company_tipo_regimen'
    company_telefono = 'company_telefono'
    company_matricula_mercantil = 'company_matricula_mercantil'
    company_responsabilidad_fiscal = 'company_responsabilidad_fiscal'

    tercero_es_compania = 'tercero_es_compania'
    tercero_ciudad = 'tercero_ciudad'
    tercero_departamento = 'tercero_departamento'
    tercero_direccion = 'tercero_direccion'
    tercero_razon_social = 'tercero_razon_social'
    tercero_primer_apellido = 'tercero_primer_apellido'
    tercero_segundo_apellido = 'tercero_segundo_apellido'
    tercero_primer_nombre = 'tercero_primer_nombre'
    tercero_segundo_nombre = 'tercero_segundo_nombre'
    tercero_nit = 'tercero_nit'
    tercero_digito_verificacion = 'tercero_digito_verificacion'
    tercero_tipo_documento = 'tercero_tipo_documento'
    tercero_to_email = 'tercero_to_email'
    tercero_tipo_regimen = 'tercero_tipo_regimen'
    tercero_telefono = 'tercero_telefono'
    tercero_matricula_mercantil = 'tercero_matricula_mercantil'
    tercero_responsabilidad_fiscal = 'tercero_responsabilidad_fiscal'

    sucursal_ciudad = 'sucursal_ciudad'
    sucursal_departamento = 'sucursal_departamento'
    sucursal_direccion = 'sucursal_direccion'
    sucursal_to_email = 'sucursal_to_email'
    sucursal_telefono = 'sucursal_telefono'

class Invoice(models.Model):
    _inherit = "account.move"
    company_resolucion_id = fields.Many2one(
        'l10n_co_cei.company_resolucion',
        string='Resolución',
        ondelete='set null',
        required=False,
        copy=False
    )
    envio_fe_id = fields.Many2one(
        'l10n_co_cei.envio_fe',
        string='Envío Factura',
        copy=False
    )
    consecutivo_envio = fields.Integer(
        string='Consecutivo envío',
        ondelete='set null',
        copy=False
    )
    attachment_id = fields.Many2one(
        'ir.attachment',
        string='Archivo Adjunto',
        copy=False
    )
    nonce = fields.Char(
        string='Nonce',
        copy=False
    )
    fecha_envio = fields.Datetime(
        string='Fecha de envío en UTC',
        copy=False
    )
    filename = fields.Char(
        string='Nombre de Archivo',
        copy=False
    )
    file = fields.Binary(
        string='Archivo',
        copy=False
    )
    zipped_file = fields.Binary(
        string='Archivo Compreso',
        copy=False
    )
    firmado = fields.Boolean(
        string="¿Está firmado?",
        default=False,
        copy=False
    )
    enviada = fields.Boolean(
        string="Enviada",
        default=False,
        copy=False
    )
    cufe_seed = fields.Char(
        string='CUFE seed',
        copy=False
    )
    cufe = fields.Char(
        string='CUFE',
        copy=False
    )
    qr_code = fields.Binary(
        string='Código QR',
        copy=False
    )

    fe_company_nit = fields.Char(
        string='NIT Compañía',
        compute='compute_fe_company_nit',
        store=False,
        copy=False
    )
    fe_tercero_nit = fields.Char(
        string='NIT Tercero',
        compute='compute_fe_tercero_nit',
        store=False,
        copy=False
    )

    fe_company_digito_verificacion = fields.Char(
        string='Digíto Verificación Compañía',
        compute='compute_fe_company_digito_verificacion',
        store=False,
        copy=False
    )

    amount_total_text = fields.Char(
        compute='_amount_int_text',
        copy=False
    )

    amount_total_text_cent = fields.Char(
        compute='_amount_int_text',
        copy=False
    )

    fe_approved = fields.Selection(
        selection = [
            ('sin-calificacion', 'Sin calificar'),
            ('aprobada', 'Aprobada'),
            ('aprobada_sistema', 'Aprobada por el Sistema'),
            ('rechazada', 'Rechazada')]
        ,
        string='Respuesta Cliente',
        default='',
        copy=False
    )
    fe_feedback = fields.Text(
        string='Motivo del rechazo',
        copy=False
    )
    fe_company_email_from = fields.Text(
        string='Email de salida para facturación electrónica',
        compute='compute_fe_company_email_from',
        store=False,
        copy=False
    )
    fe_tercero_to_email = fields.Text(
        string='Email del tercero para facturación electrónica',
        compute='compute_fe_tercero_to_email',
        store=False,
        copy=False
    )
    access_token = fields.Char(
        string='Access Token',
        copy=False
    )

    tipo_resolucion = fields.Selection(
        related="company_resolucion_id.tipo",
        string="Tipo de Resolución",
        copy=False
    )

    tipo_resolucion_diario_f = fields.Selection(
        related="journal_id.company_resolucion_factura_id.tipo",
        string="Tipo de Resolución",
        copy=False
    )

    tipo_resolucion_diario_n = fields.Selection(
        related="journal_id.company_resolucion_credito_id.tipo",
        string="Tipo de Resolución",
        copy=False
    )

    estado_dian = fields.Text(
        related="envio_fe_id.respuesta_validacion",
        copy=False
    )

    # Establece por defecto el medio de pago Efectivo
    payment_mean_id = fields.Many2one(
        'l10n_co_cei.payment_mean',
        string='Medio de pago',
        copy=False,
        default=lambda self: self.env['l10n_co_cei.payment_mean'].search([('codigo_fe_dian', '=', '10')], limit=1)
    )

    forma_de_pago = fields.Selection(
        selection = [
            ('1', 'Contado'),
            ('2', 'Crédito'),
        ],
        string='Forma de pago',
        default='1'
    )

    enviada_por_correo = fields.Boolean(
        string='¿Enviada al cliente?',
        copy=False
    )

    concepto_correccion_credito = fields.Selection(
        selection=[
            ('1', 'Devolución de parte de los bienes'),
            ('2', 'Anulación de factura electrónica'),
            ('3', 'Rebaja total aplicada'),
            ('4', 'Descuento total aplicado'),
            ('5', 'Rescisión: Nulidad por falta de requisitos'),
            ('6', 'Otros')
        ],
        string='Concepto de corrección',
        default='2'
    )

    concepto_correccion_debito = fields.Selection(
        selection=[
            ('1', 'Intereses'),
            ('2', 'Gastos por cobrar'),
            ('3', 'Cambio del valor'),
            ('4', 'Otro')
        ]
    )

    es_nota_debito = fields.Boolean(
        string='¿Es una nota débito?'
    )

    credited_invoice_id = fields.Many2one(
        'account.move',
        string='Factura origen',
        copy=False
    )

    es_factura_exportacion = fields.Boolean(
        string='Factura de exportación'
    )

    es_factura_electronica = fields.Boolean(
        string='Es una factura electrónica'
    )

    fe_habilitar_facturacion_related = fields.Boolean(
        string='Habilitar Facturación electrónica',
        compute='compute_fe_habilitar_facturacion_related'
    )
    fe_archivos_email =fields.One2many(
        'l10n_co_cei.fe_archivos_email',
        'invoice_id',
        string='Archivos adjuntos',
        copy=False
    )

    fe_sucursal = fields.Many2one(
        'res.partner',
        string ='Sucursal Facturación',
    )

    company_partner_id = fields.Many2one(
        'res.partner',
        compute='compute_company_partner_id',
        string='Partner ID'
    )

    fe_habilitada_compania = fields.Boolean(
        string='FE Compañía',
        compute='compute_fe_habilitada_compania',
        store=False,
        copy=False
    )

    date_due = fields.Date(string='Fecha límite', related='invoice_date_due')

    @api.depends('invoice_sequence_number_next')
    def compute_fe_habilitada_compania(self):
        for record in self:
            if record.company_id:
                record.fe_habilitada_compania = record.company_id.fe_habilitar_facturacion
            else:
                record.fe_habilitada_compania = self.env.company.fe_habilitar_facturacion

    @api.depends('partner_id')
    def compute_company_partner_id(self):
        for invoice in self:
            invoice.company_partner_id = self.env.company.partner_id

    def compute_fe_habilitar_facturacion_related(self):
        for invoice in self:
            invoice.fe_habilitar_facturacion_related = self.company_id.fe_habilitar_facturacion


    def write(self, values):
        for invoice in self:
            if invoice.es_factura_electronica == True and 'state' in values and values['state'] == 'cancel':
                raise ValidationError(u'No puede cancelar una factura electrónica')
            elif invoice.es_factura_electronica == True and 'state' in values and 'enviada' not in values and values['state'] == 'draft':
                raise ValidationError(u'No puede Pasar a Borrador una factura electrónica')
            else:
                writed = super(Invoice, self).write(values)
                return writed


    def action_generar_nota_debito(self):
        # self.es_nota_debito = True
        invoice_form = self.env.ref('l10n_co_cei.l10n_co_cei_invoice_form', False)
        journal = self.env['account.journal'].search([('categoria', '=', 'nota-debito')], limit=1)

        for invoice in self:
            ctx = dict(
                default_partner_id=invoice.partner_id.id,
                default_es_nota_debito=True,
                default_credited_invoice_id=invoice.id,
                default_journal_id=journal.id,
                default_type='out_invoice',
            )

        return {
            'name': 'Agregar nota débito',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.move',
            'views': [(invoice_form.id, 'form')],
            'view_id': invoice_form.id,
            'target': 'new',
            'context': ctx
        }


    def action_regenerar_xml(self):
        # Permite regenerar XML de la factura en caso de respuesta fallida
        # al validar con la DIAN

        for invoice in self:
            if not self.envio_fe_id or (self.envio_fe_id and self.envio_fe_id.codigo_respuesta_validacion != '00'):

                envio = invoice.env['l10n_co_cei.envio_fe'].search([('id', '=', invoice.envio_fe_id.id)], limit=1)
                envio.unlink()

                moves = self.env['account.move']
                for inv in self:
                    inv.line_ids.filtered(lambda x: x.account_id.reconcile).remove_move_reconcile()

                # First, set the invoices as cancelled and detach the move ids
                invoice.write({'state': 'draft', 'enviada': False})
                if moves:
                    # second, invalidate the move(s)
                    moves.button_draft()
                    # delete the move this invoice was pointing to
                    # Note that the corresponding move_lines and move_reconciles
                    # will be automatically deleted too
                    moves.unlink()

                invoice.write({
                    'filename': None,
                    'firmado': False,
                    'file': None,
                    'zipped_file': None,
                    'nonce': None,
                    'qr_code': None,
                    'cufe': None,
                    'enviada': False,
                    'envio_fe_id': None,
                    'attachment_id': None,
                    'state': 'draft',
                })

                if invoice.type == 'out_invoice':
                    _logger.info('Factura {} regenerada correctamente'.format(invoice.name))
                elif invoice.type == 'out_refund':
                    _logger.info('Nota crédito {} regenerada correctamente'.format(invoice.name))
            else:
                _logger.error('No es posible regenerar el documento {}'.format(invoice.name))
                raise ValidationError('No es posible regenerar el documento {}'.format(invoice.name))

    def compute_fe_tercero_to_email(self):
        for invoice in self:
            config_fe = invoice._get_config()
            if invoice.es_factura_electronica and invoice.fe_habilitar_facturacion_related and invoice.type not in ['in_invoice', 'in_refund'] and invoice.tipo_resolucion_diario_f == 'facturacion-electronica':
                return config_fe.get_value(
                    field_name=ConfigFE.tercero_to_email.name,
                    obj_id=invoice.id
                )
            else:
                return None


    @api.depends('partner_id')
    def compute_fe_company_email_from(self):
        for invoice in self:
            config_fe = invoice._get_config()
            if invoice.es_factura_electronica and invoice.fe_habilitar_facturacion_related and invoice.type not in ['in_invoice', 'in_refund'] and invoice.tipo_resolucion_diario_f == 'facturacion-electronica':
                invoice.fe_company_email_from = str(config_fe.get_value(
                    field_name=ConfigFE.company_email_from.name,
                    obj_id=invoice.id
                ))
            else:
                invoice.fe_company_email_from = None

    def _amount_int_text(self):
        for rec in self:
            dec, cent = amount_to_text_es("{0:.2f}".format(rec.amount_total))
            rec.amount_total_text = dec
            rec.amount_total_text_cent = cent

    def _get_config(self):
        return self.env['l10n_co_cei.config_fe'].search(
            [],
            limit=1
        )

    def _unload_config_data(self):
        global fe_company
        global fe_tercero
        global fe_sucursal_data
        fe_company = None
        fe_tercero = None
        fe_sucursal_data = None


    def _load_config_data(self):
        for invoice in self:
            config_fe = invoice._get_config()
            # config set up
            global fe_company
            global fe_tercero
            global fe_sucursal_data

            if invoice.es_factura_electronica and invoice.fe_habilitar_facturacion_related and invoice.type not in ['in_invoice', 'in_refund'] and invoice.tipo_resolucion_diario_f == 'facturacion-electronica':
                fe_company = {
                    ConfigFE.company_tipo_documento.name: config_fe.get_value(
                        field_name=ConfigFE.company_tipo_documento.name,
                        obj_id=invoice.id
                    ),
                    ConfigFE.company_nit.name: config_fe.get_value(
                        field_name=ConfigFE.company_nit.name,
                        obj_id=invoice.id
                    ),
                    ConfigFE.company_direccion.name: config_fe.get_value(
                        field_name=ConfigFE.company_direccion.name,
                        obj_id=invoice.id
                    ),
                    ConfigFE.company_departamento.name: config_fe.get_value(
                        field_name=ConfigFE.company_departamento.name,
                        obj_id=invoice.id
                    ),
                    ConfigFE.company_ciudad.name: config_fe.get_value(
                        field_name=ConfigFE.company_ciudad.name,
                        obj_id=invoice.id
                    ),
                    ConfigFE.company_tipo_regimen.name: config_fe.get_value(
                        field_name=ConfigFE.company_tipo_regimen.name,
                        obj_id=invoice.id
                    ),
                    ConfigFE.company_digito_verificacion.name: config_fe.get_value(
                        field_name=ConfigFE.company_digito_verificacion.name,
                        obj_id=invoice.id
                    ),
                    ConfigFE.company_telefono.name: config_fe.get_value(
                        field_name=ConfigFE.company_telefono.name,
                        obj_id=invoice.id
                    ),
                    ConfigFE.company_email_from.name: config_fe.get_value(
                        field_name=ConfigFE.company_email_from.name,
                        obj_id=invoice.id
                    ),
                    ConfigFE.company_matricula_mercantil.name: config_fe.get_value(
                        field_name=ConfigFE.company_matricula_mercantil.name,
                        obj_id=invoice.id
                    ),
                    ConfigFE.company_responsabilidad_fiscal.name: config_fe.get_value(
                        field_name=ConfigFE.company_responsabilidad_fiscal.name,
                        obj_id=invoice.id
                    ),
                }
                fe_tercero = {
                    ConfigFE.tercero_es_compania.name: config_fe.get_value(
                        field_name=ConfigFE.tercero_es_compania.name,
                        obj_id=invoice.id
                    ),
                    ConfigFE.tercero_ciudad.name: config_fe.get_value(
                        field_name=ConfigFE.tercero_ciudad.name,
                        obj_id=invoice.id
                    ),
                    ConfigFE.tercero_departamento.name: config_fe.get_value(
                        field_name=ConfigFE.tercero_departamento.name,
                        obj_id=invoice.id
                    ),
                    ConfigFE.tercero_direccion.name: config_fe.get_value(
                        field_name=ConfigFE.tercero_direccion.name,
                        obj_id=invoice.id
                    ),
                    ConfigFE.tercero_razon_social.name: config_fe.get_value(
                        field_name=ConfigFE.tercero_razon_social.name,
                        obj_id=invoice.id,
                        can_be_null=True
                    ),
                    ConfigFE.tercero_primer_apellido.name: config_fe.get_value(
                        field_name=ConfigFE.tercero_primer_apellido.name,
                        obj_id=invoice.id,
                        can_be_null=True
                    ),
                    ConfigFE.tercero_segundo_apellido.name: config_fe.get_value(
                        field_name=ConfigFE.tercero_segundo_apellido.name,
                        obj_id=invoice.id,
                        can_be_null=True
                    ),
                    ConfigFE.tercero_primer_nombre.name: config_fe.get_value(
                        field_name=ConfigFE.tercero_primer_nombre.name,
                        obj_id=invoice.id,
                        can_be_null=True
                    ),
                    ConfigFE.tercero_segundo_nombre.name: config_fe.get_value(
                        field_name=ConfigFE.tercero_segundo_nombre.name,
                        obj_id=invoice.id,
                        can_be_null=True
                    ),
                    ConfigFE.tercero_nit.name: config_fe.get_value(
                        field_name=ConfigFE.tercero_nit.name,
                        obj_id=invoice.id
                    ),
                    ConfigFE.tercero_tipo_documento.name: config_fe.get_value(
                        field_name=ConfigFE.tercero_tipo_documento.name,
                        obj_id=invoice.id
                    ),
                    ConfigFE.tercero_tipo_regimen.name: config_fe.get_value(
                        field_name=ConfigFE.tercero_tipo_regimen.name,
                        obj_id=invoice.id
                    ),
                    ConfigFE.tercero_digito_verificacion.name: config_fe.get_value(
                        field_name=ConfigFE.tercero_digito_verificacion.name,
                        obj_id=invoice.id
                    ),
                    ConfigFE.tercero_telefono.name: config_fe.get_value(
                        field_name=ConfigFE.tercero_telefono.name,
                        obj_id=invoice.id
                    ),
                    ConfigFE.tercero_to_email.name: config_fe.get_value(
                        field_name=ConfigFE.tercero_to_email.name,
                        obj_id=invoice.id
                    ),
                    ConfigFE.tercero_matricula_mercantil.name: config_fe.get_value(
                        field_name=ConfigFE.tercero_matricula_mercantil.name,
                        obj_id=invoice.id
                    ),
                    ConfigFE.tercero_responsabilidad_fiscal.name: config_fe.get_value(
                        field_name=ConfigFE.tercero_responsabilidad_fiscal.name,
                        obj_id=invoice.id
                    ),
                }
                if invoice.fe_sucursal:
                    fe_sucursal_data = {
                        ConfigFE.sucursal_ciudad.name: config_fe.get_value(
                            field_name=ConfigFE.sucursal_ciudad.name,
                            obj_id=invoice.id
                        ),
                        ConfigFE.sucursal_departamento.name: config_fe.get_value(
                            field_name=ConfigFE.sucursal_departamento.name,
                            obj_id=invoice.id
                        ),
                        ConfigFE.sucursal_direccion.name: config_fe.get_value(
                            field_name=ConfigFE.sucursal_direccion.name,
                            obj_id=invoice.id
                        ),
                        ConfigFE.sucursal_telefono.name: config_fe.get_value(
                            field_name=ConfigFE.sucursal_telefono.name,
                            obj_id=invoice.id
                        ),
                        ConfigFE.sucursal_to_email.name: config_fe.get_value(
                            field_name=ConfigFE.sucursal_to_email.name,
                            obj_id=invoice.id
                        ),
                    }

    def compute_fe_company_nit(self):
        for invoice in self:
            config_fe = invoice._get_config()
            if invoice.es_factura_electronica and invoice.fe_habilitar_facturacion_related  and invoice.type not in ['in_invoice', 'in_refund'] and invoice.tipo_resolucion_diario_f == 'facturacion-electronica':
                return config_fe.get_value(
                    field_name=ConfigFE.company_nit.name,
                    obj_id=invoice.id
                )
            else:
                return None


    def compute_fe_company_digito_verificacion(self):
        for invoice in self:
            config_fe = invoice._get_config()
            if invoice.es_factura_electronica and invoice.fe_habilitar_facturacion_related and invoice.type not in ['in_invoice', 'in_refund'] and invoice.tipo_resolucion_diario_f == 'facturacion-electronica':
                return config_fe.get_value(
                    field_name=ConfigFE.company_digito_verificacion.name,
                    obj_id=invoice.id
                )
            else:
                return None


    def compute_fe_tercero_nit(self):
        for invoice in self:
            config_fe = invoice._get_config()
            if invoice.es_factura_electronica and invoice.fe_habilitar_facturacion_related and invoice.type not in ['in_invoice', 'in_refund'] and invoice.tipo_resolucion_diario_f == 'facturacion-electronica':
                return config_fe.get_value(
                    field_name=ConfigFE.tercero_nit.name,
                    obj_id=invoice.id
                )
            else:
                return None

    def _get_fe_filename(self):
        try:
            for invoice in self:
                if invoice.filename:
                    return invoice.filename

                nit = str(fe_company[ConfigFE.company_nit.name]).zfill(10)
                current_year = datetime.datetime.now().replace(tzinfo=pytz.timezone('America/Bogota')).strftime('%Y')

        except Exception as e:
            _logger.error('[!] por favor valide el numero de documento y tipo de documento del cliente y la compañia en el modulo de contactos para la factura {} - Excepción: {}'.format(self.invoice_payment_ref, e))
            raise ValidationError('[!] por favor valide el numero de documento y tipo de documento del cliente y la compañia en el modulo de contactos para la factura {} - Excepción: {}'.format(self.invoice_payment_ref, e))

        try:
            # TODO: Migrar a Odoo 9, 10 y 11
            # Multicompañía habilitado de forma experimental
            if invoice.type == 'out_invoice' and not invoice.es_nota_debito:
                # sequence = self.env.ref('l10n_co_cei.dian_invoice_sequence', False)
                sequence = self.env['ir.sequence'].search([
                    ('company_id', '=', invoice.company_id.id), ('fe_tipo_secuencia', '=', 'facturas-venta')], limit=1)
            elif invoice.type == 'out_refund':
                # sequence = self.env.ref('l10n_co_cei.dian_credit_note_sequence', False)
                sequence = self.env['ir.sequence'].search([
                    ('company_id', '=', invoice.company_id.id), ('fe_tipo_secuencia', '=', 'notas-credito')], limit=1)
            else:
                # sequence = self.env.ref('l10n_co_cei.dian_debit_note_sequence', False)
                sequence = self.env['ir.sequence'].search([
                    ('company_id', '=', invoice.company_id.id), ('fe_tipo_secuencia', '=', 'notas-debito')], limit=1)

            if self.tipo_resolucion_diario_f == 'facturacion-electronica' or self.tipo_resolucion_diario_n == 'facturacion-electronica':
                sequence_year = invoice._str_to_datetime(sequence.write_date).replace(tzinfo=pytz.timezone('America/Bogota')).strftime('%Y')

            if invoice.type == 'out_invoice' and not invoice.es_nota_debito:
                filename = 'fv{}000{}{}'.format(nit, current_year[-2:], str(sequence.number_next_actual).zfill(8))
            elif invoice.type == 'out_refund':
                filename = 'nc{}000{}{}'.format(nit, current_year[-2:], str(sequence.number_next_actual).zfill(8))
            else:
                filename = 'nd{}000{}{}'.format(nit, current_year[-2:], str(sequence.number_next_actual).zfill(8))

            return filename

        except Exception as e:
            _logger.error('[!] por favor valide las configuraciones de la secuencia, diario y resolucion para el documento {} - Excepción: {}'.format(self.invoice_payment_ref, e))
            raise ValidationError('[!] por favor valide las configuraciones de la secuencia, diario y resolucion para el documento {} - Excepción: {}'.format(self.invoice_payment_ref, e))

    # genera xml de facturacion electronica

    def generar_factura_electronica(self):
        if len(self) != 1:
            raise ValidationError(
                "Esta opción solo debe ser usada por ID individual a la vez."
            )
        for invoice in self:
            if (invoice.type == 'out_invoice' and
                    not invoice.company_resolucion_id.tipo == 'facturacion-electronica'):
                raise ValidationError(
                    "Esta función es solo para facturación electrónica."
                )
            if invoice.file:
                raise ValidationError(
                    "La factura electrónica ya fue generada."
                )

            if invoice.type == 'out_invoice' and not invoice.company_resolucion_id:
                raise ValidationError(
                    "La factura no está vinculada a una resolución."
                )
            if not invoice.file:
                output = ''
                if invoice.type == 'out_invoice':
                    if invoice.es_nota_debito:
                        output = invoice.generar_creditnote_xml()
                        _logger.info('Nota débito {} generada'.format(invoice.name))
                    else:
                        output = invoice.generar_invoice_xml()
                        _logger.info('Factura {} generada'.format(invoice.name))
                elif invoice.type == 'out_refund':
                    output = invoice.generar_creditnote_xml()
                    _logger.info('Nota crédito {} generada'.format(invoice.name))

                invoice.sudo().write({
                    'file': base64.b64encode(output.encode())
                })

    def prefix_invoice_number(self):
        for invoice in self:
            if invoice.type == 'out_invoice':
                prefijo = invoice.company_resolucion_id.prefijo
                return (prefijo if prefijo else '') + invoice.name
            else:  # Necesario para evitar errores cuando se le asigna prefijo a secuencia de nota cŕedito.
                if invoice.company_resolucion_id.journal_id.refund_sequence_id:
                    return invoice.name
                else:
                    prefijo = invoice.company_resolucion_id.prefijo
                    return (prefijo if prefijo else '') + invoice.name

    def _tipo_de_documento(self, tipo_de_documento):
        return str(tipo_de_documento)

    @staticmethod
    def _str_to_datetime(date):
        date = date.replace(tzinfo=pytz.timezone('UTC'))
        return date

    def calcular_cufe(self, tax_total_values):

        create_date = self._str_to_datetime(self.create_date)
        tax_computed_values = {tax: value['total'] for tax, value in tax_total_values.items()}

        numfac = self.prefix_invoice_number()
        fecfac = create_date.astimezone(pytz.timezone('America/Bogota')).strftime('%Y-%m-%d')
        horfac = create_date.astimezone(pytz.timezone('America/Bogota')).strftime('%H:%M:%S-05:00')
        valfac = '{:.2f}'.format(self.amount_untaxed)
        codimp1 = '01'
        valimp1 = '{:.2f}'.format(tax_computed_values.get('01', 0))
        codimp2 = '04'
        valimp2 = '{:.2f}'.format(tax_computed_values.get('04', 0))
        codimp3 = '03'
        valimp3 = '{:.2f}'.format(tax_computed_values.get('03', 0))
        valtot = '{:.2f}'.format(self.amount_total)
        nitofe = fe_company[ConfigFE.company_nit.name]
        if self.company_id.fe_tipo_ambiente != '3':
            tipoambiente = self.company_id.fe_tipo_ambiente
        else:
            tipoambiente = '2'
        numadq = fe_tercero[ConfigFE.tercero_nit.name]

        if self.type == 'out_invoice' and not self.es_nota_debito:
            citec = self.company_resolucion_id.clave_tecnica
        else:
            citec = self.company_id.fe_software_pin

        total_otros_impuestos = sum([value for key, value in tax_computed_values.items() if key != '01'])
        iva = tax_computed_values.get('01', '0.00')

        cufe = (
                numfac + fecfac + horfac + valfac + codimp1 + valimp1 + codimp2 +
                valimp2 + codimp3 + valimp3 + valtot + nitofe + numadq + citec +
                tipoambiente
        )
        cufe_seed = cufe

        sha384 = hashlib.sha384()
        sha384.update(cufe.encode())
        cufe = sha384.hexdigest()

        qr_code = 'NumFac: {}\n' \
                  'FecFac: {}\n' \
                  'HorFac: {}\n' \
                  'NitFac: {}\n' \
                  'DocAdq: {}\n' \
                  'ValFac: {}\n' \
                  'ValIva: {}\n' \
                  'ValOtroIm: {:.2f}\n' \
                  'ValFacIm: {}\n' \
                  'CUFE: {}'.format(
                    numfac,
                    fecfac,
                    horfac,
                    nitofe,
                    numadq,
                    valfac,
                    iva,
                    total_otros_impuestos,
                    valtot,
                    cufe
                    )

        qr = pyqrcode.create(qr_code, error='L')

        self.write({
            'cufe_seed': cufe_seed,
            'cufe': cufe,
            'qr_code': qr.png_as_base64_str(scale=2)
        })

        return self.cufe

    def get_template_str(self, relative_file_path):
        template_file = os.path.realpath(
            os.path.join(
                os.getcwd(),
                os.path.dirname(__file__),
                relative_file_path
            )
        )

        f = open(template_file, 'rU')
        # xml_template = f.read().decode('utf-8')
        xml_template = f.read()
        f.close()

        return xml_template

    def generar_invoice_xml(self):
        try:
            invoice = self
            create_date = self._str_to_datetime(self.create_date)

            key_data = '{}{}{}'.format(
                invoice.company_id.fe_software_id, invoice.company_id.fe_software_pin, invoice.prefix_invoice_number()
            )
            sha384 = hashlib.sha384()
            sha384.update(key_data.encode())
            software_security_code = sha384.hexdigest()

            invoice_lines = []

            tax_exclusive_amount = 0
            tax_total_values = {}

            # Bloque de código para imitar la estructura requerida por el XML de la DIAN para los totales externos
            # a las líneas de la factura.
            for line_id in self.invoice_line_ids:
                for tax in line_id.tax_ids:

                    # Inicializa contador a cero para cada ID de impuesto
                    if tax.codigo_fe_dian not in tax_total_values:
                        tax_total_values[tax.codigo_fe_dian] = dict()
                        tax_total_values[tax.codigo_fe_dian]['total'] = 0
                        tax_total_values[tax.codigo_fe_dian]['info'] = dict()

                    # Suma al total de cada código, y añade información por cada tarifa.
                    if tax.amount not in tax_total_values[tax.codigo_fe_dian]['info']:

                        aux_total = tax_total_values[tax.codigo_fe_dian]['total']
                        aux_total = aux_total + line_id.price_subtotal * tax['amount'] / 100
                        aux_total = round(aux_total, 2)
                        tax_total_values[tax.codigo_fe_dian]['total'] = aux_total

                        tax_total_values[tax.codigo_fe_dian]['info'][tax.amount] = {
                            'taxable_amount': line_id.price_subtotal,
                            'value': round(line_id.price_subtotal * tax['amount'] / 100, 2),
                            'technical_name': tax.nombre_tecnico_dian
                        }
                    else:
                        aux_tax = tax_total_values[tax.codigo_fe_dian]['info'][tax.amount]['value']
                        aux_total = tax_total_values[tax.codigo_fe_dian]['total']
                        aux_taxable = tax_total_values[tax.codigo_fe_dian]['info'][tax.amount]['taxable_amount']
                        aux_tax = aux_tax + line_id.price_subtotal * tax['amount'] / 100
                        aux_total = aux_total + line_id.price_subtotal * tax['amount'] / 100
                        aux_taxable = aux_taxable + line_id.price_subtotal
                        aux_tax = round(aux_tax, 2)
                        aux_total = round(aux_total, 2)
                        aux_taxable = round(aux_taxable, 2)
                        tax_total_values[tax.codigo_fe_dian]['info'][tax.amount]['value'] = aux_tax
                        tax_total_values[tax.codigo_fe_dian]['total'] = aux_total
                        tax_total_values[tax.codigo_fe_dian]['info'][tax.amount]['taxable_amount'] = aux_taxable

            for index, invoice_line_id in enumerate(self.invoice_line_ids):
                taxes = invoice_line_id.tax_ids
                tax_values = [invoice_line_id.price_subtotal * tax['amount'] / 100 for tax in taxes]
                tax_values = [round(value, 2) for value in tax_values]
                tax_info = dict()

                for tax in invoice_line_id.tax_ids:
                    # Inicializa contador a cero para cada ID de impuesto
                    if tax.codigo_fe_dian not in tax_info:
                        tax_info[tax.codigo_fe_dian] = dict()
                        tax_info[tax.codigo_fe_dian]['total'] = 0
                        tax_info[tax.codigo_fe_dian]['info'] = dict()

                    # Suma al total de cada código, y añade información por cada tarifa para cada línea.
                    if tax.amount not in tax_info[tax.codigo_fe_dian]['info']:

                        aux_total = tax_info[tax.codigo_fe_dian]['total']
                        aux_total = aux_total + invoice_line_id.price_subtotal * tax['amount'] / 100
                        aux_total = round(aux_total, 2)
                        tax_info[tax.codigo_fe_dian]['total'] = aux_total

                        tax_info[tax.codigo_fe_dian]['info'][tax.amount] = {
                            'taxable_amount': invoice_line_id.price_subtotal,
                            'value': round(invoice_line_id.price_subtotal * tax['amount'] / 100, 2),
                            'technical_name': tax.nombre_tecnico_dian
                        }
                    else:
                        aux_tax = tax_info[tax.codigo_fe_dian]['info'][tax.amount]['value']
                        aux_total = tax_info[tax.codigo_fe_dian]['total']
                        aux_taxable = tax_total_values[tax.codigo_fe_dian]['info'][tax.amount]['taxable_amount']
                        aux_tax = aux_tax + invoice_line_id.price_subtotal * tax['amount'] / 100
                        aux_total = aux_total + invoice_line_id.price_subtotal * tax['amount'] / 100
                        aux_taxable = aux_taxable + invoice_line_id.price_subtotal
                        aux_tax = round(aux_tax, 2)
                        aux_total = round(aux_total, 2)
                        aux_taxable = round(aux_taxable, 2)
                        tax_info[tax.codigo_fe_dian]['info'][tax.amount]['value'] = aux_tax
                        tax_info[tax.codigo_fe_dian]['total'] = aux_total
                        tax_info[tax.codigo_fe_dian]['info'][tax.amount]['taxable_amount'] = aux_taxable

                invoice_lines.append({
                    'id': index + 1,
                    'invoiced_quantity': invoice_line_id.quantity,
                    'line_extension_amount': invoice_line_id.price_subtotal,
                    'item_description': saxutils.escape(invoice_line_id.name),
                    'price': invoice_line_id.price_subtotal/invoice_line_id.quantity,
                    'total_amount_tax': invoice.amount_tax,
                    'tax_info': tax_info,
                })

                if invoice_line_id.tax_ids.ids:
                    # si existe tax para una linea, entonces el price_subtotal
                    # de la linea se incluye en tax_exclusive_amount
                    tax_exclusive_amount += invoice_line_id.price_subtotal

            invoice_fe_data = {
                'invoice_authorization': invoice.company_resolucion_id.number,
                'start_date': invoice.company_resolucion_id.fecha_inicial,
                'end_date': invoice.company_resolucion_id.fecha_final,
                'invoice_prefix': (
                    invoice.company_resolucion_id.prefijo
                    if invoice.company_resolucion_id.prefijo
                    else ''
                ),
                'authorization_from': self.company_resolucion_id.rango_desde,
                'authorization_to': self.company_resolucion_id.rango_hasta,
                'provider_id': fe_company[ConfigFE.company_nit.name],
                'software_id': self.company_id.fe_software_id,
                'software_security_code': software_security_code,
                'invoice_number': self.prefix_invoice_number(),
                'invoice_cufe': invoice.calcular_cufe(tax_total_values),
                'invoice_issue_date': create_date.astimezone(pytz.timezone("America/Bogota")).strftime('%Y-%m-%d'),
                'invoice_issue_time': create_date.astimezone(pytz.timezone("America/Bogota")).strftime('%H:%M:%S-05:00'),
                'invoice_note': self.narration or '',
                # supplier
                'invoice_supplier_additional_account_id': self.company_id.partner_id.fe_es_compania,
                'invoice_supplier_document_type': self._tipo_de_documento(fe_company[ConfigFE.company_tipo_documento.name]),
                'invoice_supplier_identification': fe_company[ConfigFE.company_nit.name],
                'invoice_supplier_identification_digit': fe_company[ConfigFE.company_digito_verificacion.name],
                'invoice_supplier_party_name': saxutils.escape(invoice.company_id.name),
                'invoice_supplier_department': fe_company[ConfigFE.company_departamento.name].name
                    if not self.fe_sucursal
                    else fe_sucursal_data[ConfigFE.sucursal_departamento.name].name,
                'invoice_supplier_department_code': fe_company[ConfigFE.company_departamento.name].state_code
                    if not self.fe_sucursal
                    else fe_sucursal_data[ConfigFE.sucursal_departamento.name].state_code,
                'invoice_supplier_city': self.calcular_ciudad(fe_company[ConfigFE.company_ciudad.name])
                    if not self.fe_sucursal
                    else self.calcular_ciudad(fe_sucursal_data[ConfigFE.sucursal_ciudad.name]),
                'invoice_supplier_city_code': self.calcular_codigo_ciudad(fe_company[ConfigFE.company_ciudad.name])
                    if not self.fe_sucursal
                    else self.calcular_codigo_ciudad(fe_sucursal_data[ConfigFE.sucursal_ciudad.name]),
                'invoice_supplier_address_line': fe_company[ConfigFE.company_direccion.name]
                    if not self.fe_sucursal
                    else fe_sucursal_data[ConfigFE.sucursal_direccion.name],
                'invoice_supplier_tax_level_code': fe_company[ConfigFE.company_responsabilidad_fiscal.name],
                'invoice_supplier_country_code': self.company_id.partner_id.country_id.code
                    if not self.fe_sucursal
                    else self.env.user.fe_sucursal.country_id.code,
                'invoice_supplier_commercial_registration':
                    fe_company[ConfigFE.company_matricula_mercantil.name]
                    if fe_company[ConfigFE.company_matricula_mercantil.name]
                    else 0,
                'invoice_supplier_phone': fe_company[ConfigFE.company_telefono.name]
                    if not self.fe_sucursal
                    else fe_sucursal_data[ConfigFE.sucursal_telefono.name],
                'invoice_supplier_email': fe_company[ConfigFE.company_email_from.name]
                    if not self.fe_sucursal
                    else fe_sucursal_data[ConfigFE.sucursal_to_email.name],
                # customer
                'invoice_customer_additional_account_id': fe_tercero[ConfigFE.tercero_es_compania.name],
                'invoice_customer_document_type': self._tipo_de_documento(fe_tercero[ConfigFE.tercero_tipo_documento.name]),
                'invoice_customer_identification': fe_tercero[ConfigFE.tercero_nit.name],
                'invoice_customer_identification_digit': fe_tercero[ConfigFE.tercero_digito_verificacion.name],
                'invoice_customer_party_name': saxutils.escape(invoice.partner_id.name),
                'invoice_customer_department': fe_tercero[ConfigFE.tercero_departamento.name].name,
                'invoice_customer_department_code': fe_tercero[ConfigFE.tercero_departamento.name].state_code,
                'invoice_customer_city': self.calcular_ciudad(fe_tercero[ConfigFE.tercero_ciudad.name]),
                'invoice_customer_city_code': self.calcular_codigo_ciudad(fe_tercero[ConfigFE.tercero_ciudad.name]),
                'invoice_customer_address_line': fe_tercero[ConfigFE.tercero_direccion.name],
                'invoice_customer_country': self.partner_id.country_id.iso_name,
                'invoice_customer_country_code': self.partner_id.country_id.code,
                'invoice_customer_first_name': fe_tercero[ConfigFE.tercero_primer_nombre.name],
                'invoice_customer_family_name': fe_tercero[ConfigFE.tercero_primer_apellido.name],
                'invoice_customer_family_last_name':
                    fe_tercero[ConfigFE.tercero_segundo_apellido.name]
                    if fe_tercero[ConfigFE.tercero_segundo_apellido.name]
                    else ' ',
                'invoice_customer_middle_name':
                    fe_tercero[ConfigFE.tercero_segundo_nombre.name]
                    if fe_tercero[ConfigFE.tercero_segundo_nombre.name]
                    else ' ',
                'invoice_customer_phone': fe_tercero[ConfigFE.tercero_telefono.name],
                'invoice_customer_commercial_registration':
                    fe_tercero[ConfigFE.tercero_matricula_mercantil.name]
                    if fe_tercero[ConfigFE.tercero_matricula_mercantil.name]
                    else 0,
                'invoice_customer_email': fe_tercero[ConfigFE.tercero_to_email.name],
                'invoice_customer_tax_level_code': fe_tercero[ConfigFE.tercero_responsabilidad_fiscal.name],
                # legal monetary total
                'line_extension_amount': '{:.2f}'.format(invoice.amount_untaxed),
                'tax_exclusive_amount': '{:.2f}'.format(tax_exclusive_amount),
                'payable_amount': '{:.2f}'.format(invoice.amount_total),
                # invoice lines
                'invoice_lines': invoice_lines,
                'tax_total': tax_values,
                'tax_total_values': tax_total_values,
                'date_due': invoice.date_due,
                # Info validación previa
                'payment_means_id': self.forma_de_pago,
                'payment_means_code': self.payment_mean_id.codigo_fe_dian,
                'payment_id': self.payment_mean_id.nombre_tecnico_dian,
                'reference_event_code': self.invoice_payment_term_id.codigo_fe_dian,
                'duration_measure': self.invoice_payment_term_id.line_ids[0].days,
                'profile_execution_id': self.company_id.fe_tipo_ambiente if self.company_id.fe_tipo_ambiente != '3' else '2'
            }

            if fe_tercero[ConfigFE.tercero_es_compania.name] == '1':
                invoice_fe_data['invoice_registration_name'] = fe_tercero[ConfigFE.tercero_razon_social.name]
            elif fe_tercero[ConfigFE.tercero_es_compania.name] == '2':
                invoice_fe_data['invoice_customer_is_company'] = fe_tercero[ConfigFE.tercero_es_compania.name]

            if self.es_factura_exportacion:
                invoice_fe_data['currency_id'] = self.currency_id.name
                invoice_fe_data['calculation_rate'] = round(1/self.currency_id.rate, 2)
                invoice_fe_data['rate_date'] = self.currency_id.date
                invoice_fe_data['invoice_customer_country'] = self.partner_id.country_id.iso_name
                invoice_fe_data['invoice_incoterm_code'] = self.invoice_incoterm_id.code
                invoice_fe_data['invoice_incoterm_description'] = self.invoice_incoterm_id.name
                xml_template = self.get_template_str('../templates/export.xml')
                export_template = Template(xml_template)
                output = export_template.render(invoice_fe_data)
            else:
                xml_template = self.get_template_str('../templates/invoice.xml')
                invoice_template = Template(xml_template)
                output = invoice_template.render(invoice_fe_data)

            return output
        except Exception as e:
            raise ValidationError(
                "Error validando la factura : {}".format(e)
            )

    def calcular_ciudad(self, objeto):
        return objeto.city_name

    def calcular_codigo_ciudad(self, objeto):
        return objeto.city_code

    def generar_creditnote_xml(self):
        create_date = self._str_to_datetime(self.create_date)
        invoice = self

        key_data = '{}{}{}'.format(
            invoice.company_id.fe_software_id, invoice.company_id.fe_software_pin, invoice.prefix_invoice_number()
        )
        sha384 = hashlib.sha384()
        sha384.update(key_data.encode())
        software_security_code = sha384.hexdigest()

        creditnote_lines = []

        tax_exclusive_amount = 0
        tax_total_values = {}

        # Bloque de código para imitar la estructura requerida por el XML de la DIAN para los totales externos
        # a las líneas de la factura.
        for line_id in self.invoice_line_ids:
            for tax in line_id.tax_ids:

                # Inicializa contador a cero para cada ID de impuesto
                if tax.codigo_fe_dian not in tax_total_values:
                    tax_total_values[tax.codigo_fe_dian] = dict()
                    tax_total_values[tax.codigo_fe_dian]['total'] = 0
                    tax_total_values[tax.codigo_fe_dian]['info'] = dict()

                # Suma al total de cada código, y añade información por cada tarifa.
                if tax.amount not in tax_total_values[tax.codigo_fe_dian]['info']:

                    aux_total = tax_total_values[tax.codigo_fe_dian]['total']
                    aux_total = aux_total + line_id.price_subtotal * tax['amount'] / 100
                    aux_total = round(aux_total, 2)
                    tax_total_values[tax.codigo_fe_dian]['total'] = aux_total

                    tax_total_values[tax.codigo_fe_dian]['info'][tax.amount] = {
                        'taxable_amount': line_id.price_subtotal,
                        'value': round(line_id.price_subtotal * tax['amount'] / 100, 2),
                        'technical_name': tax.nombre_tecnico_dian
                    }
                else:
                    aux_tax = tax_total_values[tax.codigo_fe_dian]['info'][tax.amount]['value']
                    aux_total = tax_total_values[tax.codigo_fe_dian]['total']
                    aux_taxable = tax_total_values[tax.codigo_fe_dian]['info'][tax.amount]['taxable_amount']
                    aux_tax = aux_tax + line_id.price_subtotal * tax['amount'] / 100
                    aux_total = aux_total + line_id.price_subtotal * tax['amount'] / 100
                    aux_taxable = aux_taxable + line_id.price_subtotal
                    aux_tax = round(aux_tax, 2)
                    aux_total = round(aux_total, 2)
                    aux_taxable = round(aux_taxable, 2)
                    tax_total_values[tax.codigo_fe_dian]['info'][tax.amount]['value'] = aux_tax
                    tax_total_values[tax.codigo_fe_dian]['total'] = aux_total
                    tax_total_values[tax.codigo_fe_dian]['info'][tax.amount]['taxable_amount'] = aux_taxable

        for index, invoice_line_id in enumerate(self.invoice_line_ids):
            taxes = invoice_line_id.tax_ids
            tax_values = [invoice_line_id.price_subtotal * tax['amount'] / 100 for tax in taxes]
            tax_values = [round(value, 2) for value in tax_values]
            tax_info = dict()

            for tax in invoice_line_id.tax_ids:
                # Inicializa contador a cero para cada ID de impuesto
                if tax.codigo_fe_dian not in tax_info:
                    tax_info[tax.codigo_fe_dian] = dict()
                    tax_info[tax.codigo_fe_dian]['total'] = 0
                    tax_info[tax.codigo_fe_dian]['info'] = dict()

                # Suma al total de cada código, y añade información por cada tarifa para cada línea.
                if tax.amount not in tax_info[tax.codigo_fe_dian]['info']:

                    aux_total = tax_info[tax.codigo_fe_dian]['total']
                    aux_total = aux_total + invoice_line_id.price_subtotal * tax['amount'] / 100
                    aux_total = round(aux_total, 2)
                    tax_info[tax.codigo_fe_dian]['total'] = aux_total

                    tax_info[tax.codigo_fe_dian]['info'][tax.amount] = {
                        'taxable_amount': invoice_line_id.price_subtotal,
                        'value': round(invoice_line_id.price_subtotal * tax['amount'] / 100, 2),
                        'technical_name': tax.nombre_tecnico_dian
                    }
                else:
                    aux_tax = tax_info[tax.codigo_fe_dian]['info'][tax.amount]['value']
                    aux_total = tax_info[tax.codigo_fe_dian]['total']
                    aux_taxable = tax_info[tax.codigo_fe_dian]['info'][tax.amount]['taxable_amount']
                    aux_tax = aux_tax + invoice_line_id.price_subtotal * tax['amount'] / 100
                    aux_total = aux_total + invoice_line_id.price_subtotal * tax['amount'] / 100
                    aux_taxable = aux_taxable + invoice_line_id.price_subtotal
                    aux_tax = round(aux_tax, 2)
                    aux_total = round(aux_total, 2)
                    aux_taxable = round(aux_taxable, 2)
                    tax_info[tax.codigo_fe_dian]['info'][tax.amount]['value'] = aux_tax
                    tax_info[tax.codigo_fe_dian]['total'] = aux_total
                    tax_info[tax.codigo_fe_dian]['info'][tax.amount]['taxable_amount'] = aux_taxable

            creditnote_lines.append({
                'id': index + 1,
                'credited_quantity': invoice_line_id.quantity,
                'line_extension_amount': invoice_line_id.price_subtotal,
                'item_description': saxutils.escape(invoice_line_id.name),
                'price': invoice_line_id.price_subtotal/invoice_line_id.quantity,
                'total_amount_tax': invoice.amount_tax,
                'tax_info': tax_info,
            })

            if invoice_line_id.tax_ids.ids:
                # si existe tax para una linea, entonces el price_subtotal
                # de la linea se incluye en tax_exclusive_amount
                tax_exclusive_amount += invoice_line_id.price_subtotal

        creditnote_fe_data = {
            'provider_id': fe_company[ConfigFE.company_nit.name],
            'software_id': self.company_id.fe_software_id,
            'software_security_code': software_security_code,
            'invoice_number': self.prefix_invoice_number(),
            'creditnote_cufe': self.calcular_cufe(tax_total_values),
            'invoice_issue_date': create_date.astimezone(pytz.timezone("America/Bogota")).strftime('%Y-%m-%d'),
            'invoice_issue_time': create_date.astimezone(pytz.timezone("America/Bogota")).strftime('%H:%M:%S-05:00'),
            'invoice_note': invoice.name if invoice.name else '',
            'credit_note_reason': invoice.reversed_entry_id.narration or '',
            'billing_issue_date': create_date.astimezone(pytz.timezone("America/Bogota")).strftime('%Y-%m-%d'),
            # supplier
            'invoice_supplier_additional_account_id': self.company_id.partner_id.fe_es_compania,
            'invoice_supplier_document_type': self._tipo_de_documento(fe_company[ConfigFE.company_tipo_documento.name]),
            'invoice_supplier_identification': fe_company[ConfigFE.company_nit.name],
            'invoice_supplier_identification_digit': fe_company[ConfigFE.company_digito_verificacion.name],
            'invoice_supplier_party_name': saxutils.escape(invoice.company_id.name),
            'invoice_supplier_department': fe_company[ConfigFE.company_departamento.name].name
                if not self.fe_sucursal
                else fe_sucursal_data[ConfigFE.sucursal_departamento.name].name,
            'invoice_supplier_department_code': fe_company[ConfigFE.company_departamento.name].state_code
                if not self.fe_sucursal
                else fe_sucursal_data[ConfigFE.sucursal_departamento.name].state_code,
            'invoice_supplier_city': self.calcular_ciudad(fe_company[ConfigFE.company_ciudad.name])
                if not self.fe_sucursal
                else self.calcular_ciudad(fe_sucursal_data[ConfigFE.sucursal_ciudad.name]),
            'invoice_supplier_city_code': self.calcular_codigo_ciudad(fe_company[ConfigFE.company_ciudad.name])
                if not self.fe_sucursal
                else self.calcular_codigo_ciudad(fe_sucursal_data[ConfigFE.sucursal_ciudad.name]),
            'invoice_supplier_address_line': fe_company[ConfigFE.company_direccion.name]
                if not self.fe_sucursal
                else fe_sucursal_data[ConfigFE.sucursal_direccion.name],
            'invoice_supplier_tax_level_code': fe_company[ConfigFE.company_responsabilidad_fiscal.name],
            'invoice_supplier_country_code': self.company_id.partner_id.country_id.code
                if not self.fe_sucursal
                else self.env.user.fe_sucursal.country_id.code,
            'invoice_supplier_commercial_registration':
                fe_company[ConfigFE.company_matricula_mercantil.name]
                if fe_company[ConfigFE.company_matricula_mercantil.name]
                else 0,
            'invoice_supplier_phone': fe_company[ConfigFE.company_telefono.name]
                if not self.fe_sucursal
                else fe_sucursal_data[ConfigFE.sucursal_telefono.name],
            'invoice_supplier_email': fe_company[ConfigFE.company_email_from.name]
                if not self.fe_sucursal
                else fe_sucursal_data[ConfigFE.sucursal_to_email.name],
            # customer
            'invoice_customer_additional_account_id': fe_tercero[ConfigFE.tercero_es_compania.name],
            'invoice_customer_document_type': self._tipo_de_documento(fe_tercero[ConfigFE.tercero_tipo_documento.name]),
            'invoice_customer_identification': fe_tercero[ConfigFE.tercero_nit.name],
            'invoice_customer_identification_digit': fe_tercero[ConfigFE.tercero_digito_verificacion.name],
            'invoice_customer_party_name': saxutils.escape(invoice.partner_id.name),
            'invoice_customer_department': fe_tercero[ConfigFE.tercero_departamento.name].name,
            'invoice_customer_department_code': fe_tercero[ConfigFE.tercero_departamento.name].state_code,
            'invoice_customer_city': self.calcular_ciudad(fe_tercero[ConfigFE.tercero_ciudad.name]),
            'invoice_customer_city_code': self.calcular_codigo_ciudad(fe_tercero[ConfigFE.tercero_ciudad.name]),
            'invoice_customer_address_line': fe_tercero[ConfigFE.tercero_direccion.name],
            'invoice_customer_country': self.partner_id.country_id.iso_name,
            'invoice_customer_country_code': self.partner_id.country_id.code,
            'invoice_customer_tax_level_code': fe_tercero[ConfigFE.tercero_responsabilidad_fiscal.name],
            'invoice_customer_first_name': fe_tercero[ConfigFE.tercero_primer_nombre.name],
            'invoice_customer_family_name': fe_tercero[ConfigFE.tercero_primer_apellido.name],
            'invoice_customer_family_last_name':
                fe_tercero[ConfigFE.tercero_segundo_apellido.name]
                if fe_tercero[ConfigFE.tercero_segundo_apellido.name]
                else ' ',
            'invoice_customer_middle_name':
                fe_tercero[ConfigFE.tercero_segundo_nombre.name]
                if fe_tercero[ConfigFE.tercero_segundo_nombre.name]
                else ' ',
            'invoice_customer_phone': fe_tercero[ConfigFE.tercero_telefono.name],
            'invoice_customer_commercial_registration':
                fe_tercero[ConfigFE.tercero_matricula_mercantil.name]
                if fe_tercero[ConfigFE.tercero_matricula_mercantil.name]
                else 0,
            'invoice_customer_email': fe_tercero[ConfigFE.tercero_to_email.name],
            # legal monetary total
            'line_extension_amount': '{:.2f}'.format(invoice.amount_untaxed),
            'tax_exclusive_amount': '{:.2f}'.format(tax_exclusive_amount),
            'payable_amount': '{:.2f}'.format(invoice.amount_total),
            # invoice lines
            'creditnote_lines': creditnote_lines,
            'tax_total': tax_values,
            'tax_total_values': tax_total_values,
            'date_due': invoice.date_due,
            # Info validación previa
            'payment_means_id': self.forma_de_pago,
            'payment_means_code': self.payment_mean_id.codigo_fe_dian,
            'payment_id': self.payment_mean_id.nombre_tecnico_dian,
            'reference_event_code': self.invoice_payment_term_id.codigo_fe_dian,
            'duration_measure': self.invoice_payment_term_id.line_ids[0].days,
            'profile_execution_id': self.company_id.fe_tipo_ambiente if self.company_id.fe_tipo_ambiente != '3' else '2'
        }

        if fe_tercero[ConfigFE.tercero_es_compania.name] == '1':
            creditnote_fe_data['invoice_registration_name'] = fe_tercero[ConfigFE.tercero_razon_social.name]
        elif fe_tercero[ConfigFE.tercero_es_compania.name] == '2':
            creditnote_fe_data['invoice_customer_is_company'] = fe_tercero[ConfigFE.tercero_es_compania.name]

        if self.es_nota_debito:
            creditnote_fe_data['discrepancy_response_code'] = self.concepto_correccion_debito
            creditnote_fe_data['billing_reference_id'] = self.credited_invoice_id.prefix_invoice_number()
            creditnote_fe_data['billing_reference_cufe'] = self.credited_invoice_id.cufe
            creditnote_fe_data['billing_reference_issue_date'] = self._str_to_datetime(self.create_date).strftime('%Y-%m-%d')
            xml_template = self.get_template_str('../templates/debitnote.xml')
            debit_note = Template(xml_template)
            output = debit_note.render(creditnote_fe_data)
        else:
            creditnote_fe_data['discrepancy_response_code'] = self.concepto_correccion_credito
            creditnote_fe_data['billing_reference_id'] = self.reversed_entry_id.prefix_invoice_number()
            creditnote_fe_data['billing_reference_cufe'] = self.reversed_entry_id.cufe
            creditnote_fe_data['billing_reference_issue_date'] = self._str_to_datetime(self.reversed_entry_id.create_date).strftime('%Y-%m-%d')
            xml_template = self.get_template_str('../templates/creditnote.xml')
            credit_note = Template(xml_template)
            output = credit_note.render(creditnote_fe_data)

        return output


    def firmar_factura_electronica(self):
        invoice = self
        if not invoice.file:
            raise ValidationError("El archivo no ha sido generado.")

        if invoice.firmado:
            raise ValidationError("El archivo ya fue firmado.")

        if (invoice.type == 'out_invoice' and
                not invoice.company_resolucion_id.tipo == 'facturacion-electronica'):
            raise ValidationError(
                "La resolución debe ser de tipo 'facturación electrónica'"
            )

        _logger.info('Factura {} firmada correctamente'.format(invoice.name))
        # validar que campos para firma existan

        config = {
            'policy_id': self.company_id.fe_url_politica_firma,
            'policy_name': self.company_id.fe_descripcion_polica_firma,
            'policy_remote': self.company_id.fe_archivo_polica_firma,
            'key_file': self.company_id.fe_certificado,
            'key_file_password': self.company_id.fe_certificado_password,
        }

        firmado = sign(invoice.file, config)

        # Asigna consecutivo de envío y nombre definitivo para la factura.
        if not invoice.consecutivo_envio:
            if invoice.type == 'out_invoice':
                invoice.consecutivo_envio = self.company_resolucion_id.proximo_consecutivo()
            elif invoice.type == 'out_refund':
                if self.company_resolucion_id.journal_id.refund_sequence_id:
                    invoice.consecutivo_envio = self.company_resolucion_id.proximo_consecutivo()
                else:
                    invoice.consecutivo_envio = self.company_resolucion_id.proximo_consecutivo()
            else:
                invoice.consecutivo_envio = invoice.id

        if not invoice.filename:
            invoice.filename = self._get_fe_filename()

        buff = BytesIO()
        zip_file = zipfile.ZipFile(buff, mode='w')

        zip_content = BytesIO()
        zip_content.write(firmado)
        zip_file.writestr(invoice.filename + '.xml', zip_content.getvalue())
        zip_file.close()

        zipped_file = base64.b64encode(buff.getvalue())

        attachment = self.env['ir.attachment'].create({
            'name': invoice.filename,
            'store_fname': invoice.filename + '.xml',
            'datas': base64.b64encode(firmado),
            'type': 'binary',
        })

        invoice.sudo().write({

            'file': base64.b64encode(firmado),
            'firmado': True,
            'zipped_file': zipped_file,
            'attachment_id': attachment.id
        })

        buff.close()

    def _borrar_info_factura_electronica(self):
        self.write({
            'filename': None,
            'firmado': False,
            'file': None,
            'zipped_file': None,
            'nonce': None,
            'qr_code': None,
            'cufe': None,
            'enviada': False,
            'envio_fe_id': None,
        })


    def borrar_factura_electronica(self):
        invoice = self
        if invoice.state != 'draft':
            raise ValidationError(
                "La factura debe encontrarse como "
                "borrador para poder realizar este proceso."
            )
        invoice._borrar_info_factura_electronica()


    def copy(self):
        copied_invoice = super(Invoice, self).copy()
        copied_invoice._borrar_info_factura_electronica()
        return copied_invoice

    # def enviar_factura_electronica(self):
    #     if self.type == 'out_invoice' and not self.company_resolucion_id.tipo == 'facturacion-electronica':
    #         raise ValidationError("La resolución debe ser de tipo 'facturación electronica'")
    #
    #     if self.enviada:
    #         raise ValidationError('La factura electrónica ya fue enviada a la DIAN.')
    #
    #     if not self.zipped_file:
    #         raise ValidationError('No se encontró la factura electrónica firmada')
    #
    #     response_nsd = {
    #         'b': 'http://schemas.datacontract.org/2004/07/UploadDocumentResponse',
    #         'c': 'http://schemas.datacontract.org/2004/07/XmlParamsResponseTrackId'
    #     }
    #     dian_webservice_url = self.env['ir.config_parameter'].search(
    #         [('key', '=', 'dian.webservice.url')], limit=1).value
    #
    #     service = WsdlQueryHelper(
    #         url=dian_webservice_url,
    #         template_file=self.get_template_str('../templates/soap_skel.xml'),
    #         key_file=self.company_id.fe_certificado,
    #         passphrase=self.company_id.fe_certificado_password
    #     )
    #
    #     _logger.info('Enviando factura {} al Webservice DIAN'.format(self.prefix_invoice_number()))
    #
    #     if self.company_id.fe_tipo_ambiente == '1':
    #         response = service.send_bill_async(
    #             zip_name=self.filename,
    #             zip_data=self.zipped_file
    #         )
    #     elif self.company_id.fe_tipo_ambiente == '2':
    #         response = service.send_test_set_async(
    #             zip_name=self.filename,
    #             zip_data=self.zipped_file,
    #             test_set_id=self.company_id.fe_test_set_id
    #         )
    #     else:
    #         raise ValidationError('Por favor configure el ambiente de destino en el menú de su compañía.')
    #
    #     if service.get_response_status_code() == 200:
    #         xml_content = etree.fromstring(response)
    #         track_id = [item for item in xml_content.iter() if item.tag == '{' + response_nsd['b'] + '}ZipKey']
    #         document_key = [item for item in xml_content.iter() if item.tag == '{' + response_nsd['c'] + '}DocumentKey']
    #         processed_message = [item for item in xml_content.iter() if item.tag == '{' + response_nsd['c'] + '}ProcessedMessage']
    #
    #         if track_id and track_id[0].text is not None:
    #             respuesta_envio = track_id[0].text
    #         elif document_key and document_key[0].text is not None:
    #             respuesta_envio = document_key[0].text
    #         else:
    #             respuesta_envio = processed_message[0].text if processed_message else 'Error en el envío'
    #
    #         envio_fe = self.env['l10n_co_cei.envio_fe'].create({
    #             'invoice_id': self.id,
    #             'fecha_envio': datetime.datetime.now().astimezone(pytz.timezone('America/Bogota')),
    #             'codigo_respuesta_envio': service.get_response_status_code(),
    #             'respuesta_envio': respuesta_envio,
    #             'nombre_archivo_envio': 'envio_{}_{}.xml'.format(
    #                 self.number,
    #                 datetime.datetime.now(pytz.timezone("America/Bogota")).strftime('%Y%m%d_%H%M%S')
    #             ),
    #             'archivo_envio': base64.b64encode(response.encode()),
    #         })
    #
    #         if track_id:
    #             if track_id[0].text is not None:
    #                 envio_fe.write({
    #                     'track_id': track_id[0].text
    #                 })
    #             else:
    #                 envio_fe.write({
    #                     'track_id': document_key[0].text
    #                 })
    #
    #         self.write({
    #             'envio_fe_id': envio_fe.id,
    #             'enviada': True
    #         })
    #
    #     else:
    #         raise ValidationError(response)

    def enviar_factura_electronica(self):
        if self.type == 'out_invoice' and not self.company_resolucion_id.tipo == 'facturacion-electronica':
            raise ValidationError("La resolución debe ser de tipo 'facturación electrónica'")

        if self.enviada:
            raise ValidationError('La factura electrónica ya fue enviada a la DIAN.')

        if not self.zipped_file:
            raise ValidationError('No se encontró la factura electrónica firmada')

        response_nsd = {
            'b': 'http://schemas.datacontract.org/2004/07/DianResponse',
            'c': 'http://schemas.microsoft.com/2003/10/Serialization/Arrays'
        }

        if self.company_id.fe_tipo_ambiente == '1':  # Producción
            dian_webservice_url = self.env['ir.config_parameter'].sudo().search(
                [('key', '=', 'dian.webservice.url')], limit=1).value
        else:
            dian_webservice_url = self.env['ir.config_parameter'].sudo().search(
                [('key', '=', 'dian.webservice.url.pruebas')], limit=1).value

        service = WsdlQueryHelper(
            url=dian_webservice_url,
            template_file=self.get_template_str('../templates/soap_skel.xml'),
            key_file=self.company_id.fe_certificado,
            passphrase=self.company_id.fe_certificado_password
        )

        _logger.info('Enviando factura {} al Webservice DIAN'.format(self.prefix_invoice_number()))

        if self.company_id.fe_tipo_ambiente == '1':  # Producción
            response = service.send_bill_sync(
                zip_name=self.filename,
                zip_data=self.zipped_file
            )

        # El metodo test async guarda la informacion en la grafica, el metodo bill_sync solo hace el conteo en los documentos (el test async habilita el set de pruebas el bill sync es para hacer pruebas sin habilitar el set)

        elif self.company_id.fe_tipo_ambiente == '2':  # Pruebas
            response = service.send_test_set_async(
                zip_name=self.filename,
                zip_data=self.zipped_file,
                test_set_id=self.company_id.fe_test_set_id
            )

        elif self.company_id.fe_tipo_ambiente == '3':  # Pruebas sin habilitacion
            response = service.send_bill_sync(
                zip_name=self.filename,
                zip_data=self.zipped_file
            )

        else:
            raise ValidationError('Por favor configure el ambiente de destino en el menú de su compañía.')

        if service.get_response_status_code() == 200:
            xml_content = etree.fromstring(response)
            track_id = [item for item in xml_content.iter() if item.tag == '{' + response_nsd['b'] + '}ZipKey']

            if self.company_id.fe_tipo_ambiente == '1':  # El método síncrono genera el CUFE como seguimiento
                document_key = [item for item in xml_content.iter() if item.tag == '{' + response_nsd['c'] + '}XmlDocumentKey']
            else:  # El método asíncrono genera el ZipKey como número de seguimiento
                document_key = [item for item in xml_content.iter() if item.tag == '{' + response_nsd['c'] + '}DocumentKey']

            processed_message = [item for item in xml_content.iter() if item.tag == '{' + response_nsd['c'] + '}ProcessedMessage']

            if track_id and track_id[0].text is not None:
                respuesta_envio = track_id[0].text
            elif document_key and document_key[0].text is not None:
                respuesta_envio = document_key[0].text
            else:
                respuesta_envio = processed_message[0].text if processed_message else self.cufe

            envio_fe = self.env['l10n_co_cei.envio_fe'].sudo().create({
                'invoice_id': self.id,
                'fecha_envio': datetime.datetime.now(),
                'codigo_respuesta_envio': service.get_response_status_code(),
                'respuesta_envio': respuesta_envio,
                'nombre_archivo_envio': 'envio_{}_{}.xml'.format(
                    self.name,
                    datetime.datetime.now(pytz.timezone("America/Bogota")).strftime('%Y%m%d_%H%M%S')
                ),
                'archivo_envio': base64.b64encode(response.encode()),
            })

            if track_id:
                if track_id[0].text is not None:
                    envio_fe.write({
                        'track_id': track_id[0].text
                    })
                else:
                    envio_fe.write({
                        'track_id': document_key[0].text
                    })

            self.write({
                'envio_fe_id': envio_fe.id,
                'enviada': True,
                'fe_approved': 'sin-calificacion'
            })

            # Producción - El envío y la validación se realizan en un solo paso.
            if self.company_id.fe_tipo_ambiente == '1':

                status_message = [item for item in xml_content.iter() if item.tag == '{' + response_nsd['b'] + '}StatusMessage']
                status_description = [item for item in xml_content.iter() if item.tag == '{' + response_nsd['b'] + '}StatusDescription']
                status_code = [item for item in xml_content.iter() if item.tag == '{' + response_nsd['b'] + '}StatusCode']
                validation_status = status_description[0].text if status_message else 'Error'
                validation_code = status_code[0].text if status_message else 'Error'

                if status_message:
                    log_status = status_message[0].text if status_message[0].text else status_description[0].text
                else:
                    log_status = 'Error'

                _logger.info('Respuesta de validación => {}'.format(log_status))

                envio_fe.write({
                    'codigo_respuesta_validacion': status_code[0].text,
                    'respuesta_validacion': status_description[0].text,
                    'fecha_validacion': datetime.datetime.now(),
                    'nombre_archivo_validacion': 'validacion_{}_{}.xml'.format(
                        self.name,
                        datetime.datetime.now(pytz.timezone("America/Bogota")).strftime('%Y%m%d_%H%M%S')
                    ),
                    'archivo_validacion': base64.b64encode(response.encode('utf-8'))
                })

                if validation_code == '00' and not self.enviada_por_correo:
                    _logger.info('Enviando factura {} por correo electrónico.'.format(self.prefix_invoice_number()))
                    self.notificar_correo()
                    self.enviada_por_correo = True

        else:
            raise ValidationError(response)

    def notificar_correo(self):
        if not self.zipped_file:
            raise ValidationError(
                'No se encontró la factura electrónica firmada.'
            )

        if not self.enviada:
            raise ValidationError(
                'La factura electrónica aún no ha sido enviada a la DIAN.'
            )

        template = self.env.ref(
            'l10n_co_cei.approve_invoice_fe_email_template'
        )

        archivos_fe = self.env['l10n_co_cei.fe_archivos_email'].search([
                    ('invoice_id', '=', self.id)
                ])

        archivos_fe_ids=[]

        for datos in archivos_fe:
            attachment_archivos_fe = self.env['ir.attachment'].search([('res_field', '!=', None),
                ('res_id', '=', datos.id), ('res_model', '=', 'l10n_co_cei.fe_archivos_email'),
            ], limit=1).id

            if attachment_archivos_fe:
                archivos_fe_ids.append(attachment_archivos_fe)

        if archivos_fe_ids:
            archivos_anexos = archivos_fe_ids + [self.attachment_id.id]
        else:
            archivos_anexos = [self.attachment_id.id]

        if template:
            template.email_from = str(self.fe_company_email_from)
            template.attachment_ids = [(6, 0, archivos_anexos)]
            template.send_mail(self.id, force_send=True)

    def intento_envio_factura_electronica(self):

        if self.fe_habilitar_facturacion_related:
            nsd = {
                's': 'http://www.w3.org/2003/05/soap-envelope',
                'u': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd'
            }
            # TODO: Mejorar o estandarizar este handling
            self._load_config_data()
            try:
                self.enviar_factura_electronica()
            except Exception as e:
                try:
                    msg, _ = e.args
                except:
                    msg = e.args

                try:
                    soap = etree.fromstring(msg)
                    msg_tag = [item for item in soap.iter() if item.tag == '{' + nsd['s'] + '}Text']
                    msg = msg_tag[0].text
                except:
                    pass

                _logger.error(
                    u'No fue posible enviar la factura electrónica a la DIAN. Información del error: {}'.format(msg))
                raise ValidationError(
                    u'No fue posible enviar la factura electrónica a la DIAN.\n\nInformación del error:\n\n {}'.format(msg))
            self._unload_config_data()
        else:
            _logger.error(u'Esta compañia no tiene habilitada Facturación Electrónica para Colombia')
            raise ValidationError(u'Esta compañia no tiene habilitada Facturación Electrónica para Colombia')

    def type_out_invoice(self):
        if self.fe_habilitar_facturacion_related:
            resolucion = None
            self.es_factura_electronica = True

            if not self.partner_id.fe_habilitada:
                raise ValidationError(
                    "Este usuario no se encuentra habilitado para Facturar Electronicamente \n\n"
                    "Habilite la Facturación Electrónica dentro del modulo de contactos"
                )

            if not self.company_id.fe_software_id:
                raise ValidationError(
                    "El ID de software de facturación electrónica no ha sido "
                    "configurado en registro de empresa (res.company.fe_software_id)"
                )
            if not self.company_id.fe_software_pin:
                raise ValidationError(
                    "El PIN de facturación electrónica no ha sido configurado en registro "
                    "de empresa (res.company.fe_software_pin)"
                )
            if not self.name or self.name =='/':
                resolucion = self.env['l10n_co_cei.company_resolucion'].search([
                    ('id', '=', self.journal_id.company_resolucion_factura_id.id),
                ], limit=1)

                if not resolucion:
                    raise ValidationError(
                        "No se encontró resolución activa."
                    )
                # check if number is within the range
                if not resolucion.check_resolution():
                    raise ValidationError(
                        "Consecutivos de resolución agotados."
                    )
            for index, invoice_line_id in enumerate(self.invoice_line_ids):
                taxes = invoice_line_id.tax_ids

                for tax in taxes:
                    if not tax.codigo_fe_dian or not tax.nombre_tecnico_dian:
                        raise ValidationError(
                            'Por favor configure los campos código y nombre DIAN '
                            'para el impuesto {}'.format(tax.name)
                        )

            if not self.company_resolucion_id and resolucion:
                self.company_resolucion_id = resolucion.id

        super(Invoice, self).action_post()

        if self.fe_habilitar_facturacion_related:

            self.access_token = self.access_token if self.access_token else str(
                uuid.uuid4())

            self._load_config_data()

            self.generar_factura_electronica()
            self.firmar_factura_electronica()

            self._unload_config_data()

    def type_out_refund(self):
        if self.fe_habilitar_facturacion_related:
            self.es_factura_electronica = True

            if not self.partner_id.fe_habilitada:
                raise ValidationError(
                    "Este usuario no se encuentra habilitado para Facturar Electronicamente \n\n"
                    "Habilite la Facturación Electrónica dentro del modulo de contactos"
                )

            if not self.company_id.fe_software_id:
                raise ValidationError(
                    "El ID de facturación electrónica no ha sido configurado "
                    "en registro de empresa (res.company.fe_software_id)"
                )
            if not self.company_id.fe_software_pin:
                raise ValidationError(
                    "El PIN de facturación electrónica no ha sido configurado en registro "
                    "de empresa (res.company.fe_software_pin)"
                )

            resolucion = self.env['l10n_co_cei.company_resolucion'].search([
                ('id', '=', self.journal_id.company_resolucion_credito_id.id),
            ], limit=1)

            if not resolucion:
                raise ValidationError(
                    "No se encontró resolución activa."
                )
            # check if number is within the range
            if not resolucion.check_resolution():
                raise ValidationError(
                    "Consecutivos de resolución agotados."
                )

            if not self.company_resolucion_id and resolucion:
                self.company_resolucion_id = resolucion.id

            for index, invoice_line_id in enumerate(self.invoice_line_ids):
                taxes = invoice_line_id.tax_ids

                for tax in taxes:
                    if not tax.codigo_fe_dian or not tax.nombre_tecnico_dian:
                        raise ValidationError(
                            'Por favor configure los campos código y nombre DIAN '
                            'para el impuesto {}'.format(tax.name)
                        )

        super(Invoice, self).action_post()

        if self.fe_habilitar_facturacion_related:

            self.access_token = self.access_token if self.access_token else str(
                uuid.uuid4())

            self._load_config_data()

            self.generar_factura_electronica()
            self.firmar_factura_electronica()

            self._unload_config_data()

    # asigna consecutivo de facturacion electronica
    def action_post(self):
        resolucion = self.env['l10n_co_cei.company_resolucion'].search([
            ('company_id', '=', self.company_id.id),
            ('journal_id', '=', self.journal_id.id),
            ('state', '=', 'active'),
        ], limit=1)

        if self.type == 'out_invoice' and resolucion.tipo == 'facturacion-electronica':
            self.type_out_invoice()
        elif self.type == 'out_refund' and resolucion.tipo == 'facturacion-electronica':
            if not self.reversed_entry_id:
                raise ValidationError(
                    "No se pueden validar facturas crédito que no esten vinculadas "
                    "a una factura existente."
                )
            else:
                self.type_out_refund()
        else:
            super(Invoice, self).action_post()

        return self

    def download_xml(self):
        if self.fe_habilitar_facturacion_related:
            if self.tipo_resolucion_diario_f == 'facturacion-electronica':
                global fe_company
                config_fe = self._get_config()
                fe_company = {
                    ConfigFE.company_nit.name: config_fe.get_value(
                        field_name=ConfigFE.company_nit.name,
                        obj_id=self.id
                    )
                }
                filename = self._get_fe_filename()
                fe_company = None

                return {
                    'name': 'Report',
                    'type': 'ir.actions.act_url',
                    'url': (
                            "web/content/?model=" +
                            self._name + "&id=" + str(self.id) +
                            "&filename_field=filename&field=file&download=true&filename=" +
                            filename + '.xml'
                    ),
                    'target': 'self',
                }
            else:
                _logger.error(u'Este documento no corresponde a una Factura Electrónica')
                raise ValidationError(u'Este documento no corresponde a una Factura Electrónica')
        else:
            _logger.error(u'Esta compañia no tiene habilitada Facturación Electrónica para Colombia')
            raise ValidationError(u'Esta compañia no tiene habilitada Facturación Electrónica para Colombia')

    def download_xml_firmado(self):
        if self.fe_habilitar_facturacion_related:
            if self.tipo_resolucion_diario_f == 'facturacion-electronica':
                filename = self._get_fe_filename()

                if filename:
                    return {
                        'name': 'Report',
                        'type': 'ir.actions.act_url',
                        'url': "web/content/?model=" + self._name + "&id=" + str(
                            self.id) + "&filename_field=filename&field=zipped_file&download=true&filename=" + filename + '.zip',
                        'target': 'self',
                    }
                else:
                    return {
                        'name': 'Report',
                        'type': 'ir.actions.act_url',
                        'url': "web/content/?model=" + self._name + "&id=" + str(
                            self.id) + "&filename_field=filename&field=zipped_file&download=true&filename=False.zip",
                        'target': 'self',
                    }
            else:
                _logger.error(u'Este documento no corresponde a una Factura Electrónica')
                raise ValidationError(u'Este documento no corresponde a una Factura Electrónica')
        else:
            _logger.error(u'Esta compañia no tiene habilitada Facturación Electrónica para Colombia')
            raise ValidationError(u'Esta compañia no tiene habilitada Facturación Electrónica para Colombia')
    # def consulta_fe_dian(self):
    #     response_nsd = {
    #         'b': 'http://schemas.datacontract.org/2004/07/DianResponse',
    #     }
    #     dian_webservice_url = self.env['ir.config_parameter'].search(
    #         [('key', '=', 'dian.webservice.url')], limit=1).value
    #
    #     service = WsdlQueryHelper(
    #         url=dian_webservice_url,
    #         template_file=self.get_template_str('../templates/soap_skel.xml'),
    #         key_file=self.company_id.fe_certificado,
    #         passphrase=self.company_id.fe_certificado_password
    #     )
    #     _logger.info('Consultando estado de validación para factura {}'.format(self.prefix_invoice_number()))
    #
    #     if not self.envio_fe_id.track_id:
    #         raise ValidationError(
    #             'No se puede realizar la consulta debido a que '
    #             'la factura no tiene un número de seguimiento asignado por la DIAN'
    #         )
    #
    #     try:
    #         if len(self.envio_fe_id.track_id) == 96:  # Consulta con CUFE de documento
    #             response = service.get_status(track_id=self.envio_fe_id.track_id)
    #         else:
    #             response = service.get_status_zip(track_id=self.envio_fe_id.track_id)
    #     except Exception as e:
    #         _logger.error('No fue posible realizar la consulta a la DIAN. Código de error: {}'.format(e))
    #         raise ValidationError(u'No fue posible realizar la consulta a la DIAN. \n\nCódigo de error: {}'.format(e))
    #
    #     xml_content = etree.fromstring(response)
    #     status_message = [item for item in xml_content.iter() if item.tag == '{' + response_nsd['b'] + '}StatusMessage']
    #     status_description = [item for item in xml_content.iter() if item.tag == '{' + response_nsd['b'] + '}StatusDescription']
    #     validation_status = status_description[0].text if status_message else 'Error'
    #
    #     if status_message:
    #         log_status = status_message[0].text if status_message[0].text else status_description[0].text
    #     else:
    #         log_status = 'Error'
    #
    #     _logger.info('Respuesta de validación => {}'.format(log_status))
    #
    #     if validation_status == 'Procesado Correctamente' and not self.enviada_por_correo:
    #         _logger.info('Enviando factura {} por correo electrónico.'.format(self.prefix_invoice_number()))
    #         self.notificar_correo()
    #         self.enviada_por_correo = True
    #
    #     data = {
    #         'codigo_respuesta': service.get_response_status_code(),
    #         'descripcion_estado': status_description[0].text,
    #         'hora_actual': datetime.datetime.now(),
    #         'contenido_respuesta': response,
    #         'nombre_fichero': 'validacion_{}_{}.xml'.format(
    #             self.number,
    #             datetime.datetime.now(pytz.timezone("America/Bogota")).strftime('%Y%m%d_%H%M%S')
    #         ),
    #     }
    #
    #     return data

    def consulta_fe_dian(self):
        response_nsd = {
            'b': 'http://schemas.datacontract.org/2004/07/DianResponse',
        }

        if self.company_id.fe_tipo_ambiente == '1':  # Producción
            dian_webservice_url = self.env['ir.config_parameter'].sudo().search(
                [('key', '=', 'dian.webservice.url')], limit=1).value
        else:
            dian_webservice_url = self.env['ir.config_parameter'].sudo().search(
                [('key', '=', 'dian.webservice.url.pruebas')], limit=1).value

        service = WsdlQueryHelper(
            url=dian_webservice_url,
            template_file=self.get_template_str('../templates/soap_skel.xml'),
            key_file=self.company_id.fe_certificado,
            passphrase=self.company_id.fe_certificado_password
        )
        _logger.info('Consultando estado de validación para factura {}'.format(self.prefix_invoice_number()))

        try:
            response = service.get_status(track_id=self.cufe)
        except Exception as e:
            _logger.error('No fue posible realizar la consulta a la DIAN. Código de error: {}'.format(e))
            raise ValidationError(u'No fue posible realizar la consulta a la DIAN. \n\nCódigo de error: {}'.format(e))

        xml_content = etree.fromstring(response)
        status_message = [item for item in xml_content.iter() if item.tag == '{' + response_nsd['b'] + '}StatusMessage']
        status_description = [item for item in xml_content.iter() if item.tag == '{' + response_nsd['b'] + '}StatusDescription']
        status_code = [item for item in xml_content.iter() if item.tag == '{' + response_nsd['b'] + '}StatusCode']
        validation_status = status_description[0].text if status_message else 'Error'
        validation_code = status_code[0].text if status_message else 'Error'

        if status_message:
            log_status = status_message[0].text if status_message[0].text else status_description[0].text
        else:
            log_status = 'Error'

        _logger.info('Respuesta de validación => {}'.format(log_status))

        data = {
            'codigo_respuesta': status_code[0].text,
            'descripcion_estado': status_description[0].text,
            'hora_actual': datetime.datetime.now(),
            'contenido_respuesta': response,
            'nombre_fichero': 'validacion_{}_{}.xml'.format(
                self.name,
                datetime.datetime.now(pytz.timezone("America/Bogota")).strftime('%Y%m%d_%H%M%S')
            ),
        }

        if validation_code == '00' and not self.enviada_por_correo:
            _logger.info('Enviando factura {} por correo electrónico.'.format(self.prefix_invoice_number()))
            self.notificar_correo()
            self.enviada_por_correo = True

        return data

    def get_base_url(self):
        external_url = self.env['ir.config_parameter'].sudo().get_param(
            'email.button.url'
        )

        if external_url and external_url != u' ':
            return external_url

        else:
            base_url = self.env['ir.config_parameter'].sudo().get_param(
                'web.base.url'
            )
            return base_url

    def get_attachment(self):
        if not self.attachment_id:
            raise ValidationError('No se encontró el archivo adjunto.')

        return self.attachment_id.id

    @api.model
    def cron_envio_dian(self):
        invoices = self.env['account.move'].search([
            ('state', '=', 'open'),
            ('enviada', '=', False),
            ('zipped_file', '!=', False),
        ])

        for invoice in invoices:
            if not invoice.enviada and \
                    invoice.state == 'open' and \
                    invoice.company_resolucion_id.tipo == 'facturacion-electronica':

                try:
                    _logger.info('=> Enviando factura No. {}'.format(invoice.name))
                    invoice.intento_envio_factura_electronica()
                except Exception as e:
                    _logger.error('[!] Error al enviar la factura {} - Excepción: {}'.format(invoice.name, e))

        invoices_72 = self.env['account.move'].search([
            ('state', '=', 'open'),
            ('enviada', '=', True),
            ('envio_fe_id', '!=', None),
            ('fe_approved', '=','sin-calificacion')
        ])

        for id_envio in invoices_72:
            if id_envio.envio_fe_id.fecha_validacion:
                hora_comparar = id_envio.envio_fe_id.fecha_validacion + datetime.timedelta(hours=72)
                hora = hora_comparar - datetime.datetime.now()
                horas = int(hora.total_seconds())
                if horas < 0 and id_envio.envio_fe_id.codigo_respuesta_validacion == '00':
                    id_envio.write({'fe_approved':'aprobada_sistema'})


    @api.model
    def _default_journal_fe(self):
        return self._get_default_journal()

    @api.onchange('fe_sucursal')
    def compute_journal_fe(self):
        self.journal_id = self._get_default_journal()

    @api.model
    def _get_default_journal(self):
        journal_id = super(Invoice, self)._get_default_journal()
        # Si la factura por defecto es una nota débito, busca de nuevo el diario por defecto

        if ((journal_id and journal_id.categoria == 'nota-debito') or (journal_id and self.credited_invoice_id)) and not self._context.get('default_journal_id', False):
            if self.fe_sucursal and self.fe_sucursal.journal_id_nd:
                journal_id = self.fe_sucursal.journal_id_nd
            else:
                domain = [
                    ('type', '=', journal_id.type),
                    ('company_id', '=', journal_id.company_id.id),
                    ('categoria', '=', 'nota-debito'),
                ]
                company_currency_id = journal_id.company_id.currency_id.id
                currency_id = self._context.get('default_currency_id') or company_currency_id
                currency_clause = [('currency_id', '=', currency_id)]
                if currency_id == company_currency_id:
                    currency_clause = ['|', ('currency_id', '=', False)] + currency_clause
                journal_id = self.env['account.journal'].search(domain + currency_clause, limit=1)

                return journal_id
        # if self.es_factura_electronica and self.fe_habilitar_facturacion_related:

        if self.fe_sucursal and self.fe_sucursal.journal_id_fv:
            journal_id = self.fe_sucursal.journal_id_fv

        return journal_id



    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_journal_fe,
        domain="""
            [('type', 'in', {'out_invoice': ['sale'], 
            'out_refund': ['sale'], 'in_refund': ['purchase'], 
            'in_invoice': ['purchase']}.get(type, [])), 
            ('company_id', '=', company_id)]
            """
    )
