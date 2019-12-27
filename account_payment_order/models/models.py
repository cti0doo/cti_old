# -*- coding: utf-8 -*-

import base64
import logging

from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountPaymentOrder(models.Model):
    _name = 'account.payment.order'
    _description = 'Account Payment Order'

    
    @api.depends('payment_ids')
    def _get_total(self):
        for pay in self.payment_ids:
            self.amount += pay.amount

    name = fields.Char(string='Name', required=True, index=True)
    date = fields.Date(string='Date', required=True, index=True)
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('cancel', 'Cancel')],
                             string='State', index=True, default='draft')
    type = fields.Many2one('account.payment.order.type', string='Type', index=True, required=False)
    description = fields.Text(string='Description')
    res_bank_id = fields.Many2one(
        'res.partner.bank', string='Bank account', index=True, required=True,
        domain=lambda self: [('partner_id', '=', self.env.user.company_id.partner_id.id)]
    )
    amount = fields.Float(compute='_get_total', string='Amount', required=True,
                          default=0.0, readonly=True)
    move_id = fields.Many2one('account.move', string='Account move', index=True)
    journal_id = fields.Many2one('account.journal', string='Journal', required=True)
    payment_ids = fields.One2many('account.payment', 'order_id', string='Payments', index=True)
    bank_ids = fields.Many2many('res.bank', string='Suggested banks')
    file = fields.Binary(string='Bank file', readonly=True)
    date_file = fields.Date(string='Fields date')
    filename = fields.Char(string='Filename')

    # TODO: Verificar si se usa o eliminar
    def _get_sequence(self):
        # TODO: Usar libraría datetime en vez de str
        return self.search_count([('date_file', '=', str(datetime.now())[0:10])])

    def _set_format(self, function, conf):
        result = ''
        if conf.type_format == 'date':
            result = "datetime.strptime({}, '%Y-%M-%d').strftime('{}')".format(function,
                                                                               conf.format)
        # TODO: Tipo moneda que se muestra como fecha?
        elif conf.type_format == 'money':
            result = "datetime.strptime({}, '%Y-%M-%d').strftime('{}')".format(function,
                                                                               conf.format)
        return result

    def _get_line(self, line, configuration):
        text = ''
        for conf in configuration:
            function = conf.function or ''
            ch = ' ' if conf.character == '' or not conf.character else conf.character
            text2 = ''
            if conf.type == 'p':
                get_sequence = self._get_sequence()
                try:
                    # set format
                    if conf.type_format and conf.format:
                        function = self.set_format(function, conf)
                    function = function.replace('payment_line.', 'line.') if 'payment_line' in function else function
                    function = function.replace('payment.', 'self.') if 'payment' in function else function
                    _logger.info(function)
                    text2 = str(eval(function))
                except AttributeError:
                    text2 = ''
            else:
                text2 = str(function)
            # adjust
            text2 = text2.ljust(conf.size, ch) if conf.adjust == 'l' else text2
            text2 = text2.rjust(conf.size, ch) if conf.adjust == 'r' else text2
            text2 = text2[:conf.size + 1]
            text += text2
        return text

    def _get_footer(self):
        text = ''
        for conf in self.res_bank_id.bank_id.footer_ids:
            function = conf.function or ''
            ch = ' ' if conf.character == '' or not conf.character else conf.character
            text2 = ''
            if conf.type == 'p':
                try:
                    # set format
                    if conf.type_format and conf.format:
                        function = self.set_format(function, conf)
                    function = function.replace('payment_line.', 'line.') if 'payment_line' in function else function
                    function = function.replace('payment.', 'self.') if 'payment' in function else function
                    text2 = str(eval(function))
                except AttributeError:
                    text2 = ''
            else:
                text2 = str(function)
            # adjust
            text2 = text2.ljust(conf.size, ch) if conf.adjust == 'l' else text2
            text2 = text2.rjust(conf.size, ch) if conf.adjust == 'r' else text2
            text2 = text2[:conf.size + 1]
            text += text2
        return text

    def create_file(self):
        text_complete = []
        # get header
        text_complete.append(self._get_line(False, self.res_bank_id.bank_id.header_ids))
        # get lines
        for payment in self.payment_ids:
            if payment.amount > 0:
                if not self.res_bank_id.bank_id.conf_ids:
                    raise UserError(
                        _('the bank of the account {} has no configuration for bank file').format(
                            self.res_bank_id.acc_number
                        )
                    )
                text_complete.append(self._get_line(payment, self.res_bank_id.bank_id.conf_ids))
        if self.res_bank_id.bank_id.footer_ids:
            text_complete.append(self._get_footer())
        path = "/tmp/bank_file.txt"
        with open(path, "w+") as f:
            for txt in text_complete:
                f.write(txt + '\n')
        self.write({'filename': 'bank_file_' + self.name + '.txt', 'date_file': datetime.now(),
                    'file': base64.b64encode(open(path, 'rb').read())})
        return True

    def get_pays(self):
        return self.env['ir.actions.act_window'].for_xml_id(
            module='account_payment_order', xml_id='action_account_payment_order_wizard')

    def posted(self):
        self.state = 'posted'
        for pay in self.payment_ids:
            pay.post()

    def to_draft(self):
        self.state = 'draft'
        for pay in self.payment_ids:
            pay.action_draft()

    def cancel(self):
        self.state = 'cancel'
        for pay in self.payment_ids:
            pay.cancel()


class AccountPaymentExtended(models.Model):
    _inherit = 'account.payment'

    @api.onchange('partner_id')
    def _onchange_partner(self):
        bank_id = False
        for bank in self.partner_id.bank_ids:
            bank_id = bank.id
            break
        return {
            'domain': {'res_bank_id': [('partner_id', '=', self.partner_id.id)]},
            'value': {'res_bank_id': bank_id}
        }

    order_id = fields.Many2one('account.payment.order', string='Order payment', index=True)
    res_bank_id = fields.Many2one('res.partner.bank', string='Bank account', index=True)


class AccountPaymentOrderWizard(models.TransientModel):
    _name = 'account.payment.order.wizard'
    _description = 'Account Payment Order Wizard'

    partner_id = fields.Many2one('res.partner', string='Partner', required=False,
                                 index=True, domain=[('supplier', '=', True)])
    journal_id = fields.Many2one('account.journal', string='Account journal',
                                 required=False, index=True)
    date_maturity = fields.Date(string='Date maturity', required=False, index=True)
    move_ids = fields.Many2many('account.move.line', string='Moves')

    @api.onchange('partner_id', 'journal_id', 'date_maturity')
    def _get_moves(self):
        if self.partner_id or self.journal_id or self.date_maturity:
            condition = [
                ('account_id.user_type_id.type', '=', 'payable'),
                ('amount_residual', '!=', 0),
                ('parent_state', '=', 'posted')
            ]
            order = self.env['account.payment.order'].browse(self.env.context.get('active_id'))
            if order.bank_ids:
                condition.append(('partner_id.bank_ids.bank_id.id', 'in', order.bank_ids.ids))
            if self.partner_id:
                condition.append(('partner_id', '=', self.partner_id.id))
            if self.journal_id:
                condition.append(('journal_id', '=', self.journal_id.id))
            if self.date_maturity:
                condition.append(('date_maturity', '<=', self.date_maturity))
            # Get account payable
            payment_type = order.type
            if payment_type.account_ids:
                self.env.cr.execute(
                    ''' SELECT id FROM account_account
                            WHERE id in ({})'''.format(
                        ','.join([str(x.id) for x in payment_type.account_ids])))
                account_ids = self.env.cr.dictfetchall()
                condition.append(('account_id', 'in', [x.get('id', None) for x in account_ids]))
            self.move_ids = self.env['account.move.line'].search(condition)

    @api.model
    def create(self, vals):
        vals['move_ids'] = [tuple(vals['move_ids'][0])]
        return super(AccountPaymentOrderWizard, self).create(vals)

    def _prepare_payments(self, data):
        new_data = {}
        order = self.env['account.payment.order'].browse(self.env.context.get('active_id'))
        banks = [x.id for x in order.bank_ids]
        for move in data:
            res_bank_id = self.env['res.partner.bank'].search(
                [('partner_id', '=', move.partner_id.id), ('bank_id', 'in', banks)], limit=1)
            amount = abs(move.amount_residual)
            if move.partner_id.id not in new_data.keys():
                new_data[move.partner_id.id] = {
                    'amount': amount, 'partner_type': 'supplier',
                    'partner_id': move.partner_id.id, 'payment_type': 'outbound',
                    'journal_id': order.journal_id.id, 'payment_date': order.date,
                    'communication': order.description, 'order_id': order.id,
                    'res_bank_id': res_bank_id.id,
                    'invoice_ids': [(6, 0, move.invoice_id.ids)],
                    'payment_method_id': self.env.ref(
                        'account.account_payment_method_manual_out').id
                }
            else:
                nd = move.invoice_id.ids
                for x in new_data[move.partner_id.id].get('invoice_ids'):
                    nd += x[2]
                new_data[move.partner_id.id].update(
                    {'invoice_ids': [(6, 0, nd)],
                     'amount': new_data.get(move.partner_id.id).get('amount', 0.0) + amount})
        return new_data

    def add_move(self):
        data = self._prepare_payments(self.move_ids)
        for pay in data:
            pay = self.env['account.payment'].create(data.get(pay))
            pay.write(pay._onchange_partner().get('value', {}))
        return True


class AccountPaymentOrderType(models.Model):
    _name = 'account.payment.order.type'
    _description = 'Account Payment Order Type'

    def _get_domain(self):
        user_type_id = self.env.ref('account.data_account_type_payable').id
        return [('user_type_id', '=', user_type_id)]

    name = fields.Char(string='Name', index=True)
    account_ids = fields.Many2many('account.account', string='Account',
                                   index=True, domain=_get_domain, required=True)
