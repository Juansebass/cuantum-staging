# -*- coding: utf-8 -*-
{
    'name': 'Sentencias',
    'category': 'Account',
    'summary': 'Modulo de Sentencias Cuantum',
    'version': '15',
    'description': """ """,
    'author': 'Juan Sebastian Correa Acevedo',
    'license': '',
    'depends': [
        'base','contacts', 'portal',
        ],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/tasas_views.xml',
        'views/cargar_sentencias_views.xml',
        'views/liquidaciones_views.xml',
        'views/create_sentencias_views.xml',
        'views/sentencias_views.xml',
        'views/liquidacion_simulacion_views.xml',
        'views/descuento_views.xml',
        ],
    'installable': True,
    'application': True,
    'auto_install': False
}
