# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ResMachine(models.Model):
    _name = 'res.machine'
    _description = 'Machine'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Plate number', required=True, compute="_get_license_number")
    code = fields.Char('Chase Number', required=True, )
    engine_number = fields.Char('Engine Number', required=True, )
    machine_colour = fields.Char(string="Colour", required=False, )
    model_id = fields.Many2one('product.model')
    brand_id = fields.Many2one('product.brand', string='Brand', help='Select a brand for this Machine')
    production_year = fields.Char(string="Production Year", size=4, required=True)
    capacity = fields.Integer(string="Capacity", required=False, )
    transmission = fields.Selection([('manual', 'Manual'), ('automatic', 'Automatic')], 'Transmission',
                                    help='Transmission Used by the vehicle')
    fuel_type = fields.Selection([
        ('gasoline', 'Gasoline'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid')
    ], 'Fuel Type', help='Fuel Used by the vehicle')

    image = fields.Binary(string="Image", )
    partner_id = fields.Many2one('res.partner', string="Owner", required=True)
    notes = fields.Text(string="Notes", required=False, )

    code1 = fields.Char(string="code1", required=True, size=1)
    code2 = fields.Char(string="code2", required=True, size=1)
    code3 = fields.Char(string="code3", required=True, size=1)
    code4 = fields.Char(string="code4", required=True, size=1)
    code5 = fields.Char(string="code5", required=True, size=1)
    code6 = fields.Char(string="code6", required=True, size=1)

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

    def name_get(self):
        res = []
        for rec in self:
            name = "[%s] - %s" % (rec.name, rec.code)
            res += [(rec.id, name)]
        return res

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if operator in ('ilike', 'like', '=', '=like', '=ilike'):
            args = expression.AND([
                args or [],
                ['|', ('name', operator, name), ('code', operator, name)]
            ])
        return super(ResMachine, self)._name_search(name, args=args, operator=operator, limit=limit,
                                                    name_get_uid=name_get_uid)
