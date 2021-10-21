# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResMachine(models.Model):
    _name = 'res.machine'
    _description = 'Machine'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', required=True)
    code = fields.Char('Internal Ref')
    description = fields.Char('description')
    image = fields.Binary(string="Image", )
    partner_id = fields.Many2one('res.partner', )
