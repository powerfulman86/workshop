# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError


class ResMachine(models.Model):
    _name = 'res.machine'
    _description = 'Machine'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char('Name', required=True, compute="_get_license_number")
    code = fields.Char('Chase Number')
    model_id = fields.Many2one('product.model')
    production_year = fields.Integer(string="Production Year", required=False, digits=4)
    capacity = fields.Integer(string="Capacity", required=False, )

    image = fields.Binary(string="Image", )
    partner_id = fields.Many2one('res.partner', )
    notes = fields.Text(string="Notes", required=False, )

    code1 = fields.Char(string="code1", required=False, size=1)
    code2 = fields.Char(string="code2", required=False, size=1)
    code3 = fields.Char(string="code3", required=False, size=1)
    code4 = fields.Char(string="code4", required=False, size=1)
    code5 = fields.Char(string="code5", required=False, size=1)
    code6 = fields.Char(string="code6", required=False, size=1)

    @api.depends('code1', 'code2', 'code3', 'code4', 'code5', 'code6')
    def _get_license_number(self):
        for rec in self:
            rec.name = (rec.code1 or '') + (rec.code2 or '') + (rec.code3 or '') + (rec.code4 or '') + (
                    rec.code5 or '') + (rec.code6 or '')

    _sql_constraints = [
        (
            "machine_name_unique",
            "unique(name)",
            "Machine Name must be unique across the database!",
        )
    ]

    @api.constrains('production_year')
    def _check_production_year(self):
        for rec in self:
            if not rec.production_year.isdigit():
                raise ValidationError(_("Production Year Must Be Digits"))
