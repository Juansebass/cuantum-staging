# -*- coding: utf-8 -*-
{
    'name': 'Certificados',
    'category': 'Account',
    'summary': 'Modulo de Certificados Cuantum',
    'version': '15',
    'description': """ """,
    'author': 'Juan Sebastian Correa Acevedo',
    'license': '',
    'depends': [
        'base','contacts', 'portal', 'ati_extractos',
        ],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/certificado_views.xml',
        'views/retencion_views.xml',
        'report/report_comprador.xml',
        'views/portal_certificado.xml',
        ],
    'installable': True,
    'application': True,
    'auto_install': False
}
