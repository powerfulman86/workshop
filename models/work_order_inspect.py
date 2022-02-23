# -*- coding: utf-8 -*-

from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError

AVAILABLE_STATE = [
    ('draft', 'Draft'),
    ('process', 'Processing'),
    ('close', 'Closed'),
    ('cancel', 'Cancel'),
]


class InspectCategories(models.Model):
    _name = 'inspect.category'
    _description = 'Inspect Category'

    name = fields.Char('Name', required=True)
    active = fields.Boolean(default=True,
                            help="If the active field is set to False, it will allow you to hide the Category without removing it.")
    note = fields.Text(string="Note", track_visibility='always')
    category_items = fields.One2many(comodel_name="inspect.items", inverse_name="category_id", string="Category Items",
                                     required=False, )


class InspectItems(models.Model):
    _name = 'inspect.items'
    _rec_name = 'name'
    _description = 'New Description'

    name = fields.Char('Name', required=True, )
    active = fields.Boolean(default=True,
                            help="If the active field is set to False, it will allow you to hide the item without removing it.")
    note = fields.Text(string="Note", track_visibility='always')
    category_id = fields.Many2one(comodel_name="inspect.category", string="Inspect Category", required=True, )


class WorkOrderInspect(models.Model):
    _name = 'work.order.inspect'
    _description = 'Work-Order Inspect'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = "id desc"

    name = fields.Char('Name')
    work_order_id = fields.Many2one("work.order", string="Work-Order", readonly=True,
                                    states={'draft': [('readonly', False)]}, )
    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True, readonly=True,
                                 states={'draft': [('readonly', False)]}, )
    machine_id = fields.Many2one('res.machine', string='Machine', tracking=True, readonly=True,
                                 states={'draft': [('readonly', False)]}, )
    user_id = fields.Many2one('res.users', string='Assigned to', default=lambda self: self.env.uid, index=True,
                              readonly=True, states={'draft': [('readonly', False)]}, )
    description = fields.Html('Description', help='Description')
    state = fields.Selection(AVAILABLE_STATE, string='State', index=True, default=AVAILABLE_STATE[0][0],
                             tracking=True, )

    inspect_date = fields.Datetime(string='Inspect Date', required=True, index=True, copy=False,
                                   readonly=True, states={'draft': [('readonly', False)]},
                                   default=fields.Datetime.now, help="Creation date of Inspect Work orders.")
    date_assign = fields.Datetime(string='Assigning Date', index=True, copy=False, readonly=True,
                                  states={'draft': [('readonly', False)]}, )

    inspect_type = fields.Selection(string="Type", selection=[('general', 'General'), ('receive', 'Receive'),
                                                              ('technical', 'Technical'), ], required=False,
                                    readonly=True, states={'draft': [('readonly', False)]}, default='general', )
    inspect_line = fields.One2many(comodel_name="work.order.inspect.line", inverse_name="inspect_id", string="Lines",
                                   required=False, readonly=True, states={'process': [('readonly', False)]}, )

    def action_process(self):
        self.state = 'process'

    def action_close(self):
        self.state = 'close'

    def action_cancel(self):
        self.state = 'cancel'

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('You can not delete an Inspection Which Is Not In Draft State.'))
        return super(WorkOrderInspect, self).unlink()

    def inspection_technical(self):
        return

    def inspection_receive(self):
        return

    @api.model
    def create(self, values):
        if values.get('user_id'):
            values['date_assign'] = fields.Datetime.now()

        res = super(WorkOrderInspect, self).create(values)
        res.name = self.env['ir.sequence'].next_by_code('work.order.inspect') or '/'
        return res

    def write(self, values):
        # user_id change: update date_assign
        if values.get('user_id') and 'date_assign' not in values:
            values['date_assign'] = fields.Datetime.now()

        res = super(WorkOrderInspect, self).write(values)
        return res


class WorkOrderInspectLine(models.Model):
    _name = 'work.order.inspect.line'
    _description = 'Work-Order Inspect Line'
    _order = "id desc"

    name = fields.Char('Name')
    sequence = fields.Integer(string='Sequence', default=10)
    inspect_id = fields.Many2one(comodel_name="work.order.inspect", string="Inspect Id", required=False, )
    partner_id = fields.Many2one('res.partner', string='Customer', related="inspect_id.partner_id", store=True)
    machine_id = fields.Many2one('res.machine', string='Machine', related="inspect_id.machine_id", store=True)
    user_id = fields.Many2one('res.users', string='Assigned to', related="inspect_id.user_id", store=True)
    state = fields.Selection(AVAILABLE_STATE, string='State', related="inspect_id.state", store=True)
    inspect_date = fields.Datetime(string='Inspect Date', related="inspect_id.inspect_date", store=True)
    inspect_type = fields.Selection(string="Type", related="inspect_id.inspect_type", store=True)

    inspect_category = fields.Many2one(comodel_name="inspect.category", string="Inspect Category", required=True, )
    inspect_item = fields.Many2one(comodel_name="inspect.items", string="Inspect Item", required=True,
                                   domain="[('category_id', '=', inspect_category)]")
    item_evaluation = fields.Selection(string="Evaluation",
                                       selection=[('working', 'Working'), ('malfunction', 'Not Working'), ],
                                       required=True, default="working")
    note = fields.Text(string="Note", track_visibility='always')
