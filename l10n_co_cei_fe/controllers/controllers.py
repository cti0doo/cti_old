# -*- coding: utf-8 -*-
from odoo import http

# class CustomAddons/l10nCoCeiFe(http.Controller):
#     @http.route('/custom_addons/l10n_co_cei_fe/custom_addons/l10n_co_cei_fe/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_addons/l10n_co_cei_fe/custom_addons/l10n_co_cei_fe/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_addons/l10n_co_cei_fe.listing', {
#             'root': '/custom_addons/l10n_co_cei_fe/custom_addons/l10n_co_cei_fe',
#             'objects': http.request.env['custom_addons/l10n_co_cei_fe.custom_addons/l10n_co_cei_fe'].search([]),
#         })

#     @http.route('/custom_addons/l10n_co_cei_fe/custom_addons/l10n_co_cei_fe/objects/<model("custom_addons/l10n_co_cei_fe.custom_addons/l10n_co_cei_fe"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_addons/l10n_co_cei_fe.object', {
#             'object': obj
#         })