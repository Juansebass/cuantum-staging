 # -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

logger = logging.getLogger(__name__)

class Extracto(models.Model):
    _name = 'ati.extracto'

    name = fields.Char('Nombre')
    client = fields.Many2one('res.partner','Cliente',required=1)
    manager = fields.Many2one('res.partner','Gestor',required=1)
    issuing = fields.Many2one('res.partner','Emisor',required=1)
    payer = fields.Many2one('res.partner','Pagador',required=1)
    title = fields.Char('Titulo')
    date = fields.Date('Fecha')
    movement_type = fields.Many2one('ati.movement.type','Tipo de movimiento')
    value = fields.Float('Valor')
    fee = fields.Float('Tasa')
    bonding_date = fields.Date('Fecha de validacion')
    redemption_date = fields.Date('Fecha de redencion')
    state_extracto = fields.Many2one('ati.state.extracto','Estado de extracto')
    state = fields.Selection(
        string='Status',
        store=True,
        selection=[
            ('draft', 'Borrador'),
            ('cancel', 'Cancelado'),
            ('confirmed', 'Confirmado')
        ],
    )