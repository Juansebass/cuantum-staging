# -*- coding: utf-8 -*-
{
    'name': 'Validaciones',
    'category': 'Web',
    'summary': 'Modulo de Validaciones Cuantum',
    'version': '15',
    'description': """ """,
    'author': 'Juan Sebastian Correa Acevedo',
    'license': '',
    'depends': [
        'base','contacts','ati_titulos' , 'portal',
        ],
    'data': [
        'views/menu.xml',
        'views/validacion_views.xml',
        'security/ir.model.access.csv',
        # 'report/xls_informe_clientes.xml',
        # 'data/mail_template_extracto.xml'
        ],
    'installable': True,
    'application': True,
    'auto_install': False
}
