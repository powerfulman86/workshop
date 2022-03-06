# -*- coding: utf-8 -*-

from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError

AVAILABLE_STATE = [
    ('draft', 'Draft'),
    ('close', 'Closed'),
]


class WorkshopInspectCategories(models.Model):
    _name = 'workshop.inspect.category'
    _description = 'Inspect Category'

    name = fields.Char('Name', required=True)
    active = fields.Boolean(default=True,
                            help="If the active field is set to False, it will allow you to hide the Category without removing it.")
    note = fields.Text(string="Note", track_visibility='always')
    category_items = fields.One2many(comodel_name="workshop.inspect.items", inverse_name="category_id",
                                     string="Category Items",
                                     required=False, )


class WorkshopInspectItems(models.Model):
    _name = 'workshop.inspect.items'
    _rec_name = 'name'
    _description = 'Inspect Items'

    name = fields.Char('Name', required=True, translate=True)
    active = fields.Boolean(default=True,
                            help="If the active field is set to False, it will allow you to hide the item without removing it.")
    note = fields.Text(string="Note", track_visibility='always')
    category_id = fields.Many2one(comodel_name="workshop.inspect.category", string="Inspect Category", required=True, )
    inspect_item_type = fields.Many2many(comodel_name='workshop.inspect.type', relation="inspect_type_items", )
    product_ids = fields.One2many('product.template', 'inspect_item_id', string='Item Products', )
    products_count = fields.Integer(string='Number of products', compute='_compute_products_count', )

    @api.depends('product_ids')
    def _compute_products_count(self):
        for rec in self:
            rec.products_count = len(rec.product_ids)


class WorkshopInspectType(models.Model):
    _name = 'workshop.inspect.type'
    _rec_name = 'name'
    _description = 'Inspect Type'

    name = fields.Char('Name', required=True, translate=True)
    active = fields.Boolean(default=True,
                            help="If the active field is set to False, it will allow you to hide the item without removing it.")
    note = fields.Text(string="Note", track_visibility='always')
    inspect_type_items = fields.Many2many(comodel_name='workshop.inspect.items', relation="inspect_type_items", )


class WorkshopInspect(models.Model):
    _name = 'workshop.inspect'
    _description = 'Work-Order Inspect'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = "id desc"

    def _get_default_type(self):
        """ Gives default stage_id """
        default_stage = self.env['workshop.inspect.type'].search([], limit=1)
        return default_stage

    name = fields.Char('Name')
    ticket_id = fields.Many2one("workshop.ticket", string="Workshop Ticket", readonly=True,
                                states={'draft': [('readonly', False)]}, )
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

    inspect_date = fields.Datetime(string='Inspect Date', required=True, index=True, copy=False,
                                   readonly=True, states={'draft': [('readonly', False)]},
                                   default=fields.Datetime.now, help="Creation date of Inspect Work orders.")
    date_assign = fields.Datetime(string='Assigning Date', index=True, copy=False, readonly=True,
                                  states={'draft': [('readonly', False)]}, )

    inspect_type = fields.Many2one(comodel_name="workshop.inspect.type", string="Type", required=True,
                                   readonly=True, states={'draft': [('readonly', False)]}, default=_get_default_type)
    inspect_line = fields.One2many(comodel_name="workshop.inspect.line", inverse_name="inspect_id", string="Lines",
                                   required=False, readonly=True, states={'draft': [('readonly', False)]}, )
    estimate_ids = fields.One2many('workshop.estimate', 'inspect_id')
    estimate_count = fields.Integer('Estimate Count', compute="_compute_estimate_count", store=True)
    is_automatic = fields.Boolean(string="Is Automatic", default=False)

    @api.depends('estimate_ids')
    def _compute_estimate_count(self):
        for rec in self:
            rec.estimate_count = len(rec.estimate_ids.ids)

    def action_close(self):
        if len(self.inspect_line) == 0:
            raise UserError(_('You Must Add Line To Inspection.'))

        for rec in self.inspect_line:
            if rec.item_evaluation == 'check':
                raise UserError(_("Some Items Haven't Been Checked."))

        self.state = 'close'

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('You can not delete an Inspection Which Is Not In Draft State.'))
        return super(WorkshopInspect, self).unlink()

    @api.onchange("inspect_type")
    def set_inspection_type_items(self):
        self.ensure_one()
        if self.inspect_type and len(self.inspect_type.inspect_type_items.ids) != 0:
            for x in self.inspect_type.inspect_type_items.ids:
                self.update({'inspect_line': [(4, x)]})

    @api.model
    def create(self, values):
        if values.get('user_id'):
            values['date_assign'] = fields.Datetime.now()

        res = super(WorkshopInspect, self).create(values)
        res.name = self.env['ir.sequence'].next_by_code('workshop.inspect') or '/'
        return res

    def write(self, values):
        # user_id change: update date_assign
        if values.get('user_id') and 'date_assign' not in values:
            values['date_assign'] = fields.Datetime.now()

        res = super(WorkshopInspect, self).write(values)
        return res

    def create_estimate(self):
        if len(self.inspect_line) == 0:
            raise UserError(_('Inspection Lines Must Be Recorded to Proceed With Estimate'))

        inspect_order_id = self.env['workshop.estimate'].create({
            'partner_id': self.partner_id.id,
            'machine_id': self.machine_id.id,
            'inspect_id': self.id,
            'is_automatic': True,
        })
        return {
            "type": "ir.actions.act_window",
            'res_model': 'workshop.estimate',
            "views": [[False, "form"]],
            "res_id": inspect_order_id.id,
            "context": {"create": False},
        }

    def action_view_estimate_order(self):
        self.ensure_one()
        inspect_order_id = self.env['workshop.estimate'].search([('inspect_id', '=', self.id)])
        if len(inspect_order_id.ids) != 0:
            return {
                "type": "ir.actions.act_window",
                'res_model': 'workshop.estimate',
                "views": [[False, "form"]],
                "res_id": inspect_order_id.id,
                "context": {"create": False},
            }


class WorkOrderInspectLine(models.Model):
    _name = 'workshop.inspect.line'
    _description = 'Work-Order Inspect Line'
    _order = "id desc"

    name = fields.Char('Name')
    sequence = fields.Integer(string='Sequence', default=10)
    inspect_id = fields.Many2one(comodel_name="workshop.inspect", string="Inspect Id", required=False, )
    partner_id = fields.Many2one('res.partner', string='Customer', related="inspect_id.partner_id", store=True)
    machine_id = fields.Many2one('res.machine', string='Machine', related="inspect_id.machine_id", store=True)
    user_id = fields.Many2one('res.users', string='Assigned to', related="inspect_id.user_id", store=True)
    state = fields.Selection(AVAILABLE_STATE, string='State', related="inspect_id.state", store=True)
    inspect_date = fields.Datetime(string='Inspect Date', related="inspect_id.inspect_date", store=True)
    inspect_type = fields.Many2one(comodel_name="workshop.inspect.type", related="inspect_id.inspect_type", store=True)

    inspect_category = fields.Many2one(comodel_name="workshop.inspect.category", string="Inspect Category",
                                       related="inspect_item.category_id", store=True)
    inspect_item = fields.Many2one(comodel_name="workshop.inspect.items", string="Inspect Item", required=True, )
    item_evaluation = fields.Selection(string="Evaluation",
                                       selection=[('check', 'Check'), ('working', 'Working'),
                                                  ('malfunction', 'Not Working'), ],
                                       required=True, default="check")
    note = fields.Text(string="Note", track_visibility='always')
