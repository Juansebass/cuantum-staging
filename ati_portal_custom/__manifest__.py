# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2022 Autodidacta TI now <http://www.autodidactati.com/>
#
##############################################################################
{
    'name': 'Portal Custom',
    'category': 'PORTAL',
    'summary': 'Modificaciones en modulo Portal',
    'version': '15.0.1',
    'description': """ """,
    'author': 'Ivan Arriola - Autodidacta TI / Agil 365',
    'website': 'http://www.autodidactati.com/',
    'license': '',
    'assets': {
        'web.assets_frontend': [
            'ati_portal_custom/static/src/css/ocultar_menu_portal.css',
        ],
    },
    'depends': [
        'base','contacts','web'
        ],
    'data': [
        ],
    'installable': True,
    'application': False,
    'auto_install': False
}
