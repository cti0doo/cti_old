# -*- coding: utf-8 -*-

from odoo import models, api, fields
import logging
import json
import os

_logger = logging.getLogger(__name__)


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    state_code = fields.Char()

    fe_habilitada_compania = fields.Boolean(
        string='FE Compañía',
        compute='compute_fe_habilitada_compania',
        store=False,
        copy=False
    )

    @api.depends('state_code')
    def compute_fe_habilitada_compania(self):
        for record in self:
            record.fe_habilitada_compania = self.env.company.fe_habilitar_facturacion

    def init(self):
        _logger.warning('Entrando al init *****')
        try:
            path = 'data/states.json'
            root_directory = os.getcwd()
            dir = os.path.dirname(__file__)
            if root_directory != '/':
                file_dir = dir.replace(root_directory, '').replace('models/states', '')
            else:
                file_dir = dir.replace('models/states', '')
            route = file_dir + path
            with open(route[1:]) as file:
                data = json.load(file)

            for state in data['state']:
                country = self.env['res.country'].search(
                    [('code', '=', 'CO')])

                data = self.env['res.country.state'].search(
                    [('code', '=', state['codigo_iso']), ('country_id', '=', country.id)])

                if data.name:
                    data.write({'state_code': state['state_code']})

            file.close()

        except Exception as e:
            _logger.error('Error actualizando los datos de res_country_state - {}'.format(e))
