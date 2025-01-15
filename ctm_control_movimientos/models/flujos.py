from odoo import models, fields


class Flujos(models.Model):
    _name = 'ctm.flujos'
    _description = 'Flujos'

    name = fields.Char(string='Nombre', required=True)
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True)
    flujo = fields.Float(string='Flujo', required=True)
    cdg = fields.Float(string='CDG', required=True)
    aplicacion_id = fields.Many2one('ctm.aplicaciones', string='Aplicación')
    compra_id = fields.Many2one('ctm.compras', string='Compra')
    movimientos_flujo_ids = fields.One2many('ctm.movimientos_flujos', 'flujo_id', string='Movimientos Flujos')


class MovimientosFlujos(models.Model):
    _name = 'ctm.movimientos_flujos'
    _description = 'Movimientos Flujos'

    flujo_id = fields.Many2one('ctm.flujos', string='Flujo', required=True)
    fecha_inicial = fields.Date('Fecha Inicial', required=1)
    fecha_final = fields.Date('Fecha Final', required=1)
    compra = fields.Float('Compra', required=1)
    rendimiento = fields.Float('Rendimiento', required=1)
    rendimiento_acumulado = fields.Float('Rendimiento Acumulado', required=1)
    cdg = fields.Float('CDG', required=1)
    cdg_acumulado = fields.Float('CDG Acumulado', required=1)
    pago_otros_conceptos = fields.Float('Pago Otros Conceptos', required=1)
    pago_cdg = fields.Float('Pago CDG', required=1)
    pago_rendimientos = fields.Float('Pago Rendimientos', required=1)
    pago_capital = fields.Float('Pago Capital', required=1)
    valor_activo = fields.Float('Valor Activo', required=1)
