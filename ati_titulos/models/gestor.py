 # -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

logger = logging.getLogger(__name__)

class Gestor(models.Model):
    _name = 'ati.gestor'

    name = fields.Char('Nombre')
    description = fields.Char('Descripcion')
    code = fields.Char('Codigo corto')