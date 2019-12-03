# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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
from datetime import timedelta
from odoo.tools import float_utils
from odoo import models, fields


class resource_calendar_template(models.Model):
    _name = "resource.calendar.template"
    _description = "Resource Calendar"

    name = fields.Char("Name", size=64, required=True, default="Default Calendar Template")
    attendance_ids = fields.One2many('resource.calendar.attendance.template', 'calendar_id', 'Working Time')

class resource_calendar_attendance_template(models.Model):
    _name = "resource.calendar.attendance.template"
    _description = "Work Detail"

    name = fields.Char("Name", size=64, required=True, default="Default Attendace Calendar Template")
    day_of_week = fields.Selection(
            [('0', 'Monday'), ('1', 'Tuesday'), ('2', 'Wednesday'), ('3', 'Thursday'), ('4', 'Friday'),
             ('5', 'Saturday'), ('6', 'Sunday')], 'Day of Week', required=True, index=True, default = '0')
    date_from = fields.Date('Starting Date')
    hour_from = fields.Float('Work from', required=True, default=8, help="Start and End time of working.", index=True)
    hour_to = fields.Float("Work to", required=True, default=17)
    # TODO: required=True
    calendar_id = fields.Many2one("resource.calendar.template", "Resource's Calendar")
