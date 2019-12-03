# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ImportExportMassiveFields(models.Model):
    """Creating Import & Export Massive Filter model."""

    _name = 'ie.massive.filter'
    _description = 'IE Massive Filter'

    model_id = fields.Many2one('ir.model', string='Model', required=True)
    filter = fields.Char(string='Filter', required=True)

    @api.onchange('model_id')
    def onchange_model(self):
        self.filter = '''[('name','=','{}')]'''

    _sql_constraints = [
        ('model_uniq', 'unique (model_id)',
         'Model already exists')
    ]
