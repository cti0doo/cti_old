# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    @api.onchange('state_id')
    def cityfilter(self):
        return {'domain': {'cities': [('state_id', '=?', self.state_id.id)]}}

    cities = fields.Many2one('l10n_co_cities.city', context="{'default_state_id': state_id}")

    @api.onchange('parent_id')
    def onchange_parent_id_cities(self):
        self.cities = self.parent_id.cities

    @api.onchange('country_id')
    def update_country(self):
        if not self.country_id.name:
            self.cities = None
            self.state_id = None

    @api.onchange('state_id')
    def update_state(self):
        if not self.state_id.name:
            self.cities = None

    @api.onchange('cities')
    def update_cities(self):
        if not self.cities.city_name:
            self.country_id = None
        self.state_id = self.cities.state_id
