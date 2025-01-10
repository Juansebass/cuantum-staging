# -*- coding: utf-8 -*-
{
    'name': 'Control de Movimientos',
    'category': 'Account',
    'summary': 'Modulo de Control de Movimientos Cuantum',
    'version': '0.0.1',
    'description': """ """,
    'author': 'Juan Sebastian Correa Acevedo',
    'license': '',
    'depends': [
        'base', 'contacts', 'portal',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}
