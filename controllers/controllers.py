# -*- coding: utf-8 -*-
# from odoo import http


# class RepairManagement(http.Controller):
#     @http.route('/repair_management/repair_management/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/repair_management/repair_management/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('repair_management.listing', {
#             'root': '/repair_management/repair_management',
#             'objects': http.request.env['repair_management.repair_management'].search([]),
#         })

#     @http.route('/repair_management/repair_management/objects/<model("repair_management.repair_management"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('repair_management.object', {
#             'object': obj
#         })
