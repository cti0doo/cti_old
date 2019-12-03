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

from odoo import models, fields, api
from odoo.exceptions import except_orm, Warning
from odoo.tools.translate import _

_logger = logging.getLogger('3RP')


class HrPayslipLineExtended(models.Model):
    _inherit = 'hr.payslip.line'

    def _get_partner_id(self, credit_account):
        """
        Get partner_id of slip line to use in account_move_line
        """
        register = self.salary_rule_id.register_id
        partner_id = self.slip_id.employee_id.address_home_id.id
        for rg in self.slip_id.contract_id.register_ids:
            if rg.register_id.id == register.id:
                partner_id = rg.partner_id.id
        if not partner_id:
            raise Warning('The contract %s has no defined contribution registry for %s' % (
                self.slip_id.contract_id.name, register.name))
        if credit_account:
            if partner_id or self.salary_rule_id.account_credit.internal_type in ('receivable', 'payable'):
                return partner_id
        else:
            if partner_id or self.salary_rule_id.account_debit.internal_type in ('receivable', 'payable'):
                return partner_id
        return False




class HrContributionRegisterPartnerExtended(models.Model):
    _name = 'hr.contribution.partner.register'
    _description = 'HR Contribution Partner Register'

    register_id = fields.Many2one('res.partner', string='Register')
    partner_id = fields.Many2one('res.partner', string='Partner')
    code = fields.Char(string='Code')
    code2 = fields.Char(string='Other code')


class AccountJournalAdvance(models.Model):
    _inherit = 'account.journal'

    account_advance_id = fields.Many2one('account.account', string='Advance account')


class hr_payslip_run(models.Model):
    _inherit = 'hr.payslip.run'

    
    def confirm_payslip_run(self):
        for run in self:
            if run.state == 'draft':
                for slip in run.slip_ids:
                    if slip.state == 'draft':
                        _logger.info(slip)
                        slip.action_payslip_done()
                self.close_payslip_run()
        return True

    
    def draft_payslip_run(self):
        for run in self:
            if run.state == 'close':
                for slip in run.slip_ids:
                    if slip.state == 'done':
                        slip.action_payslip_cancel()
                        slip.action_payslip_draft()
                self.write({'state': 'draft'})
        return True


class hr_payslip(models.Model):
    _inherit = 'hr.payslip'

    # def get_worked_day_lines(self, contract_ids, date_from, date_to):
    #     """
    #     Se sobre escribe esta funcion para adicionar el CODE en la regla y poder usarlo en los calculos
    #     @param contract_ids: list of contract id
    #     @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
    #     """
    #     cr = self._cr
    #     uid = self.env.user.id
    #     ids = self.id
    #     context = self.env.context
    #
    #     def _get_code_holidays_status(name):
    #         holidays_status_pool = self.pool.get('hr.leave.type')
    #         id = holidays_status_pool.search(cr, uid, [('name', 'ilike', name)])[0]
    #
    #         return holidays_status_pool.browse(cr, uid, id).code or name
    #
    #     res = super(hr_payslip, self).get_worked_day_lines(contract_ids, date_from, date_to)
    #     d = parser.parse(date_from)
    #
    #     last_day_of_month = calendar.monthrange(d.year, d.month)[1]
    #     working_days = 0.0
    #     leaves_days = 0.0
    #
    #     """
    #         compute_30 = (days_work100 == last_day_of_month) and 30.0 or days_work100
    #
    #         if (days_work100 + extended_leave) == last_day_of_month:
    #             compute_30 = 30.0 - extended_leave
    #     """
    #
    #     for k in res:
    #         k['number_of_days'] = (k['number_of_days'] == last_day_of_month) and 30.0 or k['number_of_days']
    #         if k['code'] == 'WORK100':
    #             working_days += k['number_of_days']
    #         else:
    #             leaves_days += k['number_of_days']
    #             k['code'] = _get_code_holidays_status(k['name'])
    #
    #     # Reasigna valor de dias en funcion de 30
    #     compute_30 = ((working_days == last_day_of_month) and 30.0 or False) or (
    #             ((working_days + leaves_days) == last_day_of_month) and (30.0 - leaves_days) or False) or working_days
    #
    #     for k in res:
    #         if k['code'] == 'WORK100':
    #             k['number_of_days'] = compute_30
    #             k['number_of_hours'] = compute_30 * 8.0
    #     return res

    def hr_verify_sheet(self):
        cr = self._cr
        uid = self.env.user.id
        ids = self.id
        context = self.env.context
        for payroll in self.browse(cr, uid, ids, context=context):
            if not payroll.employee_id.address_home_id:
                raise except_orm(_('Warning'), _('This employee don´t have a home address'))
            if not payroll.contract_id.working_hours:
                raise except_orm(_('Warning'), _('This employee don´t have a working hours'))
        return super(hr_payslip, self).hr_verify_sheet(cr, uid, ids)

    # def onchange_contract_id(self, date_from, date_to, employee_id=False, contract_id=False):
    #     """ Actualiza journal en los slip"""
    #     cr = self._cr
    #     uid = self.env.user.id
    #     ids = self.id
    #     context = self.env.context
    #
    #     res = super(hr_payslip, self).onchange_contract_id(cr, uid, ids, date_from, date_to, employee_id=employee_id,
    #                                                        contract_id=contract_id, context=context)
    #     if not res['value']['journal_id'] and contract_id:
    #         contract = self.pool.get('hr.contract').browse(cr, uid, contract_id, context=context)
    #         journal_id = self.pool.get('account.journal').search(cr, uid, [('code', '=ilike', 'NOM'), (
    #             'company_id', '=', contract.employee_id.company_id.id)], context=context)[0] or False
    #         res['value'].update({'journal_id': journal_id})
    #     return res
