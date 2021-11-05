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

AVAILABLE_STATE = [
    ('draft', 'Draft'),
    ('process', 'Processing'),
    ('close', 'Closed'),
    ('cancel', 'Cancel'),
]


class WorkOrder(models.Model):
    _name = 'work.order'
    _description = 'Work-Order'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = "sequence, id desc"

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
    code = fields.Integer(string="code", required=False, digits='(8,0)')
    stage_id = fields.Many2one('work.order.stage', string='Stage', ondelete='restrict', tracking=True, index=True,
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
    tag_ids = fields.Many2many('work.order.tags', string='Tags')
    order_date = fields.Datetime(string='Order Date', required=True, index=True, copy=False,
                                 default=fields.Datetime.now,
                                 help="Creation date of draft/sent Work orders,\nConfirmation date of confirmed orders.")
    expected_date = fields.Datetime(string="Expected Date", default=fields.Datetime.now, required=False, )
    date_end = fields.Datetime(string='Ending Date', index=True, copy=False)
    date_assign = fields.Datetime(string='Assigning Date', index=True, copy=False)

    inspection_receive = fields.Boolean(string="Inspection Receive", default=False)
    inspection_receive_count = fields.Integer(string="Inspection Count", compute="_compute_count_all", store=True)
    machine_kilometer = fields.Integer(string="Machine Kilometer", required=False, )
    order_parts = fields.One2many('work.order.parts', 'order_id', string='Order Parts', copy=True, auto_join=True)
    order_complain = fields.One2many('work.order.complain', 'order_id', string='Order Complain', copy=True,
                                     auto_join=True)
    order_diagnose = fields.One2many('work.order.diagnose', 'order_id', string='Order Diagnose', copy=True,
                                     auto_join=True)
    order_service = fields.One2many('work.order.service', 'order_id', string='Order Service', copy=True, auto_join=True)
    order_notes = fields.Html('Notes', help='Notes')

    sale_ids = fields.One2many('sale.order', 'work_id')
    invoice_ids = fields.One2many('account.move', 'work_id')
    sales_count = fields.Integer('Sales Count', compute="compute_counts")
    invoice_count = fields.Integer('Invoice Count', compute="compute_counts")

    def action_view_sale(self):
        action = self.env.ref('sale.action_orders').read()[0]
        action['domain'] = [('id', '=', self.sale_ids.ids)]
        action['context'] = {'default_work_id': self.id}
        return action

    def action_view_invoice(self):
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['domain'] = [('id', '=', self.invoice_ids.ids)]
        action['context'] = {'default_work_id': self.id}
        return action

    @api.depends('sale_ids', 'invoice_ids')
    def compute_counts(self):
        for rec in self:
            rec.sales_count = len(rec.sale_ids.ids)
            rec.invoice_count = len(rec.invoice_ids.ids)

    # def _compute_count_all(self):
    #     inspection = self.env['work.order.inspect']
    #     for record in self:
    #         record.inspection_receive_count = inspection.search_count([('work_order_id', '=', record.id)])

    @api.model
    def create(self, values):
        if values.get('user_id'):
            values['date_assign'] = fields.Datetime.now()

        # if values.get('inspection_receive'):
        #     self.create_inspection()
        # Stage change: Update date_end if folded stage and date_last_stage_update
        if values.get('stage_id'):
            values.update(self.update_date_end(values['stage_id']))

        res = super(WorkOrder, self).create(values)
        res.name = self.env['ir.sequence'].next_by_code('work.order') or '/'
        if not res.stage_id:
            stage = self._get_default_stage_id()
            res.stage_id = stage

        if res.inspection_receive:
            inspection = self.env['work.order.inspect']
            record = {
                'work_order_id': res.id,
                'partner_id': res.partner_id.id,
                'machine_id': res.machine_id.id,
                'inspect_date': res.order_date,
            }
            inspection.create(record)
        return res

    def action_view_inspect(self):
        self.ensure_one()
        inspection_id = self.env['work.order.inspect'].search([('work_order_id', '=', self.id)])
        if len(inspection_id.ids) != 0:
            return {
                "type": "ir.actions.act_window",
                'res_model': 'work.order.inspect',
                "views": [[False, "form"]],
                "res_id": inspection_id.id,
                "context": {"create": False},
            }

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

        # create inspection if not exist
        if 'inspection_receive' in values:
            if self.inspection_receive:
                inspection = self.env['work.order.inspect'].search([('work_order_id', '=', self.id)])
                if len(inspection.ids) == 0:
                    inspection = self.env['work.order.inspect']
                    record = {
                        'work_order_id': self.id,
                        'partner_id': self.partner_id.id,
                        'machine_id': self.machine_id.id,
                        'inspect_date': self.order_date,
                    }
                    inspection.create(record)

        return res

    def update_date_end(self, stage_id):
        stage_close = self.env['work.order.stage'].search([], order="sequence desc", limit=1)

        if stage_close == stage_id:
            return {'date_end': fields.Datetime.now()}
        return {'date_end': False}

    def unlink(self):
        for rec in self:
            if rec.stage_id.sequence != 1:
                raise UserError(_('You can not delete a Work-Order Which Is Not In Draft State.'))
        return super(WorkOrder, self).unlink()


class WorkOrderComplain(models.Model):
    _name = 'work.order.complain'
    _description = 'Work-Order Complain'
    _order = "sequence, id desc"

    def _get_default_stage_id(self):
        """ Gives default stage_id """
        default_stage = self.env['work.order.stage'].search([], limit=1)
        return default_stage

    order_id = fields.Many2one('work.order', string='Order Reference', required=True, ondelete='cascade', index=True,
                               copy=False)
    complain_notes = fields.Text(string='Complain', required=True)
    state = fields.Selection(string="State", selection=[('open', 'Open'), ('closed', 'Closed'), ('pending', 'Pending')],
                             required=False, default='open')
    sequence = fields.Integer(string='Sequence', default=10)
    stage_id = fields.Many2one('work.order.stage', related='order_id.stage_id', string='Order Stage', readonly=True,
                               copy=False, store=True, default=_get_default_stage_id, )
    order_partner_id = fields.Many2one(related='order_id.partner_id', store=True, string='Customer', readonly=False)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)


class WorkOrderDiagnose(models.Model):
    _name = 'work.order.diagnose'
    _description = 'Work-Order Lines'
    _order = "sequence, id desc"

    def _get_default_stage_id(self):
        """ Gives default stage_id """
        default_stage = self.env['work.order.stage'].search([], limit=1)
        return default_stage

    order_id = fields.Many2one('work.order', string='Order Reference', required=True, ondelete='cascade', index=True,
                               copy=False)
    stage_id = fields.Many2one('work.order.stage', related='order_id.stage_id', string='Order Stage', readonly=True,
                               copy=False, store=True, default=_get_default_stage_id, )
    order_partner_id = fields.Many2one(related='order_id.partner_id', store=True, string='Customer', readonly=False)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)

    technical_notes = fields.Text(string='Notes', required=True)
    state = fields.Selection(string="State", selection=[('open', 'Open'), ('closed', 'Closed'), ('pending', 'Pending')],
                             required=False, default='open')

    sequence = fields.Integer(string='Sequence', default=10)
    user_id = fields.Many2one('res.users', string='Technical', index=True, )


class WorkOrderParts(models.Model):
    _name = 'work.order.parts'
    _description = 'Work-Order Parts'
    _order = "sequence, id desc"

    def _get_default_stage_id(self):
        """ Gives default stage_id """
        default_stage = self.env['work.order.stage'].search([], limit=1)
        return default_stage

    order_id = fields.Many2one('work.order', string='Order Reference', required=True, ondelete='cascade', index=True,
                               copy=False)
    sequence = fields.Integer(string='Sequence', default=10)
    stage_id = fields.Many2one('work.order.stage', related='order_id.stage_id', string='Order Stage', readonly=True,
                               copy=False, store=True, default=_get_default_stage_id, )
    order_partner_id = fields.Many2one(related='order_id.partner_id', store=True, string='Customer', readonly=False)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Technical', index=True, default=lambda self: self.env.uid,)
    install_date = fields.Date(string="install_date", required=False, default=fields.Datetime.now,)
    price_unit = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0)
    product_id = fields.Many2one(
        'product.product', string='Product',
        domain="[('sale_ok', '=', True),('type', '=', 'product'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        change_default=True, ondelete='restrict', check_company=True)  # Unrequired company
    product_template_id = fields.Many2one(
        'product.template', string='Product Template',
        related="product_id.product_tmpl_id", domain=[('sale_ok', '=', True), ('type', '=', 'product')])

    product_qty = fields.Float(string='Quantity', digits='Product Quantity', required=True, default=1.0)


class WorkOrderService(models.Model):
    _name = 'work.order.service'
    _description = 'Work-Order Service'
    _order = "sequence, id desc"

    def _get_default_stage_id(self):
        """ Gives default stage_id """
        default_stage = self.env['work.order.stage'].search([], limit=1)
        return default_stage

    order_id = fields.Many2one('work.order', string='Order Reference', required=True, ondelete='cascade', index=True,
                               copy=False)
    sequence = fields.Integer(string='Sequence', default=10)
    stage_id = fields.Many2one('work.order.stage', related='order_id.stage_id', string='Order Stage', readonly=True,
                               copy=False, store=True, default=_get_default_stage_id, )
    order_partner_id = fields.Many2one(related='order_id.partner_id', store=True, string='Customer', readonly=False)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)

    price_unit = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0)
    product_id = fields.Many2one(
        'product.product', string='Product',
        domain="[('sale_ok', '=', True),('type', '=', 'service'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        change_default=True, ondelete='restrict', check_company=True)  # Unrequired company
    product_template_id = fields.Many2one(
        'product.template', string='Product Template',
        related="product_id.product_tmpl_id", domain=[('sale_ok', '=', True), ('type', '=', 'service')])

    product_qty = fields.Float(string='Quantity', digits='Product Quantity', required=True, default=1.0)
    user_id = fields.Many2one('res.users', string='Technical', index=True, )
    user_id_revise = fields.Many2one('res.users', string='Revision', index=True, )


class WorkOrderInspect(models.Model):
    _name = 'work.order.inspect'
    _description = 'Work-Order Inspect'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = "id desc"

    name = fields.Char('Name')
    work_order_id = fields.Many2one("work.order", string="Work-Order", required=True, )
    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True, )
    machine_id = fields.Many2one('res.machine', string='Machine', tracking=True, )
    user_id = fields.Many2one('res.users', string='Assigned to', default=lambda self: self.env.uid, index=True, )
    description = fields.Html('Description', help='Description')
    state = fields.Selection(AVAILABLE_STATE, string='State', index=True, default=AVAILABLE_STATE[0][0],
                             tracking=True, )

    inspect_date = fields.Datetime(string='Inspect Date', required=True, index=True, copy=False,
                                   default=fields.Datetime.now, help="Creation date of Inspect Work orders.")
    date_assign = fields.Datetime(string='Assigning Date', index=True, copy=False, )

    # inspect_type = fields.Selection(string="Type", selection=[('1', 'receive'), ('2', 'technical'), ], required=False, )

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
