# -*- coding: utf-8 -*-

from odoo import models, fields


class resPartnerCIIU(models.Model):
    _inherit = 'res.partner'

    ciiu_id = fields.Many2one('account.ciiu', string='CIIU')
    retention_apply = fields.Selection([('na', 'Not apply'), ('fa', 'Force apply'), ('ta', 'Apply')],
                                       string='Retention apply?', default='ta', required=True)


    customer = fields.Boolean(string='Is a Customer', default=True,
                               help="Check this box if this contact is a customer. It can be selected in sales orders.")
    supplier = fields.Boolean(string='Is a Vendor',
                               help="Check this box if this contact is a vendor. It can be selected in purchase orders.")

class resPartnerApply(models.Model):
    _inherit = 'res.partner.industry'

    ciiu_ids = fields.One2many('account.ciiu', 'industry_id', string='CIIU')
    line_ids = fields.One2many('account.ciiu.lines', 'industry_id', string='lines')
    default_tax_id = fields.Many2one('account.tax', string='Default Tax', required=False)
    type = fields.Selection([('mrp', 'Producer'), ('srv', 'Services'), ('mrk', 'Marketer')],
                            string='Type', default='mrk', required=True)
