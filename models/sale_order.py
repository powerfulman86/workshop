# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    machine_id = fields.Many2one("res.machine", string="Machine", required=False, )

    @api.onchange('machine_id')
    def _get_partner(self):
        for rec in self:
            rec.partner_id = rec.machine_id.partner_id
