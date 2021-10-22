# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductModel(models.Model):
    _name = 'product.model'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Product Model'

    name = fields.Char()
    description = fields.Text()
    product_ids = fields.One2many('product.template', 'model_id', string='Model Products', )
    products_count = fields.Integer(string='Number of products', compute='_compute_products_count', )
    active = fields.Boolean('Active', default=True, help="Set active to false to hide the Brand without removing it.")
    logo = fields.Binary('Logo File', attachment=True)
    bannar = fields.Binary('Brand Bannar', attachment=True)

    @api.depends('product_ids')
    def _compute_products_count(self):
        for rec in self:
            rec.products_count = len(rec.product_ids)
