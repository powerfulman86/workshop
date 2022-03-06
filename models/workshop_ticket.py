# -*- coding: utf-8 -*-

from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError

AVAILABLE_PRIORITIES = [
    ('0', 'Low'),
    ('1', 'Medium'),
    ('2', 'High'),
    ('3', 'Very High'),
]

AVAILABLE_STATE = [
    ('draft', 'Draft'),
    ('process', 'Processing'),
    ('close', 'Closed'),
    ('cancel', 'Cancel'),
]


class WorkshopTicketStage(models.Model):
    _name = 'workshop.ticket.stage'
    _description = 'ticket Stage'
    _order = 'sequence, id'

    name = fields.Char('Name', translate=True)
    sequence = fields.Integer(default=1)
    description = fields.Text(translate=True)
    active = fields.Boolean(string='Active', default=True)


class WorkshopTicket(models.Model):
    _name = 'workshop.ticket'
    _description = 'Work-shop Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = "sequence, id desc"

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        search_domain = []
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    def _get_default_stage_id(self):
        default_stage = self.env['workshop.ticket.stage'].search([], limit=1)
        return default_stage

    name = fields.Char('Name')
    code = fields.Integer(string="code", required=False, digits='(8,0)')
    stage_id = fields.Many2one('workshop.ticket.stage', string='Stage', ondelete='restrict', tracking=True, index=True,
                               default=_get_default_stage_id, group_expand='_read_group_stage_ids', copy=False)

    active = fields.Boolean(default=True,
                            help="If the active field is set to False, it will allow you to hide the project without removing it.")
    sequence = fields.Integer(default=10, help="Gives the sequence order when displaying a list of Projects.")
    partner_id = fields.Many2one('res.partner', string='Customer', auto_join=True, tracking=True, required=True)
    machine_id = fields.Many2one('res.machine', string='Plate Number', auto_join=True, tracking=True, required=True)
    user_id = fields.Many2one('res.users', string='Assigned to', default=lambda self: self.env.uid, index=True,
                              tracking=True)
    priority = fields.Selection(AVAILABLE_PRIORITIES, string='Priority', index=True,
                                default=AVAILABLE_PRIORITIES[0][0])
    tag_ids = fields.Many2many('workshop.tags', string='Tags')
    ticket_date = fields.Datetime(string='Ticket Date', required=True, index=True, copy=False,
                                  default=fields.Datetime.now,
                                  help="Creation date of draft/sent Work orders,\nConfirmation date of confirmed orders.")
    expected_date = fields.Datetime(string="Expected Date", default=fields.Datetime.now, required=False, )
    date_end = fields.Datetime(string='Ending Date', index=True, copy=False)
    date_assign = fields.Datetime(string='Assigning Date', index=True, copy=False)

    machine_kilometer = fields.Integer(string="Machine Kilometer", required=False, )
    ticket_notes = fields.Html('Notes', help='Notes')
    is_automatic = fields.Boolean(string="Is Automatic", default=False)
    inspect_ids = fields.One2many('workshop.inspect', 'ticket_id')
    inspect_count = fields.Integer('Inspect Count', compute="compute_inspect_count")

    ticket_line = fields.One2many(comodel_name="workshop.ticket.line", inverse_name="ticket_id", string="Lines",
                                  required=False, )

    @api.depends('inspect_ids')
    def compute_inspect_count(self):
        for rec in self:
            rec.inspect_count = len(rec.inspect_ids.ids)

    def create_inspection(self):
        inspection_id = self.env['workshop.inspect'].create({
            'partner_id': self.partner_id.id,
            'machine_id': self.machine_id.id,
            'ticket_id': self.id,
            'is_automatic': True,
        })
        inspection_id.set_inspection_type_items()

        return {
            "type": "ir.actions.act_window",
            'res_model': 'workshop.inspect',
            "views": [[False, "form"]],
            "res_id": inspection_id.id,
            "context": {"create": False},
        }

    def action_view_inspect(self):
        self.ensure_one()
        inspection_id = self.env['workshop.inspect'].search([('ticket_id', '=', self.id)])
        if len(inspection_id.ids) != 0:
            return {
                "type": "ir.actions.act_window",
                'res_model': 'workshop.inspect',
                "views": [[False, "form"]],
                "res_id": inspection_id.id,
                "context": {"create": False},
            }

    @api.model
    def create(self, values):
        if values.get('user_id'):
            values['date_assign'] = fields.Datetime.now()

        # if values.get('inspection_receive'):
        #     self.create_inspection()
        # Stage change: Update date_end if folded stage and date_last_stage_update
        if values.get('stage_id'):
            values.update(self.update_date_end(values['stage_id']))

        res = super(WorkshopTicket, self).create(values)
        res.name = self.env['ir.sequence'].next_by_code('workshop.ticket') or '/'
        if not res.stage_id:
            stage = self._get_default_stage_id()
            res.stage_id = stage

        return res

    def write(self, values):
        # user_id change: update date_assign
        if values.get('user_id') and 'date_assign' not in values:
            values['date_assign'] = fields.Datetime.now()

        # stage change: update date_last_stage_update
        if 'stage_id' in values:
            values.update(self.update_date_end(values['stage_id']))

        last = self.stage_id.sequence
        res = super(WorkshopTicket, self).write(values)
        now = self.stage_id.sequence
        if now < last:
            raise ValidationError(_("Must Proceed In Forward Steps !"))

        return res

    def update_date_end(self, stage_id):
        stage_close = self.env['workshop.order.stage'].search([], order="sequence desc", limit=1)

        if stage_close == stage_id:
            return {'date_end': fields.Datetime.now()}
        return {'date_end': False}

    def unlink(self):
        for rec in self:
            if rec.stage_id.sequence != 1:
                raise UserError(_('You can not delete a Work-Order Which Is Not In Draft State.'))
        return super(WorkshopTicket, self).unlink()


class WorkshopTicketLine(models.Model):
    _name = 'workshop.ticket.line'
    _description = 'Work-shop Ticket line'
    _order = "sequence, id desc"

    name = fields.Char('Name')
    sequence = fields.Integer(string='Sequence', default=10)
    ticket_id = fields.Many2one(comodel_name="workshop.ticket", string="Ticket Id", required=False, )
    partner_id = fields.Many2one('res.partner', string='Customer', related="ticket_id.partner_id", store=True)
    machine_id = fields.Many2one('res.machine', string='Machine', related="ticket_id.machine_id", store=True)
    user_id = fields.Many2one('res.users', string='Assigned to', related="ticket_id.user_id", store=True)
    stage_id = fields.Many2one('workshop.ticket.stage', related="ticket_id.stage_id", store=True)
    ticket_date = fields.Datetime(string='Inspect Date', related="ticket_id.ticket_date", store=True)

    line_details = fields.Char(string="Details", required=True, )
