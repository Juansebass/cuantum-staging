# -*- coding: utf-8 -*-
{
    'name': 'Control de Movimientos',
    'category': 'Account',
    'summary': 'Modulo de Control de Movimientos Cuantum',
    'version': '0.0.2',
    'description': """ """,
    'author': 'Juan Sebastian Correa Acevedo',
    'license': '',
    'depends': [
        'base', 'contacts', 'portal', 'ati_titulos',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/compras.xml',
        'views/aplicaciones_views.xml',
        'views/cargar_movimientos_views.xml',
        'views/flujos_views.xml',
        'views/valor_portafolio_views.xml',
        'wizards/cerrar_movimiento_flujo_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}
