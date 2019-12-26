# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Colombian Documents Module',
    'version': '13.0.0.0.1',
    'category': 'Hidden/Dependency',
    'description': """
NIT validation for Colombian Partners.
=========================================
    """,
    'author': 'CTI Ltda',
    'website': 'http://3rp.com',
    'sequence': 110,
    'depends': ['base'],
    'data': [
        'views/res_partner_view.xml',
        'views/res_company_view.xml',
    ],
    'images': ['images/1_partner_vat.jpeg'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
