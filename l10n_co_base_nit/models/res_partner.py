# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2012 OpenERP SA (<http://odoo.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, _

import logging

_logger = logging.getLogger(__name__)


class res_partner(models.Model):
    """Partner extension."""

    _inherit = 'res.partner'

    """Document type: Lista de selección con los tipos de documento aceptados
       por la autoridad de impuestos (DIAN).
        11 - Registro civil
        12 - Tarjeta de identidad
        13 - Cédula de ciudadanía
        21 - Tarjeta de extranjería
        22 - Cédula de extranjería
        31 - NIT (Número de identificación tributaria)
        41 - Pasaporte
        42 - Tipo de documento extranjero
        43 - Para uso definido por la DIAN

        http://www.dian.gov.co/descargas/normatividad/Factura_Electronica/Anexo_001_R14465.pdf"""

    vat_type = fields.Selection([
        ('12', u'12 - Tarjeta de identidad'),
        ('13', u'13 - Cédula de ciudadanía'),
        ('21', u'21 - Tarjeta de extranjería'),
        ('22', u'22 - Cédula de extranjería'),
        ('31', u'31 - NIT (Número de identificación tributaria)'),
        ('41', u'41 - Pasaporte'),
        ('42', u'42 - Documento de identificación extranjero'),
        ('43', u'43 - Sin identificación del exterior o para uso definido por la DIAN')
    ], string='VAT type',
        help='''Customer identifier, according to types given by the DIAN.
                If it is a natural person and has RUT use NIT''',
        required=True, default='13'
    )
    vat_vd = fields.Char('vd', size=1, help='VD')
    stock_holder = fields.Selection([
        ('sh', 'Stock holder'),
        ('nsh', 'No Stock holder')
    ], 'Stock holder', default='nsh', required=True)

    
    def write(self, vals):
        for record in self:
            if record.child_ids:
                for child in record.child_ids:
                    if vals.get('customer') is not None:
                        child.customer = vals.get('customer')
                    if vals.get('supplier') is not None:
                        child.supplier = vals.get('supplier')
                    if vals.get('stock_holder') is not None:
                        child.stock_holder = vals.get('stock_holder', child.stock_holder)
        return super(res_partner, self).write(vals)

    def _check_vat_co(self, vat_type, vat, vat_vd):
        if vat_type != '31':
            return True

        if not vat_vd or len(vat_vd) != 1:
            return False

        factor = [71, 67, 59, 53, 47, 43, 41, 37, 29, 23, 19, 17, 13, 7, 3]
        factor = factor[-len(vat):]
        csum = sum([int(vat[i]) * factor[i] for i in range(len(vat))])
        check = csum % 11
        if check > 1:
            check = 11 - check
        return check == int(vat_vd)

    def _onerror_msg(self, msg):
        return {'warning': {'title': _('Error!'), 'message': _(msg)}}

    @api.onchange('vat_type')
    def onchange_vat_type(self):

        return {'value': {'is_company': self.vat_type == '31'}}

    @api.onchange('vat')
    def onchange_vat(self):
        # Validaciones
        if not self.vat_type:
            return {'value': {'vat_vd': ''}}

        if self.vat:
            if len(self.vat) < 6:
                return self._onerror_msg(
                    u'VAT must have at least six digits.'
                )

            if not self.vat.isdigit() and self.vat_type != '41':
                return self._onerror_msg(u'VAT must have only numbers')

            if self.vat_type != '31':
                return {'value': {'vat_vd': ''}}

        return {'value': {'vat_vd': ''}}

    @api.onchange('vat_vd')
    def onchange_vat_vd(self):

        if self.vat_type == '31':
            if not self.vat_vd:
                return self._onerror_msg(
                    u"VD is required"
                )

            if not self._check_vat_co(self.vat_type, self.vat, self.vat_vd):
                return self._onerror_msg(
                    u'Given NIT is not valid!'
                )

        return False

    def _commercial_fields(self):
        """
        Return the list of fields that are managed by the commercial entity
        to which a partner belongs.

        These fields are meant to be hidden on partners that aren't
        `commercial entities` themselves, and will be delegated to
        the parent `commercial entity`. The list is meant to be
        extended by inheriting classes.
        """
        return ['website']

    def copy(self):
        [partner_dic] = self.read(['name', 'vat'])
        default = {}
        default.update({
            'name': '(copy) ' + partner_dic.get('name'),
            'vat': '(copy) ' + partner_dic.get('vat'),
        })
        return super(res_partner, self).copy(default)

    def _check_vat(self):
        if self.company_id and self.vat and self.search(
                [('company_id', '=', self.company_id.id), ('vat', '=ilike', self.vat),
                 ('parent_id', '=', None)]).id != self.id:
            return False
        return True

    def _check_vat_vd(self):
        if self.vat_type == '31' and not self._check_vat_co(self.vat_type, self.vat, self.vat_vd):
            return False
        return True

   # _constraints = [
   #     # TODO: Validar que ya existe el VAT
   #     # (_check_vat, 'NIT already exist!', ["vat", ]),
   #     (_check_vat_vd,
   #      u"Given NIT did't pass the validation!",
   #      ["vat_vd", ]),
   # ]

    # TODO: Restricción de codigo unico por compañía
    # _sql_constraints = [
    #     ('code_name_uniq',
    #      'unique (company_id,name)',
    #      u'Customer/Provider must be uniq per company!')
    # ]
