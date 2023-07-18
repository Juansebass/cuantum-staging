# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2022 Autodidacta TI now <http://www.autodidactati.com/>
#
##############################################################################
{
    'name': 'Sale Custom',
    'category': 'Sale',
    'summary': 'Modificaciones en modulo Ventas',
    'version': '11.0.1',
    'description': """ """,
    'author': 'Ivan Arriola - Autodidacta TI / Agil 365',
    'website': 'http://www.autodidactati.com/',
    'license': '',
    'depends': [
        'base','contacts','sale','ati_titulos'
        ],
    'data': [
        'views/sale_order_line_inherit_view.xml',
        'views/oferta_sale_order_portal_inherit.xml',
        'views/sale_order_approve.xml',
        'report/report_sale_order_inherit.xml',
        'report/report_acta_adicion.xml',
        'data/mail_template_data.xml'
        ],
    'installable': True,
    'application': False,
    'auto_install': False
}
