 # -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

logger = logging.getLogger(__name__)

class TituloOferta(models.Model):
    _name = 'ati.titulo.oferta'

    name = fields.Char('Nº de titulo',required=1)
    manager = fields.Many2one('ati.gestor','Gestor',required=1)
    issuing = fields.Many2one('res.partner','Emisor',required=1)
    payer = fields.Many2one('res.partner','Pagador',required=1)
    bonding_date = fields.Date('Fecha de validacion',required=1)
    redemption_date = fields.Date('Fecha de redencion',required=1)
    investment_type = fields.Many2one('ati.investment.type', 'Tipo', required=1)
    value = fields.Float('Valor',required=1)
    fee = fields.Float('Tasa',required=1)
    odquirido = fields.Boolean('Adquirido?')
    cliente = fields.Many2one('res.partner', 'Cliente')
    