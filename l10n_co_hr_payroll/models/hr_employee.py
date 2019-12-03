# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import logging

from odoo import models, api, fields

_logger = logging.getLogger(__name__)


class hr_employee(models.Model):
    _inherit = "hr.employee"

    _defaults = {
        'vehicle_distance': 2,
    }


class HRContractRegisterExtended(models.Model):
    _inherit = "hr.contract"

    register_ids = fields.One2many('hr.contract.register', 'contract_id', string='Partner')
    payslip_ids = fields.One2many('hr.payslip', 'contract_id', string='Payslips history')
    deductible_ids = fields.One2many('hr.deductible', 'contract_id', string='Deductible')


class HRContractDeductible(models.Model):
    _name = "hr.deductible"
    _description = "Deductible"

    contract_id = fields.Many2one('hr.contract', string='Contract')
    type = fields.Many2one('hr.deductible.type', string='Deductible type', required=True)
    amount = fields.Float(string='Amount', default=0.0)
    date_from = fields.Date(string='Date from')
    date_to = fields.Date(string='Date to')


class HRContractDeductibleType(models.Model):
    _name = "hr.deductible.type"
    _description = "Deductible Type"

    code = fields.Char(string='Code', required=True)
    name = fields.Char(string='Name', required=True, translate=True)
    tope = fields.Float(string='Tope (UVT)', required=True)


class HRContractRegisterLineExtended(models.Model):
    _name = "hr.contract.register"
    _description = "Contract Register"

    @api.onchange('register_id')
    def _get_partners(self):
        partner = []
        for x in self.register_id:
            partner.append(x.partner_id.id)
        return {'domain': {'partner_id': [('id', 'in', tuple(partner))]}}

    contract_id = fields.Many2one('hr.contract', string='Contract')
    register_id = fields.Many2one('res.partner', string='Register')
    partner_id = fields.Many2one('res.partner', string='Partner', domain=_get_partners)

    _sql_constraints = [
        ('contract_register', 'unique (contract_id,register_id)',
         'You can not have a record of repeated contribution per contract')
    ]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
