# -*- coding: utf-8 -*-
{
    'name': 'Partner Portal',
    'category': 'Portal',
    'summary': 'Modulo para agregar funcionalidades al portal del cliente',
    'version': '15',
    'description': """ """,
    'author': 'Juan Sebastian Correa Acevedo',
    'license': '',
    'depends': [
        'base', 'contacts', 'portal',
    ],
    'data': [
        'views/portal_my_account_inherit.xml',
        'views/res_partner_form_inherit.xml',
    ],
    'installable': True,
    'application': False,
}
