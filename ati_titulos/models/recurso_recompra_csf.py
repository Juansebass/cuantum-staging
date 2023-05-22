 # -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

logger = logging.getLogger(__name__)

class RecursoRecompraCSF(models.Model):
    _name = 'ati.recurso.recompra.csf'

    name = fields.Char('Nombre')
    date = fields.Date('Fecha')
    value = fields.Float('Valores')
    investment_type = fields.Many2one('ati.investment.type','Producto')
    movement_type = fields.Many2one('ati.movement.type','Movimiento')
    buyer = fields.Many2one('res.partner','Comprador',required=1)
    extracto_id = fields.Many2one('ati.extracto', 'Extracto')