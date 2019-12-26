# -*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

from odoo import models, fields

_logger = logging.getLogger('PAYROLL')


class hr_leave_type(models.Model):
    _inherit = "hr.leave.type"
    _description = "Leave Type"

    code = fields.Char('Code', size=64, required=False, readonly=False)
    limit = fields.Boolean('Limit')
    timesheet_generate = fields.Boolean('Timesheet Generate')

class HrLeave(models.Model):
    _inherit = 'hr.leave'

    diagnosis_id = fields.Many2one('hr.diagnosis', string='Diagnosis')


class Diagnosis(models.Model):
    _name = 'hr.diagnosis'
    _description = 'Diagnosis'

    code = fields.Char(string='Code', size=64, required=True)
    name = fields.Char(string='Name', required=True)
