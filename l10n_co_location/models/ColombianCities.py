# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CountryStateCity(models.Model):
    _name = 'res.country.state.city'
    _description = 'Cities of states'

    state_id = fields.Many2one('res.country.state', string='State', required=True)
    name = fields.Char(required=True)
    code = fields.Char(string='City code', required=True)


class Partner(models.Model):
    _inherit = 'res.partner'

    city_id = fields.Many2one('res.country.state.city', string='City Ref', ondelete='restrict', required=False)

    
    @api.onchange('city_id')
    def onchange_city(self):
        return {'value': {'state_id': self.city_id.state_id.id,
                          'city': self.city_id.name,
                          'country_id': self.city_id.state_id.country_id.id}}


class Bank(models.Model):
    _inherit = 'res.bank'

    city_id = fields.Many2one('res.country.state.city', string='City Ref', ondelete='restrict')

    
    @api.onchange('city_id')
    def onchange_city(self):
        return {'value': {'state': self.city_id.state_id.id,
                          'city': self.city_id.name,
                          'country_id': self.city_id.state_id.country_id.id}}


class Company(models.Model):
    _inherit = 'res.company'

    city_id = fields.Many2one('res.country.state.city', string='City Ref', ondelete='restrict')

    
    @api.onchange('city_id')
    def onchange_city(self):
        return {'value': {'state_id': self.city_id.state_id.id,
                          'city': self.city_id.name,
                          'country_id': self.city_id.state_id.country_id.id}}
