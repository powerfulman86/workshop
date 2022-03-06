# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ResMachine(models.Model):
    _name = 'res.machine'
    _description = 'Machine'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc, code asc'

    name = fields.Char('Plate number', compute="_get_license_number", store=True)
    code = fields.Char('Chase Number', required=True, )
    engine_number = fields.Char('Engine Number', required=True, )
    machine_colour = fields.Char(string="Colour", required=False, )
    model_id = fields.Many2one('product.model', domain="[('brand_id', '=', brand_id)]")
    brand_id = fields.Many2one('product.brand', string='Brand', help='Select a brand for this Machine')
    production_year = fields.Char(string="Production Year", size=4, required=True)
    capacity = fields.Integer(string="Capacity", required=False, )
    transmission = fields.Selection([('manual', 'Manual'), ('automatic', 'Automatic')], 'Transmission',
                                    help='Transmission Used by the vehicle')
    active = fields.Boolean('Active', default=True, tracking=True)
    fuel_type = fields.Selection([
        ('gasoline', 'Gasoline'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid')
    ], 'Fuel Type', help='Fuel Used by the vehicle')

    image = fields.Binary(string="Image", )
    partner_id = fields.Many2one('res.partner', string="Owner", required=True)
    notes = fields.Text(string="Notes", required=False, )

    code1 = fields.Char(string="code1", required=True, size=1)
    code2 = fields.Char(string="code2", required=True, size=1)
    code3 = fields.Char(string="code3", required=True, size=1)
    code4 = fields.Char(string="code4", required=True, size=1)
    code5 = fields.Char(string="code5", required=True, size=1)
    code6 = fields.Char(string="code6", required=True, size=1)
    code7 = fields.Char(string="code7", size=1)
    owner_name = fields.Char(string="Owner Name", required=False, )
    work_order_count = fields.Integer(compute="_compute_count_all", string='Work-orders')
    work_order_ids = fields.One2many('workshop.order', 'machine_id')
    inspect_count = fields.Integer(compute="_compute_count_all", string='Inspections')
    inspect_ids = fields.One2many('workshop.inspect', 'machine_id')
    ticket_count = fields.Integer(compute="_compute_count_all", string='Tickets')
    ticket_ids = fields.One2many('workshop.ticket', 'machine_id')

    _sql_constraints = [
        (
            "machine_name_unique",
            "unique(name)",
            "Machine Name must be unique across the database!",
        )
    ]

    @api.onchange('partner_id')
    def _onchange_partner(self):
        if not self.owner_name:
            self.owner_name = self.partner_id.name

    @api.depends('work_order_ids', 'inspect_ids', 'ticket_ids')
    def _compute_count_all(self):
        for rec in self:
            rec.work_order_count = len(rec.work_order_ids.ids)
            rec.inspect_count = len(rec.inspect_ids.ids)
            rec.ticket_count = len(rec.ticket_ids.ids)

    def action_view_work_orders(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            'res_model': 'workshop.order',
            'view_mode': 'tree,form',
            'name': _('Work-Orders'),
            "domain": [["machine_id", "=", self.id]],
            "context": {"create": False},
        }

    # def action_open_orders(self):
    #     """ This opens the xml view specified in xml_id for the current vehicle """
    #     self.ensure_one()
    #     xml_id = self.env.context.get('xml_id')
    #     if xml_id:
    #         res = self.env['ir.actions.act_window'].for_xml_id('workshop', xml_id)
    #         res.update(
    #             context=dict(self.env.context, default_vehicle_id=self.id, group_by=False),
    #             domain=[('machine_id', '=', self.id)]
    #         )
    #         return res
    #     return False
    #
    def action_view_inspect(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            'res_model': 'workshop.inspect',
            'view_mode': 'tree,form',
            'name': _('Inspections'),
            "domain": [["machine_id", "=", self.id]],
            "context": {"create": False},
        }

    def action_view_ticket(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            'res_model': 'workshop.ticket',
            'view_mode': 'tree,form',
            'name': _('Tickets'),
            "domain": [["machine_id", "=", self.id]],
            "context": {"create": False},
        }

    @api.depends('code1', 'code2', 'code3', 'code4', 'code5', 'code6', 'code7')
    def _get_license_number(self):
        for rec in self:
            rec.name = (rec.code1 or '') + (rec.code2 or '') + (rec.code3 or '') + (rec.code4 or '') + (
                    rec.code5 or '') + (rec.code6 or '') + (rec.code7 or '')

    @api.constrains('production_year')
    def _check_production_year(self):
        for rec in self:
            if not rec.production_year.isdigit():
                raise ValidationError(_("Production Year Must Be Digits"))

    def name_get(self):
        res = []
        for rec in self:
            name = "[%s] - %s" % (rec.name, rec.code)
            res += [(rec.id, name)]
        return res

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            domain = ['|', ('name', operator, name), ('code', operator, name)]
        rec = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return models.lazy_name_get(self.browse(rec).with_user(name_get_uid))

    def create_ticket(self):
        ticket_id = self.env['workshop.ticket'].create({
            'partner_id': self.partner_id.id,
            'machine_id': self.id,
            'is_automatic': True,
        })
        return {
            "type": "ir.actions.act_window",
            'res_model': 'workshop.ticket',
            "views": [[False, "form"]],
            "res_id": ticket_id.id,
            "context": {"create": False},
        }
