 # -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class Descuentos(models.Model):
    _name = 'descuentos'
    _description = 'Descuentos'

    name = fields.Char(string='Nombre', required=True)
    liquidacion_id = fields.Many2one(
        'ctm.liquidaciones', 
        string='Liquidación',
    )
    descuento_bruto = fields.Float(
        string='Descuento Bruto',
        required=True,
    )
    retencion_total = fields.Float(string='Retención Total', required=True)
    estructuracion = fields.Float(string='Estructuración', required=True)
    intermediacion = fields.Float(string='Intermediación', required=True)


    valor_condena = fields.Float('Valor Condena')
    fecha_liquidar = fields.Date('Fecha a Liquidar')
    total_intereses = fields.Float('Total Intereses')
    resultado = fields.Float('Resultado')
    tir_sentencia_bruta = fields.Float('TIR Sentencia Bruta')
    

    @api.onchange('descuento_bruto')
    def _onchange_descuento_bruto(self):
        for record in self:
            if record.descuento_bruto < 0:
                raise ValueError(_('Descuento bruto no puede ser negativo.'))

    @api.onchange('retencion_total')
    def _onchange_retencion_total(self):
        for record in self:
            if record.retencion_total < 0:
                raise ValueError(_('Retención total no puede ser negativa.'))

    @api.onchange('estructuracion')
    def _onchange_estructuracion(self):
        for record in self:
            if record.estructuracion < 0:
                raise ValueError(_('Estructuración no puede ser negativa.'))

    @api.onchange('intermediacion')
    def _onchange_intermediacion(self):
        for record in self:
            if record.intermediacion < 0:
                raise ValueError(_('Intermediación no puede ser negativa.'))
     
    def crear_descuento(self):
        for record in self:
            record.valor_condena = record.liquidacion_id.valor_condena
            record.fecha_liquidar = record.liquidacion_id.fecha_liquidar
            record.total_intereses = record.liquidacion_id.total_intereses
            record.resultado = record.liquidacion_id.resultado
            record.tir_sentencia_bruta = record.liquidacion_id.tir_sentencia_bruta
