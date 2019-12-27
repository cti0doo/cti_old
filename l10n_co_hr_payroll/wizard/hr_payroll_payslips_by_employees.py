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

from odoo import models


class hr_payslip_employees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    # def _get_period(self, dt=None):
    #    cr = self._cr
    #    uid = self.env.user.id
    #    context= self.env.context
    #    period_obj = self.pool.get('account.period')
    #    period_id = period_obj.find(cr, uid, dt=dt, context=context)
    #    if period_id:
    #        return period_id[0]
    #    return False

    # def _get_default_period(self):
    #    cr = self._cr
    #    uid = self.env.user.id
    #    context= self.env.context
    #    return self._get_period(cr, uid, dt=None, context=context)    

    # def compute_sheet(self):
    # cr = self.env.cr
    # uid = self.env.user.id
    # ids = self.id
    # context= self.env.context
    # emp_pool = self.env['hr.employee'] #pool.get('hr.employee')
    # run_pool = self.env['hr.payslip.run'] #pool.get('hr.payslip.run')
    # if context is None:
    #    context = {}
    # if context and context.get('active_id', False):
    #    run_data = run_pool.read(cr, uid, context['active_id'], ['period_id', 'date_start', 'date_end'])

    # period_id = run_data.get('period_id', False)
    # date_start = run_data.get('date_start', False)
    # if date_start:
    #    period_id = self._get_period(cr, uid, dt=date_start)
    # if period_id: 
    #    context.update({'period_id': period_id})
    # print "Data Start: ", run_data.get('date_start', False), " Date End:", run_data.get('date_end', False)
    # print "Context: ", context, " Period :", period_id
    # data = self.read(cr, uid, ids, context=context)[0]
    # for emp in emp_pool.browse(cr, uid, data['employee_ids'], context=context):
    #    if not emp.contract_id:
    #        raise osv.except_osv(_("Warning!"), _("El empleado %s no tiene 'Contrato'") % (emp.name))
    #    if not emp.address_home_id:
    #        raise osv.except_osv(_("Warning!"), _("El empleado %s no tiene 'Empleado / Tercero'") % (emp.name))
    #    if not emp.contract_id.struct_id:
    #        raise osv.except_osv(_("Warning!"), _("El contrato de %s no tiene 'Estructura Salarial'") % (emp.name))
    #    if not emp.contract_id.working_hours:
    #        raise osv.except_osv(_("Warning!"), _("El contrato de %s no tiene 'Planificación de Trabajo'") % (emp.name))

    # return super(hr_payslip_employees, self).compute_sheet(cr, uid, ids, context=context)

# pass #return False

# hr_payslip_employees()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
