# -*- coding: utf-8 -*-
from odoo import http

# class L10nCoAccountUvt(http.Controller):
#     @http.route('/l10n_co_account_uvt/l10n_co_account_uvt/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_co_account_uvt/l10n_co_account_uvt/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_co_account_uvt.listing', {
#             'root': '/l10n_co_account_uvt/l10n_co_account_uvt',
#             'objects': http.request.env['l10n_co_account_uvt.l10n_co_account_uvt'].search([]),
#         })

#     @http.route('/l10n_co_account_uvt/l10n_co_account_uvt/objects/<model("l10n_co_account_uvt.l10n_co_account_uvt"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_co_account_uvt.object', {
#             'object': obj
#         })