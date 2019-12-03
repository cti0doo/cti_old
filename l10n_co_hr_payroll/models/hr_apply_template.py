# -*- coding: utf-8 -*-

import logging

from odoo.exceptions import UserError

from odoo import models, api

_logger = logging.getLogger(__name__)


class HRApplyTemplate(models.TransientModel):
    _inherit = 'res.config.settings'

    def create_translation(self, model, register, reg):
        translations = self.env['ir.translation'].search(
            [('name', '=', model + ',name'), ('res_id', '=', register.id)])
        for translate in translations:
            self.env['ir.translation'].create({'display_name': translate.display_name,
                                               'lang': translate.lang,
                                               'module': translate.module,
                                               'name': translate.name.replace('.template', ''),
                                               'res_id': reg.id,
                                               'source': translate.source,
                                               'src': translate.src,
                                               'state': translate.state,
                                               'type': translate.type,
                                               'value': translate.value,
                                               })
        return True

    
    def apply_hr_template(self):
        _logger.info('INIT method apply_hr_template')
        if not self.env.user.company_id.chart_template_id:
            raise UserError('You must define a chart of accounts for the company')
        # hr.contribution.register.template
        #_logger.info('hr.contribution.register.template')
        # hcrt = self.env['hr.contribution.register.template'].search([])
        # for register in hcrt:
        #     reg = self.env['hr.contribution.register'].create({'name': register.name,
        #                                                        'company_id': self.env.user.company_id.id,
        #                                                        'note': register.note})
        #     self.create_translation('hr.contribution.register.template', register, reg)

        # hr.salary.rule.category.template
        _logger.info('hr.salary.rule.category.template')
        hsrct = self.env['hr.salary.rule.category.template'].search([])
        for register in hsrct:
            reg = self.env['hr.salary.rule.category'].create({'code': register.code,
                                                              'name': register.name,
                                                              'company_id': self.env.user.company_id.id,
                                                              'note': register.note,
                                                              'parent_id': register.parent_id.id})
            self.create_translation('hr.salary.rule.category.template', register, reg)

        # hr.salary.rule.template
        _logger.info('hr.salary.rule.template')
        hsrt = self.env['hr.salary.rule.template'].search(
            [('chart_template_id', '=', self.env.user.company_id.chart_template_id.id)])
        for register in hsrt:
            register_contribution = self.env['res.partner'].search(
                [('name', '=', register.name), ('company_id', '=', self.env.user.company_id.id)])
            parent = self.env['hr.salary.rule'].search(
                [('code', '=', register.parent_rule_id.code), ('company_id', '=', self.env.user.company_id.id)])
            category = self.env['hr.salary.rule.category'].search(
                [('name', '=', register.category_id.name), ('company_id', '=', self.env.user.company_id.id)])
            _logger.info(category)
            _logger.info(register.category_id.name)
            account_credit = self.env['account.account'].search([('code', '=', register.account_credit.code or False),
                                                                 ('company_id', '=', self.env.user.company_id.id)])
            account_debit = self.env['account.account'].search(
                [('code', '=', register.account_debit.code or False), ('company_id', '=', self.env.user.company_id.id)])

            reg = self.env['hr.salary.rule'].create({'parent_rule_id': parent.id,
                                                     'code': register.code,
                                                     'company_id': self.env.user.company_id.id,
                                                     'sequence': register.sequence,
                                                     'appears_on_payslip': register.appears_on_payslip,
                                                     'condition_range': register.condition_range,
                                                     'amount_fix': register.amount_fix,
                                                     'note': register.note,
                                                     'amount_percentage': register.amount_percentage,
                                                     'condition_range_min': register.condition_range_min,
                                                     'condition_select': register.condition_select,
                                                     'amount_percentage_base': register.amount_percentage_base,
                                                     'register_id': register_contribution.id,
                                                     'amount_select': register.amount_select,
                                                     'active': register.active,
                                                     'condition_range_max': register.condition_range_max,
                                                     'name': register.name,
                                                     'condition_python': register.condition_python,
                                                     'amount_python_compute': register.amount_python_compute,
                                                     'category_id': category.id,
                                                     'account_credit': account_credit.id,
                                                     'account_debit': account_debit.id,
                                                     # 'account_tax_id':account_tax_id.id,
                                                     })
            self.create_translation('hr.salary.rule.template', register, reg)

        # hr.rule.input.template
        _logger.info('hr.rule.input.template')
        hrit = self.env['hr.rule.input.template'].search(
            [('chart_template_id', '=', self.env.user.company_id.chart_template_id.id)])
        for register in hrit:
            rule_id = self.env['hr.salary.rule'].search(
                [('code', '=', register.input_id.code), ('company_id', '=', self.env.user.company_id.id)])
            reg = self.env['hr.rule.input'].create({'input_id': rule_id.id,
                                                    'code': register.code,
                                                    'name': register.name,
                                                    'assing_value': register.assing_value})
            self.create_translation('hr.rule.input.template', register, reg)

        # hr.payroll.structure.template
        _logger.info('hr.payroll.structure.template')
        structure_template = self.env['hr.payroll.structure.template'].search(
            [('chart_template_id', '=', self.env.user.company_id.chart_template_id.id)])
        for register in structure_template:
            structure_id = self.env['hr.payroll.structure'].search(
                [('code', '=', register.parent_id.code), ('company_id', '=', self.env.user.company_id.id)])

            rule_id = []
            for rules in register.rule_ids:
                _logger.info(rules.code)
                rule_id.append(self.env['hr.salary.rule'].search(
                    [('code', '=', rules.code), ('company_id', '=', self.env.user.company_id.id)]).id)

            reg = self.env['hr.payroll.structure'].create({'parent_id': structure_id,
                                                           'code': register.code,
                                                           'name': register.name,
                                                           'note': register.note,
                                                           'note': register.note,
                                                           'rule_ids': [(6, 0, rule_id)],
                                                           })
            self.create_translation('hr.payroll.structure.template', register, reg)
        _logger.info('END method apply_hr_template')
        return True
