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


class WorkshopOrderStage(models.Model):
    _name = 'workshop.order.stage'
    _description = 'Work-Order Stage'
    _order = 'sequence, id'

    name = fields.Char('Name', translate=True)
    sequence = fields.Integer(default=1)
    description = fields.Text(translate=True)
    active = fields.Boolean(string='Active', default=True)


class WorkshopTags(models.Model):
    _name = "workshop.tags"
    _description = "Work-Shop Tags"

    name = fields.Char('Tag Name', required=True)
    color = fields.Integer(string='Color Index')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists!"),
    ]


class WorkshopOrder(models.Model):
    _name = 'workshop.order'
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
        default_stage = self.env['workshop.order.stage'].search([], limit=1)
        return default_stage

    name = fields.Char('Name')
    code = fields.Integer(string="code", required=False, digits='(8,0)')
    stage_id = fields.Many2one('workshop.order.stage', string='Stage', ondelete='restrict', tracking=True, index=True,
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
    order_date = fields.Datetime(string='Order Date', required=True, index=True, copy=False,
                                 default=fields.Datetime.now,
                                 help="Creation date of draft/sent Work orders,\nConfirmation date of confirmed orders.")
    expected_date = fields.Datetime(string="Expected Date", default=fields.Datetime.now, required=False, )
    date_end = fields.Datetime(string='Ending Date', index=True, copy=False)
    date_assign = fields.Datetime(string='Assigning Date', index=True, copy=False)
    machine_kilometer = fields.Integer(string="Machine Kilometer", required=False, )
    order_parts = fields.One2many('workshop.order.parts', 'order_id', string='Order Parts', copy=True, auto_join=True)
    order_service = fields.One2many('workshop.order.service', 'order_id', string='Order Service', copy=True,
                                    auto_join=True)
    order_notes = fields.Html('Notes', help='Notes')

    sale_ids = fields.One2many('sale.order', 'work_id')
    invoice_ids = fields.One2many('account.move', 'work_id')
    sales_count = fields.Integer('Sales Count', compute="compute_counts")
    invoice_count = fields.Integer('Invoice Count', compute="compute_counts")
    sale_created = fields.Boolean()
    inspect_id = fields.Many2one(comodel_name="workshop.inspect", string="Inspection", required=False, )
    is_automatic = fields.Boolean(string="Is Automatic", default=False)
    ticket_id = fields.Many2one("workshop.ticket", string="Workshop Ticket", readonly=True,
                                states={'draft': [('readonly', False)]}, )

    def create_sale(self):
        sale_id = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'work_id': self.id,
            'note': self.order_notes,
        })

        for line in self.order_parts:
            self.env['sale.order.line'].create({
                'order_id': sale_id.id,
                'product_id': line.product_id.id,
                'name': line.product_id.name,
                'product_uom_qty': line.product_qty,
                'price_unit': line.price_unit,
            })
        for ln in self.order_service:
            self.env['sale.order.line'].create({
                'order_id': sale_id.id,
                'product_id': ln.product_id.id,
                'name': ln.product_id.name,
                'product_uom_qty': 1,
                'price_unit': ln.price_unit,
            })
        sale_id.action_confirm()
        for pick in sale_id.picking_ids:
            for line in pick.move_ids_without_package:
                line.quantity_done = line.product_uom_qty
            pick.button_validate()
        sale_id._create_invoices()
        for inv in sale_id.invoice_ids:
            inv.action_post()
        self.sale_created = True

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

    @api.model
    def create(self, values):
        if values.get('user_id'):
            values['date_assign'] = fields.Datetime.now()

        if values.get('stage_id'):
            values.update(self.update_date_end(values['stage_id']))

        res = super(WorkshopOrder, self).create(values)
        res.name = self.env['ir.sequence'].next_by_code('workshop.order') or '/'
        if not res.stage_id:
            stage = self._get_default_stage_id()
            res.stage_id = stage

        if res.inspection_receive:
            inspection = self.env['workshop.inspect']
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
        inspection_id = self.env['workshop.inspect'].search([('work_order_id', '=', self.id)])
        if len(inspection_id.ids) != 0:
            return {
                "type": "ir.actions.act_window",
                'res_model': 'workshop.inspect',
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
        res = super(WorkshopOrder, self).write(values)
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
        return super(WorkshopOrder, self).unlink()


class WorkOrderParts(models.Model):
    _name = 'workshop.order.parts'
    _description = 'Work-Order Parts'
    _order = "sequence, id desc"

    order_id = fields.Many2one('workshop.order', string='Order Reference', required=True, ondelete='cascade',
                               index=True,
                               copy=False)
    sequence = fields.Integer(string='Sequence', default=10)
    stage_id = fields.Many2one('workshop.order.stage', related='order_id.stage_id', string='Order Stage', readonly=True,
                               copy=False, store=True, )
    order_partner_id = fields.Many2one(related='order_id.partner_id', store=True, string='Customer', readonly=False)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Technical', index=True, default=lambda self: self.env.uid, )
    install_date = fields.Date(string="install_date", required=False, default=fields.Datetime.now, )
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
    _name = 'workshop.order.service'
    _description = 'Work-Order Service'
    _order = "sequence, id desc"

    order_id = fields.Many2one('workshop.order', string='Order Reference', required=True, ondelete='cascade',
                               index=True,
                               copy=False)
    sequence = fields.Integer(string='Sequence', default=10)
    stage_id = fields.Many2one('workshop.order.stage', related='order_id.stage_id', string='Order Stage', readonly=True,
                               copy=False, store=True, )
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


class WorkshopOrderDiagnose(models.Model):
    _name = 'workshop.order.diagnose'
    _rec_name = 'name'
    _description = 'New Description'

    name = fields.Char()


class WorkshopOrderComplain(models.Model):
    _name = 'workshop.order.complain'
    _rec_name = 'name'
    _description = 'New Description'

    name = fields.Char()
