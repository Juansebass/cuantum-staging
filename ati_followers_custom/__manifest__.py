# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2022 Autodidacta TI now <http://www.autodidactati.com/>
#
##############################################################################
{
    'name': 'Followers Custom',
    'category': 'Sale',
    'summary': 'Modificaciones en modulo Ventas',
    'version': '15.0.1',
    'description': """ """,
    'author': 'Ivan Arriola - Autodidacta TI / Agil 365',
    'website': 'http://www.autodidactati.com/',
    'license': '',
    'depends': [
        'base','contacts','sale','ati_extractos'
        ],
    'data': [
        'views/contact_views.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}
