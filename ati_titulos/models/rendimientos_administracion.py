 # -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

logger = logging.getLogger(__name__)

class RendimientosAdministracion(models.Model):
    _name = 'ati.rendimientos.administracion'

    name = fields.Char('Nombre')
    date = fields.Date('Fecha', required=True)
    value = fields.Float('Valores', required=True)
    investment_type = fields.Many2one('ati.investment.type','Producto', required=True)
    manager = fields.Many2one('ati.gestor','Gestor', required=True)
    movement_type = fields.Selection([
        ('RENDIMIENTO' , 'Rendimiento'),
        ('ADMINISTRACION' , 'Administracion')
    ],'Movimiento', required=True)
    buyer = fields.Many2one('res.partner','Comprador',required=True)