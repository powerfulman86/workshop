# -*- coding: utf-8 -*-
# from odoo import http


# class PurchaseCreditLetter(http.Controller):
#     @http.route('/purchase_credit_letter/purchase_credit_letter/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/purchase_credit_letter/purchase_credit_letter/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('purchase_credit_letter.listing', {
#             'root': '/purchase_credit_letter/purchase_credit_letter',
#             'objects': http.request.env['purchase_credit_letter.purchase_credit_letter'].search([]),
#         })

#     @http.route('/purchase_credit_letter/purchase_credit_letter/objects/<model("purchase_credit_letter.purchase_credit_letter"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('purchase_credit_letter.object', {
#             'object': obj
#         })
