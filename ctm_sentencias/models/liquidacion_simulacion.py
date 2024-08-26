 # -*- coding: utf-8 -*-

from odoo import models, fields, api


class LiquidacionSimulacion(models.Model):
    _name = 'liquidacion.simulacion'
    _description = 'Simulacion de Liquidaciones'

    name = fields.Char('Nombre', required=True)
    liquidacion_id = fields.Many2one('ctm.liquidaciones', 'Liquidación', required=True, ondelete='cascade')
    fecha_ejecutoria = fields.Date('Fecha de Ejecutoría')
    fecha_cuenta_cobro = fields.Date('Fecha de Cuenta de Cobro')
    fecha_liquidar = fields.Date('Fecha a Liquidar')
    valor_condena = fields.Float('Valor Condena')
    total_intereses = fields.Float('Total Intereses')
    resultado = fields.Float('Resultado')
    tir_sentencia_bruta = fields.Float('TIR Sentencia Bruta')
