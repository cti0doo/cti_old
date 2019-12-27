# -*- coding: utf-8 -*-

import base64
import io
import logging
import zipfile
import xmltodict

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class FacturaProveedor(models.TransientModel):
    _name = 'l10n_co_cei.factura_proveedor'
    _descripcion = 'Carga de factura de proveedor'

    file = fields.Binary(
        string='Factura de proveedor'
    )

    def _get_invoice_data(self, parsed_data):

        ns = {
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
            'fe': 'http://www.dian.gov.co/contratos/facturaelectronica/v1',
        }

        invoice_data = {}

        invoice = parsed_data[ns['fe'] + ':Invoice']
        invoice_data['invoice_id'] = invoice[ns['cbc'] + ':ID']
        invoice_data['invoice_uuid'] = invoice[ns['cbc'] + ':UUID']['#text']
        invoice_data['invoice_issue_date'] = invoice[ns['cbc'] + ':IssueDate']
        invoice_data['invoice_issue_time'] = invoice[ns['cbc'] + ':IssueTime']
        invoice_data['invoice_type_code'] = (
            invoice[ns['cbc'] + ':InvoiceTypeCode']['#text']
        )
        invoice_data['invoice_note'] = invoice[ns['cbc'] + ':Note']
        # account supplier party
        invoice_data['supplier'] = {}
        supplier = invoice[ns['fe'] + ':AccountingSupplierParty']
        invoice_data['supplier']['additional_account_id'] = (
            supplier[ns['cbc'] + ':AdditionalAccountID']
        )
        supplier_party = supplier[ns['fe'] + ':Party']
        invoice_data['supplier']['party_identification'] = (
            supplier_party[ns['cac'] + ':PartyIdentification']
            [ns['cbc'] + ':ID']
            ['#text']
        )
        invoice_data['supplier']['party_name'] = (
            supplier_party[ns['cac'] + ':PartyName'][ns['cbc'] + ':Name']
        )
        invoice_data['supplier']['department'] = (
            supplier_party[ns['fe'] + ':PhysicalLocation']
            [ns['fe'] + ':Address']
            [ns['cbc'] + ':Department']
        )
        invoice_data['supplier']['city_name'] = (
            supplier_party[ns['fe'] + ':PhysicalLocation']
            [ns['fe'] + ':Address']
            [ns['cbc'] + ':CityName']
        )
        invoice_data['supplier']['address'] = (
            supplier_party[ns['fe'] + ':PhysicalLocation']
            [ns['fe'] + ':Address']
            [ns['cac'] + ':AddressLine']
            [ns['cbc'] + ':Line']
        )
        invoice_data['supplier']['country'] = (
            supplier_party[ns['fe'] + ':PhysicalLocation']
            [ns['fe'] + ':Address']
            [ns['cac'] + ':Country']
            [ns['cbc'] + ':IdentificationCode']
        )
        invoice_data['supplier']['tax_level_code'] = (
            supplier_party[ns['fe'] + ':PartyTaxScheme']
            [ns['cbc'] + ':TaxLevelCode']
        )
        invoice_data['supplier']['registration_name'] = (
            supplier_party[ns['fe'] + ':PartyLegalEntity']
            [ns['cbc'] + ':RegistrationName']
        )
        # customer
        invoice_data['customer'] = {}
        customer = invoice[ns['fe'] + ':AccountingCustomerParty']
        invoice_data['customer']['additional_account_id'] = (
            customer[ns['cbc'] + ':AdditionalAccountID']
        )
        customer_party = customer[ns['fe'] + ':Party']
        invoice_data['customer']['party_identification'] = (
            customer_party[ns['cac'] + ':PartyIdentification']
            [ns['cbc'] + ':ID']
            ['#text']
        )

        try:
            customer_party[ns['cac'] + ':PartyName']
        except KeyError:
            invoice_data['customer']['party_name'] = None

        invoice_data['customer']['department'] = (
            customer_party[ns['fe'] + ':PhysicalLocation']
            [ns['fe'] + ':Address']
            [ns['cbc'] + ':Department']
        )
        invoice_data['customer']['city_name'] = (
            customer_party[ns['fe'] + ':PhysicalLocation']
            [ns['fe'] + ':Address']
            [ns['cbc'] + ':CityName']
        )
        invoice_data['customer']['address'] = (
            customer_party[ns['fe'] + ':PhysicalLocation']
            [ns['fe'] + ':Address']
            [ns['cac'] + ':AddressLine']
            [ns['cbc'] + ':Line']
        )
        invoice_data['customer']['country'] = (
            customer_party[ns['fe'] + ':PhysicalLocation']
            [ns['fe'] + ':Address']
            [ns['cac'] + ':Country']
            [ns['cbc'] + ':IdentificationCode']
        )
        invoice_data['customer']['tax_level_code'] = (
            customer_party[ns['fe'] + ':PartyTaxScheme']
            [ns['cbc'] + ':TaxLevelCode']
        )

        try:
            invoice_data['customer']['registration_name'] = (
                customer_party[ns['fe'] + ':PartyLegalEntity']
                [ns['cbc'] + ':RegistrationName']
            )
        except KeyError:
            invoice_data['customer']['registration_name'] = None

        try:
            person = customer_party[ns['fe'] + ':Person']
            invoice_data['customer']['person'] = {
                'firstname': person[ns['cbc'] + ':FirstName'],
                'familyname': person[ns['cbc'] + ':FamilyName'],
                'middlename': person[ns['cbc'] + ':MiddleName'],
            }
        except KeyError:
            invoice_data['customer']['person'] = {
                'firstname': None,
                'familyname': None,
                'middlename': None,
            }

        invoice_data['legal_monetary_total'] = {}
        legal_monetary_total = invoice[ns['fe'] + ':LegalMonetaryTotal']
        invoice_data['legal_monetary_total'] = {
            'line_extension_amount': (
                legal_monetary_total[ns['cbc'] + ':LineExtensionAmount']
                ['#text']
            ),
            'tax_exclusive_amount': (
                legal_monetary_total[ns['cbc'] + ':TaxExclusiveAmount']
                ['#text']
            ),
            'payabel_amount': (
                legal_monetary_total[ns['cbc'] + ':PayableAmount']['#text']
            )
        }

        invoice_data['invoice_lines'] = []
        if isinstance(invoice[ns['fe'] + ':InvoiceLine'], list):
            for invoice_line in invoice[ns['fe'] + ':InvoiceLine']:

                item = invoice_line[ns['fe'] + ':Item']
                price = invoice_line[ns['fe'] + ':Price']

                invoice_data['invoice_lines'].append({
                    'id': invoice_line[ns['cbc'] + ':ID'],
                    'invoiced_quantity': invoice_line[ns['cbc'] + ':InvoicedQuantity'],
                    'line_extension_amount': (
                        invoice_line[ns['cbc'] + ':LineExtensionAmount']
                        ['#text']
                    ),
                    'item': {
                        'description': item[ns['cbc'] + ':Description']
                    },
                    'price': {
                        'price_amount': price[ns['cbc'] + ':PriceAmount']['#text']
                    },
                    'id': invoice_line[ns['cbc'] + ':ID'],
                })

        else:
            invoice_line = invoice[ns['fe'] + ':InvoiceLine']

            item = invoice_line[ns['fe'] + ':Item']
            price = invoice_line[ns['fe'] + ':Price']

            invoice_data['invoice_lines'].append({
                'id': invoice_line[ns['cbc'] + ':ID'],
                'invoiced_quantity': invoice_line[ns['cbc'] + ':InvoicedQuantity'],
                'line_extension_amount': (
                    invoice_line[ns['cbc'] + ':LineExtensionAmount']['#text']
                ),
                'item': {
                    'description': item[ns['cbc'] + ':Description']
                },
                'price': {
                    'price_amount': price[ns['cbc'] + ':PriceAmount']['#text']
                },
            })

        return invoice_data

    def cargar_factura_proveedor(self):
        if not self.file:
            raise ValidationError(
                "Debe adjuntar una factura para continuar con esta acción"
            )
        file_object = io.BytesIO(base64.b64decode(self.file))
        zipfile_ob = zipfile.ZipFile(file_object)

        for finfo in zipfile_ob.infolist():
            ifile = zipfile_ob.read(finfo)

            parsed_xml = xmltodict.parse(
                ifile,
                process_namespaces=True
            )

            invoice_data = self._get_invoice_data(parsed_xml)

            # busca tercero
            partner_id = self.env['res.partner'].search([
                (
                    'nit',
                    '=',
                    invoice_data['supplier']['party_identification']
                )
            ], limit=1).id

            # auxiliar de factura
            invoice_account = self.env['account.account'].search([
                (
                    'user_type',
                    '=',
                    self.env.ref('account.data_account_type_payable').id
                )
            ], limit=1).id

            # auxiliar de linea
            invoice_line_account = self.env['account.account'].search([
                (
                    'user_type',
                    '=',
                    self.env.ref('account.data_account_type_expense').id
                )
            ], limit=1).id

            if not partner_id:
                raise ValidationError(
                    "Nit [%s] No se encuentra registrado como tercero en el "
                    "sistema" % invoice_data['supplier']['party_identification']
                )

            # crea cabecera de factura
            invoice = self.env['account.move'].create({
                'partner_id': partner_id,
                'account_id': invoice_account,
                'type': 'in_invoice',
            })

            # lineas de factura
            for invoice_line in invoice_data['invoice_lines']:
                self.env['account.move.line'].create({
                    # 'product_id': self.env.ref('product.product_product_4').id,
                    'quantity': invoice_line['invoiced_quantity'],
                    'price_unit': invoice_line['price']['price_amount'],
                    'invoice_id': invoice.id,
                    'name': invoice_line['item']['description'],
                    'account_id': invoice_line_account,
                    # 'invoice_line_tax_ids': [(6, 0, [tax.id])],
                    # 'account_analytic_id': analytic_account.id,
                })

            # return invoice
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form,tree',
                'res_model': 'account.move',
                'target': 'current',
                'res_id': invoice.id,
            }
