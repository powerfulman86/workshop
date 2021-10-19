from odoo import fields, models, api


class ResMachine(models.Model):
    _inherit = 'res.partner'
    _description = 'Machine'

    machine_ids = fields.One2many( comodel_name='res.machine',  inverse_name='partner_id',)