 # -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

logger = logging.getLogger(__name__)

class StatePeriodo(models.Model):
    _name = 'ati.state.periodo'

    name = fields.Char('Nombre')
    month = fields.Char('Mes')
    year = fields.Char('Año')
    state_cargue = fields.Selection(
        string='Estado de Cargue',
        store=True,
        selection=[
            ('open', 'Abierto'),
            ('close', 'Cerrado')
        ],
    )
    state_envio_extracto = fields.Selection(
        string='Estado envio de extracto',
        store=True,
        selection=[
            ('open', 'Abierto'),
            ('close', 'Cerrado')
        ],
    )
    state_consulta_extracto = fields.Selection(
        string='Estado consulta de extracto',
        store=True,
        selection=[
            ('open', 'Abierto'),
            ('close', 'Cerrado')
        ],
    )