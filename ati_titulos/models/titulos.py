 # -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

logger = logging.getLogger(__name__)

class Titulo(models.Model):
    _name = 'ati.titulo'
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char('Nombre')
    investment_type = fields.Many2one('ati.investment.type','Tipo de inversion', required=1)
    client = fields.Many2one('res.partner','Cliente',required=1)
    manager = fields.Many2one('ati.gestor','Gestor',required=1)
    issuing = fields.Many2one('res.partner','Emisor',required=1)
    payer = fields.Many2one('res.partner','Pagador',required=1)
    title = fields.Char('Titulo',required=1)
    last_periodo = fields.Char('Ultimo periodo cargado')
    date = fields.Date('Fecha ultima carga')
    value = fields.Float('Valor')
    recaudo_total = fields.Float('Recaudo Total')
    fee = fields.Float('Tasa')
    bonding_date = fields.Date('Fecha de validacion')
    redemption_date = fields.Date('Fecha de redencion')
    state_titulo = fields.Many2one('ati.state.titulo','Estado de titulo')
    state = fields.Selection(
        string='Status',
        store=True,
        selection=[
            ('draft', 'Borrador'),
            ('cancel', 'Cancelado'),
            ('confirmed', 'Confirmado')
        ],
    )
    tit_historico_ids = fields.One2many('ati.titulo.historico','titulo_id','Titulo Historico')

    #Variables de padre/hijo
    is_parent = fields.Boolean('Es padre')
    is_son = fields.Boolean(related='parent_id.is_parent', string='Es Hijo')
    son_ids = fields.One2many('ati.titulo.son','parent_id','Titulos hijo')
    parent_id = fields.Many2one('ati.titulo', 'Padre')

    @api.model
    def create(self, var):

        res = super(Titulo, self).create(var)
        res.name = res.title + ' - ' + res.client.name

        return res
    
    def write(self, values):
        res = super(Titulo, self).write(values)
        for son in self.son_ids:
                son.name.parent_id = self.id

        return res

class TitulosHistorico(models.Model):
    _name = 'ati.titulo.historico'

    name = fields.Char('Nombre')
    titulo_id = fields.Many2one('ati.titulo','Titulo')
    investment_type = fields.Many2one('ati.investment.type','Tipo de inversion', required=1)
    client = fields.Many2one('res.partner','Cliente',required=1)
    manager = fields.Many2one('res.partner','Gestor',required=1)
    issuing = fields.Many2one('res.partner','Emisor',required=1)
    payer = fields.Many2one('res.partner','Pagador',required=1)
    title = fields.Char('Titulo',required=1)
    periodo = fields.Char('Periodo')
    date_create = fields.Date('Fecha Carga')
    movement_type = fields.Many2one('ati.movement.type','Tipo de movimiento')
    value = fields.Float('Valor')
    recaudo = fields.Float('Recaudo')
    fee = fields.Float('Tasa')
    bonding_date = fields.Date('Fecha de Negociación')
    redemption_date = fields.Date('Fecha de redencion')
    state_titulo = fields.Many2one('ati.state.titulo','Estado de titulo')
    responsable = fields.Many2one('res.partner','Responsable de proceso')
    state = fields.Selection(
        string='Status',
        store=True,
        selection=[
            ('draft', 'Borrador'),
            ('cancel', 'Cancelado'),
            ('confirmed', 'Confirmado')
        ],
    )

class TitulosHijos(models.Model):
    _name = 'ati.titulo.son'

    name = fields.Many2one('ati.titulo', 'Hijos')
    parent_id = fields.Many2one('ati.titulo', 'Padre')