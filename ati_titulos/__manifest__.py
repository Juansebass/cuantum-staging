# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2022 Autodidacta TI now <http://www.autodidactati.com/>
#
##############################################################################
{
    'name': 'Titulos',
    'category': 'Web',
    'summary': 'Modulo de Titulos Cuantum',
    'version': '11.0.1',
    'description': """ """,
    'author': 'Ivan Arriola - Autodidacta TI / Agil 365',
    'website': 'http://www.autodidactati.com/',
    'license': '',
    'depends': [
        'base','contacts','crm', 'ati_extractos'
        ],
    'data': [
        'security/security.xml',
        'views/state_titulo.xml',
        'views/state_periodos_view.xml',
        'views/movement_type.xml',
        'views/titulos_view.xml',
        'views/titulo_oferta_view.xml',
        'views/gestor_view.xml',
        'views/res_partner_view.xml',
        'views/investment_type.xml',
        'views/import_libranzas_view.xml',
        'views/import_factoring_view.xml',
        'views/import_sentencias_view.xml',
        'views/import_mutuos_view.xml',
        'views/import_recursos_fcl.xml',
        'views/import_recursos_csf.xml',
        'views/import_recursos_fcp.xml',
        'views/import_titulo_oferta_view.xml',
        'views/import_rendimientos_administracion_view.xml',
        'views/rendimientos_administracion_view.xml',
        'views/menu.xml',
        'data/state_titulo_data.xml',
        'data/movement_type_data.xml',
        'data/investment_type_data.xml',
        'data/gestor_data.xml',
        'security/ir.model.access.csv',
        ],
    'installable': True,
    'application': True,
    'auto_install': False
}
