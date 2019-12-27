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

import logging

from odoo import SUPERUSER_ID
from odoo import models

_logger = logging.getLogger('3RP')


class wizard_update_calendar(models.TransientModel):
    """
        Wizard update calendar and attendance from template for multicompany
    """
    _name = "wizard.update.calendar"
    _description = "Wizard Update Calendar"

    def get_resource_calendar_attendance_template(self, rc_temp_id, rc_id, obj_rca_temp):

        cr = self._cr
        uid = self.env.user_id.id
        ids = self.id
        context = self.env.context
        rca_refs = {}
        rca_temp_ids = obj_rca_temp.search(cr, uid, [('calendar_id', '=', rc_temp_id)])
        for rca in obj_rca_temp.browse(cr, uid, rca_temp_ids):
            vals = {
                'name': rca.name,
                'day_of_week': rca.day_of_week,
                'date_from': rca.date_from,
                'hour_from': rca.hour_from,
                'hour_to': rca.hour_to,
                'calendar_id': rc_id,
            }
            rca_refs[rca.id] = vals

        return rca_refs

    def update_calendar_from_template(self, context=None):
        cr = self._cr
        uid = self.env.user_id.id
        ids = self.id
        context = self.env.context
        '''
        Update resource calendar and attendance from template
        '''
        uid = SUPERUSER_ID
        obj_company = self.pool.get('res.company')
        obj_rc = self.pool.get('resource.calendar')
        obj_rc_temp = self.pool.get('resource.calendar.template')
        obj_rca = self.pool.get('resource.calendar.attendance')
        obj_rca_temp = self.pool.get('resource.calendar.attendance.template')

        company_ids = obj_company.search(cr, uid, [])

        for company_id in obj_company.browse(cr, uid, company_ids):
            _logger.info("UPDATE resource.calendar and attendance for Company: %s", company_id.name)
            rc_temp_ids = obj_rc_temp.search(cr, uid, [])
            for rc_temp in obj_rc_temp.browse(cr, uid, rc_temp_ids):
                rc_id = obj_rc.search(cr, uid, [('company_id', '=', company_id.id), ('name', '=', rc_temp.name)])
                if not rc_id:
                    rc_id = obj_rc.create(cr, uid, {'name': rc_temp.name, })
                    for key, rca_ref in self.get_resource_calendar_attendance_template(cr, uid, rc_temp.id, rc_id,
                                                                                       obj_rca_temp).items():
                        obj_rca.create(cr, uid, rca_ref)
                else:
                    for key, rca_ref in self.get_resource_calendar_attendance_template(cr, uid, rc_temp.id, rc_id[0],
                                                                                       obj_rca_temp).items():
                        rca_id = obj_rca.search(cr, uid, [('name', '=', rca_ref['name']),
                                                          ('calendar_id', '=', rca_ref['calendar_id'])])
                        if rca_id:
                            obj_rca.write(cr, uid, rca_id, rca_ref)
                        else:
                            obj_rca.create(cr, uid, rca_ref)

        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
