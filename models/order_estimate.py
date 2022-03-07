# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

AVAILABLE_STATE = [
    ('draft', 'Draft'),
    ('close', 'Closed'),
]


class WorkshopEstimate(models.Model):
    _name = 'workshop.estimate'
    _description = 'Work-Order Estimate'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = "id desc"

    name = fields.Char('Name')
    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True, readonly=True,
                                 states={'draft': [('readonly', False)]}, required=True)
    machine_id = fields.Many2one('res.machine', string='Machine', tracking=True, readonly=True,
                                 states={'draft': [('readonly', False)]}, required=True,
                                 domain="[('partner_id', '=', partner_id)]")
    user_id = fields.Many2one('res.users', string='Assigned to', default=lambda self: self.env.uid, index=True,
                              readonly=True, states={'draft': [('readonly', False)]}, )
    description = fields.Html('Description', help='Description')
    state = fields.Selection(AVAILABLE_STATE, string='State', index=True, default=AVAILABLE_STATE[0][0],
                             tracking=True, )

    order_date = fields.Datetime(string='Inspect Date', required=True, index=True, copy=False,
                                 readonly=True, states={'draft': [('readonly', False)]},
                                 default=fields.Datetime.now, help="Creation date of Inspect Work orders.")
    inspect_id = fields.Many2one("workshop.inspect", string="Workshop Inspect", readonly=True,
                                 states={'draft': [('readonly', False)]}, )
    date_assign = fields.Datetime(string='Assigning Date', index=True, copy=False, readonly=True,
                                  states={'draft': [('readonly', False)]}, )
    is_automatic = fields.Boolean(string="Is Automatic", default=False)
    ticket_id = fields.Many2one("workshop.ticket", string="Workshop Ticket", readonly=True,
                                states={'draft': [('readonly', False)]}, )

    def action_close(self):
        self.state = 'close'

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('You can not delete an Inspection Which Is Not In Draft State.'))
        return super(WorkshopEstimate, self).unlink()

    @api.model
    def create(self, values):
        if values.get('user_id'):
            values['date_assign'] = fields.Datetime.now()

        res = super(WorkshopEstimate, self).create(values)
        res.name = self.env['ir.sequence'].next_by_code('workshop.estimate') or '/'
        return res

    def _create_work_order(self):
        work_order_id = self.env['workshop.order'].create({
            'partner_id': self.partner_id.id,
            'machine_id': self.machine_id.id,
            'ticket_id': self.ticket_id.id,
            'is_automatic': True,
        })
        return {
            "type": "ir.actions.act_window",
            'res_model': 'workshop.estimate',
            "views": [[False, "form"]],
            "res_id": estimate_order_id.id,
            "context": {"create": False},
        }
