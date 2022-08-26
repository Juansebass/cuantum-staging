# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2022 Autodidacta TI now <http://www.autodidactati.com/>
#
##############################################################################
{
    'name': 'CRM Custom',
    'category': 'CRM',
    'summary': 'Modificaciones en modulo CRM',
    'version': '15.0.1',
    'description': """ """,
    'author': 'Ivan Arriola - Autodidacta TI / Agil 365',
    'website': 'http://www.autodidactati.com/',
    'license': '',
    'depends': [
        'base','contacts','sale','ati_titulos','crm'
        ],
    'data': [
        'views/crm_lead_inherit_view.xml',
        'views/crm_stage_inherit_view.xml',
        'security/ir.model.access.csv',
        ],
    'installable': True,
    'application': False,
    'auto_install': False
}
