# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2022 Autodidacta TI now <http://www.autodidactati.com/>
#
##############################################################################
{
    'name': 'Extractos',
    'category': 'Web',
    'summary': 'Modulo de Extractos Cuantum',
    'version': '11.0.1',
    'description': """ """,
    'author': 'Ivan Arriola - Autodidacta TI / Agil 365',
    'website': 'http://www.autodidactati.com/',
    'license': '',
    'depends': [
        'base','contacts','ati_titulos','portal',
        ],
    'data': [
        'views/menu.xml',
        'views/extracto_views.xml',
        'views/portal_extracto.xml',
        'security/ir.model.access.csv',
        'report/report_extracto.xml',
        ],
    'installable': True,
    'application': True,
    'auto_install': False
}
