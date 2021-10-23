# -*- coding: utf-8 -*-

from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError


class WorkOrderStage(models.Model):
    _name = 'work.order.stage'
    _description = 'Work-Order Stage'
    _order = 'sequence, id'

    name = fields.Char('Name', translate=True)
    sequence = fields.Integer(default=1)
    description = fields.Text(translate=True)
    active = fields.Boolean(string='Active', default=True)


class WorkOrderTags(models.Model):
    """ Tags of project's tasks """
    _name = "work.order.tags"
    _description = "Work-Order Tags"

    name = fields.Char('Tag Name', required=True)
    color = fields.Integer(string='Color Index')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists!"),
    ]


AVAILABLE_PRIORITIES = [
    ('0', 'Low'),
    ('1', 'Medium'),
    ('2', 'High'),
    ('3', 'Very High'),
]


class WorkOrder(models.Model):
    _name = 'work.order'
    _description = 'Work-Order'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = "priority desc, sequence, id desc"

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        search_domain = []
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    def _get_default_stage_id(self):
        """ Gives default stage_id """
        default_stage = self.env['work.order.stage'].search([], limit=1)
        return default_stage

    name = fields.Char('Name')
    stage_id = fields.Many2one('work.order.stage', string='Stage', ondelete='restrict', tracking=True, index=True,
                               default=_get_default_stage_id, group_expand='_read_group_stage_ids', copy=False)

    active = fields.Boolean(default=True,
                            help="If the active field is set to False, it will allow you to hide the project without removing it.")
    sequence = fields.Integer(default=10, help="Gives the sequence order when displaying a list of Projects.")
    partner_id = fields.Many2one('res.partner', string='Customer', auto_join=True, tracking=True, required=True)
    machine_id = fields.Many2one('res.machine', string='Machine', auto_join=True, tracking=True, required=True)
    user_id = fields.Many2one('res.users', string='Assigned to', default=lambda self: self.env.uid, index=True,
                              tracking=True)
    priority = fields.Selection(AVAILABLE_PRIORITIES, string='Priority', index=True,
                                default=AVAILABLE_PRIORITIES[0][0])
    tag_ids = fields.Many2many('work.order.tags', string='Tags')
    order_date = fields.Datetime(string='order Date', required=True, readonly=True, index=True, copy=False,
                                 default=fields.Datetime.now,
                                 help="Creation date of draft/sent Work orders,\nConfirmation date of confirmed orders.")
    date_end = fields.Datetime(string='Ending Date', index=True, copy=False, readonly=True)
    date_assign = fields.Datetime(string='Assigning Date', index=True, copy=False, readonly=True)
    description = fields.Text(translate=True)
    order_inspect = fields.One2many('work.order.inspect', 'work_order_id', string="Work-Order Inspect")
    order_inspect_count = fields.Integer('Inspect Count', compute="_compute_inspect_count")

    @api.depends('order_inspect')
    def _compute_inspect_count(self):
        for rec in self:
            rec.order_inspect_count = len(rec.order_inspect.ids)

    @api.model
    def create(self, values):
        if values.get('user_id'):
            values['date_assign'] = fields.Datetime.now()

        # Stage change: Update date_end if folded stage and date_last_stage_update
        if values.get('stage_id'):
            values.update(self.update_date_end(values['stage_id']))

        res = super(WorkOrder, self).create(values)
        res.name = self.env['ir.sequence'].next_by_code('work.order') or '/'
        if not res.stage_id:
            stage = self._get_default_stage_id()
            res.stage_id = stage
        return res

    def action_view_inspect(self):
        self.ensure_one()
        action = self.env.ref('workshop.work_order_inspect_action')
        result = action.read()[0]
        result['context'] = {'default_parent_id': self.id}
        result['domain'] = "[('id', 'in', " + str(self.order_inspect.ids) + ")]"
        return result

    def write(self, values):
        # user_id change: update date_assign
        if values.get('user_id') and 'date_assign' not in values:
            values['date_assign'] = fields.Datetime.now()

        # stage change: update date_last_stage_update
        if 'stage_id' in values:
            values.update(self.update_date_end(values['stage_id']))

        last = self.stage_id.sequence
        res = super(WorkOrder, self).write(values)
        now = self.stage_id.sequence
        if now < last:
            raise ValidationError(_("Must Proceed In Forward Steps !"))

        return res

    def update_date_end(self, stage_id):
        stage_close = self.env['work.order.stage'].search([], order="sequence desc", limit=1)

        if stage_close == stage_id:
            return {'date_end': fields.Datetime.now()}
        return {'date_end': False}


AVAILABLE_STATE = [
    ('draft', 'Draft'),
    ('process', 'Processing'),
    ('close', 'Closed'),
    ('cancel', 'Cancel'),
]


class WorkOrderInspect(models.Model):
    _name = 'work.order.inspect'
    _description = 'Work-Order Inspect'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = "id desc"

    name = fields.Char('Name')
    partner_id = fields.Many2one('res.partner', string='Customer', auto_join=True, tracking=True, required=True)
    machine_id = fields.Many2one('res.machine', string='Machine', auto_join=True, tracking=True, required=True)
    user_id = fields.Many2one('res.users', string='Assigned to', default=lambda self: self.env.uid, index=True,
                              tracking=True)
    description = fields.Text(translate=True)
    state = fields.Selection(AVAILABLE_STATE, string='State', index=True, default=AVAILABLE_STATE[0][0],
                             tracking=True, )
    work_order_id = fields.Many2one("work.order", string="Work-Order", required=True, )
    inspect_date = fields.Datetime(string='Inspect Date', required=True, readonly=True, index=True, copy=False,
                                   default=fields.Datetime.now, help="Creation date of Inspect Work orders.")
    date_assign = fields.Datetime(string='Assigning Date', index=True, copy=False, readonly=True)

    def action_process(self):
        self.state = 'process'

    def action_close(self):
        self.state = 'close'

    def action_cancel(self):
        self.state = 'cancel'

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('You can not delete a Sugar Entry Which Is Not In Draft State.'))
        return super(WorkOrderInspect, self).unlink()

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