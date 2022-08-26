 # -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

logger = logging.getLogger(__name__)

class MovementType(models.Model):
    _name = 'ati.movement.type'

    name = fields.Char('Nombre')
    code = fields.Char('Codigo Corto')