from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class DateRangeAttribute(models.Model):
    _name = 'date.range.attribute'
    _description = 'Date Range Attribute'

    def _default_company(self):
        return self.env.company

    company_id = fields.Many2one(comodel_name='res.company', string='Company',
                                 index=True, default=_default_company)
    name = fields.Char(string='Name', required=True,
                       help='The name that will be used on the attribute')
    description = fields.Char(string='Description', required=True,
                              help='The description that will be used on the attribute')
    value = fields.Char(string='Value', required=True,
                        help="The attribute's value", )
    range_id = fields.Many2one('date.range', string='Date Range', ondelete='cascade')



class DateRange(models.Model):
    _inherit = 'date.range'

    attributes_ids = fields.One2many('date.range.attribute', 'range_id', string='Range Attributes')

    @api.onchange('company_id', 'type_id')
    def _onchange_company_id(self):
        if self.company_id and self.type_id.company_id and \
                self.type_id.company_id != self.company_id:
            self._cache.update(
                self._convert_to_cache({'type_id': False}, update=True))
            

class DateRangeType(models.Model):
    _inherit = 'date.range.type'

    fiscal_year = fields.Boolean(string='Is fiscal year?', default=False)

    def unlink(self):
        """
        Cannot delete a date_range_type with 'fiscal_year' flag = True
        """
        for rec in self:
            if rec.fiscal_year:
                raise ValidationError(
                    _('You cannot delete a date range type with '
                      'flag "fiscal_year"')
                )
            else:
                super(DateRangeType, rec).unlink()