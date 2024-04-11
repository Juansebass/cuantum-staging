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
    'version': '11.0.2',
    'description': """ """,
    'author': 'Ivan Arriola - Autodidacta TI / Agil 365',
    'website': 'http://www.autodidactati.com/',
    'license': '',
    'depends': [
        'base','contacts','ati_titulos','portal', 'ctm_validaciones'
        ],
    'data': [
        'views/menu.xml',
        'views/extracto_views.xml',
        'views/portal_extracto.xml',
        'views/create_extractos_views.xml',
        'security/ir.model.access.csv',
        'report/report_extracto.xml',
        'data/mail_template_extracto.xml',
        'wizards/validate_extractos_views.xml',
        'wizards/informe_errores_wizard.xml',
        ],
    'installable': True,
    'application': True,
    'auto_install': False
}
