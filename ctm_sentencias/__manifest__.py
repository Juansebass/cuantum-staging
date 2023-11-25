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
        # 'views/validacion_views.xml',
        #'views/informe_administracion_views.xml',\
        # 'report/xls_informe_clientes.xml',
        # 'data/mail_template_extracto.xml'
        ],
    'installable': True,
    'application': True,
    'auto_install': False
}
