 # -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

logger = logging.getLogger(__name__)

class StateTitulo(models.Model):
    _name = 'ati.state.titulo'

    name = fields.Char('Nombre')
    code = fields.Char('Codigo corto')