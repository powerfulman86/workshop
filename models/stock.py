# -*- coding: utf-8 -*-

from odoo import api, fields, models
from random import randint


class ProductBrand(models.Model):
    _name = 'product.brand'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Product Brand"

    code = fields.Char('Code', )
    name = fields.Char('Brand Name', required=True)
    ar_name = fields.Char('Arabic Brand Name')
    description = fields.Text(translate=True)
    partner_id = fields.Many2one('res.partner', string='Partner', help='Select a partner for this brand if any.',
                                 ondelete='restrict')
    logo = fields.Binary('Logo File', attachment=True)
    bannar = fields.Binary('Brand Bannar', attachment=True)
    product_ids = fields.One2many('product.template', 'brand_id', string='Brand Products', )
    products_count = fields.Integer(string='Number of products', compute='_compute_products_count', )
    active = fields.Boolean('Active', default=True, help="Set active to false to hide the Brand without removing it.")
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                          groups="analytic.group_analytic_accounting")
    model_ids = fields.One2many('product.model', 'brand_id', string='Brand Models', )
    models_count = fields.Integer(string='Number of Models', compute='_compute_products_count', )

    # enable_analytic = fields.Boolean(string='Enable analytic', compute="_enable_analytic")

    # @api.depends('name')
    # def _enable_analytic(self):
    #     for rec in self:
    #         if rec.env['ir.config_parameter'].sudo().get_param('base_setup.group_analytic_accounting') == "True":
    #             rec.enable_analytic = True
    #         else:
    #             rec.enable_analytic = False

    def random_number(self, n):
        range_start = 10 ** (n - 1)
        range_end = (10 ** n) - 1
        return randint(range_start, range_end)

    def check_brand_code(self, code):
        brand_ids = self.env['product.brand'].search([('code', '=', str("BR%s" % code))])
        while len(brand_ids) >= 1:
            code = self.random_number(4)
            self.check_brand_code(code)
        return str(code)

    @api.model
    def create(self, values):
        seq = self.env['ir.sequence'].next_by_code('product.brand') or '/'
        values['code'] = "BR" + self.check_brand_code(self.random_number(4))
        return super(ProductBrand, self).create(values)

    @api.depends('product_ids','model_ids')
    def _compute_products_count(self):
        for brand in self:
            brand.products_count = len(brand.product_ids)
            brand.models_count = len(brand.model_ids)


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
    brand_id = fields.Many2one('product.brand', string='Brand', help='Select a brand for this product')

    @api.depends('product_ids')
    def _compute_products_count(self):
        for rec in self:
            rec.products_count = len(rec.product_ids)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    model_id = fields.Many2many('product.model', string='Model', help='Select a brand for this product',
                                domain="[('brand_id', '=', brand_id)]")
    brand_id = fields.Many2one('product.brand', string='Brand', help='Select a brand for this product')
