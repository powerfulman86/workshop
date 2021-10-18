# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    model_id = fields.Many2many('product.model', string='Model', help='Select a brand for this product')
    brand_id = fields.Many2one('product.brand', string='Brand', help='Select a brand for this product')