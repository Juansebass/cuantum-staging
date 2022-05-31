# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2022 Autodidacta TI now <http://www.autodidactati.com/>
#
##############################################################################
{
    'name': 'Extractos',
    'category': 'Web',
    'summary': 'Modulo de extractos Cuantum',
    'version': '11.0.1',
    'description': """ """,
    'author': 'Ivan Arriola - Autodidacta TI / Agil 365',
    'website': 'http://www.autodidactati.com/',
    'license': '',
    'depends': [
        'base','contacts',
        ],
    'data': [
        'views/state_extracto.xml',
        'views/movement_type.xml',
        'views/extractos_view.xml',
        'views/gestor_view.xml',
        'views/res_partner_view.xml',
        'views/menu.xml',
        ],
    'installable': True,
    'application': False,
    'auto_install': False
}
