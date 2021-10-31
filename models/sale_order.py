# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'
    work_id = fields.Many2one("work.order", string="Workshop", required=False, )


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    machine_id = fields.Many2one("res.machine", string="Machine", required=False, )
    work_id = fields.Many2one("work.order", string="Workshop", required=False, )

    def _prepare_invoice_vals(self):
        vals = super(SaleOrder, self)._prepare_invoice_vals()
        print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
        vals['work_id'] = self.work_id.id
        return vals

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals.update({  'work_id': self.work_id.id})
        return invoice_vals

    @api.onchange('machine_id')
    def _get_partner(self):
        for rec in self:
            rec.partner_id = rec.machine_id.partner_id
