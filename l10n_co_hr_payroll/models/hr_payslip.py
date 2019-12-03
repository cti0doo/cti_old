# -*- coding:utf-8 -*-


import logging
from datetime import datetime
from datetime import time as datetime_time, timedelta

from dateutil.relativedelta import *
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class HrPayslipWorkedDaysHolidays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    leave_ids = fields.Many2many('hr.leave', string='Holidays')


class HrPayrollStructureExtended(models.Model):
    _inherit = 'hr.payroll.structure'

    name = fields.Char(translate=True)


class HrContributionRegister(models.Model):
    _inherit = 'res.partner'

    name = fields.Char(translate=True)


class HrSalaryRuleExtended(models.Model):
    _inherit = 'hr.salary.rule'

    name = fields.Char(required=True, translate=True)


class HrSalaryRuleCategoryExtended(models.Model):
    _inherit = 'hr.salary.rule.category'

    name = fields.Char(required=True, translate=True)


class HRPayslipExtended(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = []

        structure_ids = contracts.get_all_structures()
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        inputs = self.env['hr.salary.rule'].browse(sorted_rule_ids).mapped('input_ids')

        for contract in contracts:
            for input in inputs:
                input_data = {
                    'name': _(input.name),
                    'code': input.code,
                    'contract_id': contract.id,
                }
                res += [input_data]
        return res

    
    def get_all_structures(self):
        """
        @return: the structures linked to the given contracts, ordered by hierachy (parent=False first,
                 then first level children and so on) and without duplicata
        """
        structures = self.mapped('struct_id')
        if not structures:
            return []
        # YTI TODO return browse records
        return list(set(structures._get_parent_structure().ids))

    
    def compute_sheet(self):
        for payslip in self:
            number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
            # delete old payslip lines
            payslip.line_ids.unlink()
            payslip.details_by_salary_rule.unlink()
            # set the list of contract for which the rules have to be applied
            # if we don't give the contract, then the rules to apply should be for all current contracts of the employee
            contract_ids = payslip.contract_id.ids or \
                           self.get_contract(payslip.employee_id, payslip.date_from, payslip.date_to)
            lines = [(0, 0, line) for line in self._get_payslip_lines(contract_ids, payslip.id)]
            payslip.write({'line_ids': lines, 'number': number})
        return True

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        """
        @param contract: Browse record of contracts
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        res = []
        # fill only if the contract as a working schedule linked
        for contract in contracts.filtered(lambda contract: contract.resource_calendar_id):
            day_from = datetime.combine(fields.Date.from_string(date_from), datetime_time.min)
            day_to = datetime.combine(fields.Date.from_string(date_to), datetime_time.max)

            # compute leave days
            leaves = {}
            #day_leave_intervals = contract.employee_id.iter_leaves(day_from, day_to,
            #                                                       calendar=contract.resource_calendar_id)
            day_leave_intervals = contract.employee_id.list_leaves(day_from, day_to,
                                                                   calendar=contract.resource_calendar_id)
            leave = []
            for day_intervals in day_leave_intervals:
                for interval in day_intervals:
                    holiday = interval[2]['leaves'].holiday_id
                    if interval[0] >= datetime.strptime(date_from, '%Y-%m-%d') and interval[
                        0] <= datetime.strptime(date_to, '%Y-%m-%d'):
                        leave.append(holiday.id)
                        current_leave_struct = leaves.setdefault(holiday.holiday_status_id, {
                            'name': holiday.holiday_status_id.name,
                            'sequence': 5,
                            'code': holiday.holiday_status_id.code,
                            'number_of_days': 0.0,
                            'number_of_hours': 0.0,
                            'contract_id': contract.id,
                            'leave_ids': [(6, 0, leave)]
                        })
                        leave_time = (interval[1] - interval[0]).seconds / 3600
                        current_leave_struct['number_of_hours'] += leave_time
                        work_hours = contract.employee_id.get_day_work_hours_count(interval[0].date(),
                                                                                   calendar=contract.resource_calendar_id)
                        current_leave_struct['number_of_days'] += leave_time / work_hours

            # compute worked days
            # work_data = contract.employee_id.get_work_days_data(day_from, day_to, calendar=contract.resource_calendar_id)
            wdays = (day_to - day_from).days
            if contract.schedule_pay == 'monthly':
                if wdays != 30:
                    wdays = 30
            elif contract.schedule_pay == 'bi-weekly':
                if wdays != 15:
                    wdays = 15
            for leave in leaves.values():
                wdays -= leave.get('number_of_days', 0)
            if contract.date_start > date_from:
                wdays -= (fields.Date.from_string(contract.date_start) - fields.Date.from_string(date_from)).days
                wdays += 1
            if contract.date_end:
                if contract.date_end < date_to:
                    wdays -= (fields.Date.from_string(date_to) - fields.Date.from_string(contract.date_end)).days
                    wdays += 1
            if wdays < 0:
                wdays = 0
            whours = wdays * 8
            attendances = {
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': wdays,
                'number_of_hours': whours,
                'contract_id': contract.id,
            }

            res.append(attendances)
            res.extend(leaves.values())
        return res

    @api.onchange('date_range')
    def onchange_date_range(self):
        self.date_start = self.date_range.date_start
        self.date_end = self.date_range.date_end

    @api.onchange('date_range_fy')
    def _onchange_date_range_fy(self):
        return {
            'domain': {'date_range': [('name', 'like', self.date_range_fy.name), ('type_id.fiscal_year', '=', False)]},
            'value': {'date_range': False, 'date_start': False, 'date_end': False}}

    
    def action_payslip_cancel(self):
        return self.write({'state': 'cancel'})

    
    def action_payslip_advance(self):
        line_ids = []
        credit_account_id, debit_account_id = False, False
        for line in self.line_ids:
            if line.salary_rule_id.code == 'TOT_PAY' and not self.move_advance_id:
                amount = line.total or 0.0
                debit_account_id = self.employee_id.address_home_id.property_account_position_id.map_account(
                    line.salary_rule_id.account_debit).id

                credit_account_id = self.employee_id.address_home_id.property_account_position_id.map_account(
                    self.journal_id.account_advance_id).id

                if debit_account_id:
                    debit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=False),
                        'account_id': debit_account_id,
                        'journal_id': self.journal_id.id,
                        'date': self.date_to,
                        'debit': amount > 0.0 and amount or 0.0,
                        'credit': amount < 0.0 and -amount or 0.0,
                        'analytic_account_id': line.salary_rule_id.analytic_account_id.id,
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(debit_line)

                if credit_account_id:
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': credit_account_id,
                        'journal_id': self.journal_id.id,
                        'date': self.date_to,
                        'debit': amount < 0.0 and -amount or 0.0,
                        'credit': amount > 0.0 and amount or 0.0,
                        'analytic_account_id': line.salary_rule_id.analytic_account_id.id,
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(credit_line)
        if credit_account_id and debit_account_id:
            name = _('Advance Payslip of %s') % (self.employee_id.name)
            move_dict = {
                'narration': name,
                'ref': self.number,
                'journal_id': self.journal_id.id,
                'date': self.date_to,
            }
            move_dict['line_ids'] = line_ids
            move = self.env['account.move'].create(move_dict)
            self.write({'move_advance_id': move.id, 'date': self.date})
            move.post()
            _logger.info(move)
        return True

    
    def action_payslip_done(self):
        precision = self.env['decimal.precision'].precision_get('Payroll')

        for slip in self:
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            date = slip.date or slip.date_to

            name = _('Payslip of %s') % (slip.employee_id.name)
            move_dict = {
                'narration': name,
                'ref': slip.number,
                'journal_id': slip.journal_id.id,
                'date': date,
            }
            for line in slip.line_ids:
                amount = slip.credit_note and -line.total or line.total
                if float_is_zero(amount, precision_digits=precision):
                    continue

                # debit_account_id = line.salary_rule_id.account_debit.id
                # credit_account_id = line.salary_rule_id.account_credit.id
                if line.salary_rule_id.code == 'SALARIO_CONTRATO_ADMIN':
                    _logger.info(line.salary_rule_id.code)
                debit_account_id = self.employee_id.address_home_id.property_account_position_id.map_account(
                    line.salary_rule_id.account_debit).id
                credit_account_id = self.employee_id.address_home_id.property_account_position_id.map_account(
                    line.salary_rule_id.account_credit).id

                if debit_account_id:
                    debit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=False),
                        'account_id': debit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount > 0.0 and amount or 0.0,
                        'credit': amount < 0.0 and -amount or 0.0,
                        'analytic_account_id': line.salary_rule_id.analytic_account_id.id,
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(debit_line)
                    debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

                if credit_account_id:
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount < 0.0 and -amount or 0.0,
                        'credit': amount > 0.0 and amount or 0.0,
                        'analytic_account_id': line.salary_rule_id.analytic_account_id.id,
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(credit_line)
                    credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']

            if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_credit_account_id.id
                if not acc_id:
                    raise UserError(_('The Expense Journal "%s" has not properly configured the Credit Account!') % (
                        slip.journal_id.name))
                adjust_credit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': date,
                    'debit': 0.0,
                    'credit': debit_sum - credit_sum,
                })
                line_ids.append(adjust_credit)

            elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_debit_account_id.id
                if not acc_id:
                    raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (
                        slip.journal_id.name))
                adjust_debit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': date,
                    'debit': credit_sum - debit_sum,
                    'credit': 0.0,
                })
                line_ids.append(adjust_debit)
            move_dict['line_ids'] = line_ids
            move = self.env['account.move'].create(move_dict)
            slip.write({'move_id': move.id, 'date': date})
            move.post()
        # return True #super(HRPayslipExtended, self).action_payslip_done()
        return self.write({'state': 'done'})

    def get_ige(self, payslip):
        # IGE
        # ige_dict = {}
        # for ige_lines in payslip.worked_days_line_ids.filtered(
        #         lambda x: x.holiday_id.holiday_status_id.code == 'INCAPACIDAD_SALUD'):
        #     if ige_lines.holiday_id.date_to > payslip.date_from:
        #         if ige_lines.holiday_id.date_from >= payslip.date_from:  # este periodo
        #             if ige_lines.holiday_id.date_to > payslip.date_to:
        #                 days = (fields.Date.from_string(payslip.date_to) - fields.Date.from_string(
        #                     payslip.date_from) + timedelta(days=1)).days
        #             else:
        #                 days = (fields.Date.from_string(ige_lines.holiday_id.date_to) - fields.Date.from_string(
        #                     ige_lines.holiday_id.date_from) + timedelta(days=1)).days
        #         else:
        #             if ige_lines.holiday_id.date_to > payslip.date_to:
        #                 days = (fields.Date.from_string(payslip.date_to) - fields.Date.from_string(
        #                     payslip.date_from) + timedelta(days=1)).days
        #             else:
        #                 days = (fields.Date.from_string(ige_lines.holiday_id.date_to) - fields.Date.from_string(
        #                     payslip.date_from) + timedelta(days=1)).days
        #             # dias pagados
        #             days += (fields.Date.from_string(payslip.date_from) - fields.Date.from_string(
        #                 ige_lines.holiday_id.date_from)).days
        #     for d in [180, 90, 2, 1]:
        #         if days > d and d == 180:
        #             ige_dict['may180days'] = days - d
        #             for values_line in payslip.date_range_fy.attributes_ids.filtered(lambda x: x.code == '%EPSmay180'):
        #                 ige_dict['may180por'] = values_line.value
        #             days = 180
        #         elif days > d and d == 90:
        #             ige_dict['may90days'] = days - d
        #             for values_line in payslip.date_range_fy.attributes_ids.filtered(lambda x: x.code == '%EPSmay90'):
        #                 ige_dict['may90por'] = values_line.value
        #             days = 90
        #         elif days > d and d == 2:
        #             ige_dict['may2days'] = days - d
        #             for values_line in payslip.date_range_fy.attributes_ids.filtered(lambda x: x.code == '%EPSmay2'):
        #                 ige_dict['may2por'] = values_line.value
        #             days = 2
        #         elif days >= d and d == 1:
        #             ige_dict['may1days'] = days
        #             for values_line in payslip.date_range_fy.attributes_ids.filtered(lambda x: x.code == '%EPSmay1'):
        #                 ige_dict['may1por'] = values_line.value
        return 0  # ige_dict

    @api.model
    def _get_payslip_lines(self, contract_ids, payslip_id):
        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict, category.parent_id, amount)
            localdict['categories'].dict[category.code] = category.code in localdict['categories'].dict and \
                                                          localdict['categories'].dict[category.code] + amount or amount
            return localdict

        class BrowsableObject(object):
            def __init__(self, employee_id, dict, env):
                self.employee_id = employee_id
                self.dict = dict
                self.env = env

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class InputLine(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                        SELECT sum(amount) as sum
                        FROM hr_payslip as hp, hr_payslip_input as pi
                        WHERE hp.employee_id = %s AND hp.state = 'done'
                        AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                                    (self.employee_id, from_date, to_date, code))
                return self.env.cr.fetchone()[0] or 0.0

        class WorkedDays(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                        SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours
                        FROM hr_payslip as hp, hr_payslip_worked_days as pi
                        WHERE hp.employee_id = %s AND hp.state = 'done'
                        AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                                    (self.employee_id, from_date, to_date, code))
                return self.env.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)
                                FROM hr_payslip as hp, hr_payslip_line as pl
                                WHERE hp.employee_id = %s AND hp.state = 'done'
                                AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s""",
                                    (self.employee_id, from_date, to_date, code))
                res = self.env.cr.fetchone()
                return res and res[0] or 0.0

        # we keep a dict with the result because a value can be overwritten by another rule with the same code
        result_dict = {}
        rules_dict = {}
        values_dict = {}
        ige_dict = {}
        worked_days_dict = {}
        inputs_dict = {}
        blacklist = []
        payslip = self.env['hr.payslip'].browse(payslip_id)
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days_dict[worked_days_line.code] = worked_days_line
        for input_line in payslip.input_line_ids:
            inputs_dict[input_line.code] = input_line
        for values_line in payslip.date_range_fy.attributes_ids:
            values_dict[values_line.code] = values_line

        categories = BrowsableObject(payslip.employee_id.id, {}, self.env)
        inputs = InputLine(payslip.employee_id.id, inputs_dict, self.env)
        worked_days = WorkedDays(payslip.employee_id.id, worked_days_dict, self.env)
        payslips = Payslips(payslip.employee_id.id, payslip, self.env)
        rules = BrowsableObject(payslip.employee_id.id, rules_dict, self.env)
        values = BrowsableObject(payslip.employee_id.id, values_dict, self.env)
        get_ige = BrowsableObject(payslip.employee_id.id, self.get_ige(payslip), self.env)

        baselocaldict = {'categories': categories, 'rules': rules, 'payslip': payslips, 'worked_days': worked_days,
                         'inputs': inputs, 'values': values, 'get_ige': get_ige, 'datetime': datetime,
                         'timedelta': timedelta, 'relativedelta': relativedelta}
        # get the ids of the structures on the contracts and their parent id as well
        contracts = self.env['hr.contract'].browse(contract_ids)
        structure_ids = self.get_all_structures()
        # structure_ids = contracts.get_all_structures()
        # get the rules of the structure and thier children
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        # run the rules by sequence
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        sorted_rules = self.env['hr.salary.rule'].browse(sorted_rule_ids)

        for contract in contracts:
            employee = contract.employee_id
            localdict = dict(baselocaldict, employee=employee, contract=contract)
            for rule in sorted_rules:
                key = rule.code + '-' + str(contract.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                localdict['result_rate'] = 100
                # check if the rule can be applied
                if rule._satisfy_condition(localdict) and rule.id not in blacklist:
                    # compute the amount of the rule
                    amount, qty, rate = rule._compute_rule(localdict)
                    # check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                    # set/overwrite the amount computed for this rule in the localdict
                    tot_rule = amount * qty * rate / 100.0
                    localdict[rule.code] = tot_rule
                    rules_dict[rule.code] = rule
                    # sum the amount for its salary category
                    localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
                    # create/overwrite the rule in the temporary results
                    payslip_run_id = False
                    if payslips.payslip_run_id:
                        payslip_run_id = payslips.payslip_run_id.id
                    result_dict[key] = {
                        'salary_rule_id': rule.id,
                        'contract_id': contract.id,
                        'name': rule.name,
                        'code': rule.code,
                        'category_id': rule.category_id.id,
                        'sequence': rule.sequence,
                        'appears_on_payslip': rule.appears_on_payslip,
                        'condition_select': rule.condition_select,
                        'condition_python': rule.condition_python,
                        'condition_range': rule.condition_range,
                        'condition_range_min': rule.condition_range_min,
                        'condition_range_max': rule.condition_range_max,
                        'amount_select': rule.amount_select,
                        'amount_fix': rule.amount_fix,
                        'amount_python_compute': rule.amount_python_compute,
                        'amount_percentage': rule.amount_percentage,
                        'amount_percentage_base': rule.amount_percentage_base,
                        'register_id': rule.register_id.id,
                        'amount': amount,
                        'employee_id': contract.employee_id.id,
                        'quantity': qty,
                        'rate': rate,
                        'payslip_run_id': payslip_run_id,
                        'date_from': payslips.date_from,
                        'date_to': payslips.date_to,
                    }
                else:
                    # blacklist this rule and its children
                    blacklist += [id for id, seq in rule._recursive_search_of_rules()]

        return list(result_dict.values())

    def _get_domain_contract(self):
        return [('date_end', '>=', self.date_from)]

    date_range_fy = fields.Many2one('date.range', 'Date range fiscal year', required=True,
                                    domain="[('type_id.fiscal_year','=',True)]")
    date_range = fields.Many2one('date.range', 'Date range', required=True, domain=_onchange_date_range_fy)
    contract_id = fields.Many2one('hr.contract', string='Contract', readonly=True,
                                  states={'draft': [('readonly', False)]}, domain=_get_domain_contract)
    line_ids = fields.One2many('hr.payslip.line', 'slip_id', string='Payslip Lines', readonly=True,
                               states={'draft': [('readonly', False)]},
                               domain=[('appears_on_payslip', '=', True)])
    details_by_salary_rule = fields.One2many('hr.payslip.line', 'slip_id',
                                             string='Details by Salary Rule', readonly=True,
                                             states={'draft': [('readonly', False)]})
    move_advance_id = fields.Many2one('account.move', string='Advance move')


class HRPayslipExtendedRun(models.Model):
    _inherit = 'hr.payslip.run'

    @api.onchange('date_range')
    def onchange_date_range(self):
        self.date_start = self.date_range.date_start
        self.date_end = self.date_range.date_end

    @api.onchange('date_range_fy')
    def _onchange_date_range_fy(self):
        return {
            'domain': {'date_range': [('name', 'like', self.date_range_fy.name), ('type_id.fiscal_year', '=', False)]},
            'value': {'date_range': False, 'date_start': False, 'date_end': False}}

    date_range_fy = fields.Many2one('date.range', 'Date range fiscal year', required=True,
                                    domain="[('type_id.fiscal_year','=',True)]")
    date_range = fields.Many2one('date.range', 'Date range', required=True, domain=_onchange_date_range_fy)
    struct_id = fields.Many2one('hr.payroll.structure', string='Salary Structure', required=False)

    
    def compute_payslips(self):
        for pay in self.slip_ids:
            pay.compute_sheet()
        return True

    
    def action_payslip_advance(self):
        for payslip in self.slip_ids:
            payslip.action_payslip_advance()
        return True


class HrPayslipEmployeesExtended(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    
    def compute_sheet(self):
        payslips = self.env['hr.payslip']
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        if active_id:
            [run_data] = self.env['hr.payslip.run'].browse(active_id).read(
                ['date_start', 'date_end', 'credit_note', 'date_range', 'date_range_fy', 'struct_id'])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        date_range = run_data.get('date_range')[0]
        date_range_fy = run_data.get('date_range_fy')[0]
        struct_id = False
        if run_data.get('struct_id'):
            struct_id = run_data.get('struct_id')[0]
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        c = 0
        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)
            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': slip_data['value'].get('struct_id'),
                'contract_id': slip_data['value'].get('contract_id'),
                'payslip_run_id': active_id,
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
                'date_range': date_range,
                'date_from': from_date,
                'date_to': to_date,
                'date_range': date_range,
                'date_range_fy': date_range_fy,
                'credit_note': run_data.get('credit_note'),
                'struct_id': struct_id or slip_data.get('value').get('struct_id', False),
            }
            payslips += self.env['hr.payslip'].create(res)
            c+=1
            _logger.info(c)
        payslips.compute_sheet()
        return {'type': 'ir.actions.act_window_close'}


class HrPayslipLineExtended(models.Model):
    _inherit = 'hr.payslip.line'

    payslip_run_id = fields.Many2one('hr.payslip.run', string='Pay Slip Run', required=False)
    date_from = fields.Date(string='Date from')
    date_to = fields.Date(string='Date to')
