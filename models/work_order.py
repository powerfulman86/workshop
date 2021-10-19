from odoo import fields, models, api


class WorkOrder(models.Model):
    _name = 'work.order'
    _description = 'Work Order'

    name = fields.Char('Name')
    stage_id = fields.Many2one(comodel_name='work.order.stage')


class WorkOrder(models.Model):
    _name = 'work.order.stage'
    _description = 'Work Order'

    name = fields.Char('Name')
    active = fields.Boolean(string='Active', default=True)
