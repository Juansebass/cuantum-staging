 # -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

logger = logging.getLogger(__name__)

class RecursoRecompra(models.Model):
    _name = 'ati.recurso.recompra.fcl'

    name = fields.Char('Nombre')
    date = fields.Date('Fecha')
    value = fields.Float('Valores')
    movement_type = fields.Many2one('ati.movement.type','Movimiento')
    buyer = fields.Many2one('res.partner','Comprador',required=1)
