# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ciiu(models.Model):
    _name = 'account.ciiu'
    _description = 'Account CIIU'

    name = fields.Char(string='Code', required=True)
    description = fields.Char(string='Description', required=True)
    line_ids = fields.One2many('account.ciiu.lines', 'ciiu_id', string='lines')
    industry_id = fields.Many2one('res.partner.industry', string='Industry', required=False, index=True)

    
    def name_get(self):
        result = []
        for record in self:
            if record.name and record.description:
                result.append((record.id, record.name + ' - ' + record.description))
            if record.name and not record.description:
                result.append((record.id, record.name))
        return result


class ciiuLines(models.Model):
    _name = 'account.ciiu.lines'
    _description = 'Account CIIU Lines'

    tax_id = fields.Many2one('account.tax', string='Tax', required=False)
    city_id = fields.Many2one('res.country.state.city', string='City', required=False)
    ciiu_id = fields.Many2one('account.ciiu', string='CIIU', required=False)
    industry_id = fields.Many2one('res.partner.industry', string='Industry', required=False)

class productCategory(models.Model):
    _inherit = 'product.category'

    ciiu_id = fields.Many2one('account.ciiu', string='CIIU')