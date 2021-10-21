# -*- coding: utf-8 -*-

from odoo import fields, models, api, SUPERUSER_ID, _


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
        self.env['work.order.stage'].search([])

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
    create_date = fields.Datetime("Created On", readonly=True, index=True)
    write_date = fields.Datetime("Last Updated On", readonly=True, index=True)
    date_end = fields.Datetime(string='Ending Date', index=True, copy=False)
    date_assign = fields.Datetime(string='Assigning Date', index=True, copy=False, readonly=True)
    date_last_stage_update = fields.Datetime(string='Last Stage Update',
                                             index=True, copy=False, readonly=True)

    @api.model
    def create(self, values):
        res = super(WorkOrder, self).create(values)
        res.name = self.env['ir.sequence'].next_by_code('work.order') or '/'
        return res
