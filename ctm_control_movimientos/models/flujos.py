from odoo import models, fields  # type: ignore


class Flujos(models.Model):
    _name = 'ctm.flujos'
    _description = 'Flujos'

    name = fields.Char(string='Nombre', required=True)
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True)
    flujo = fields.Float(string='Flujo', required=True)
    cdg = fields.Float(string='CDG', required=True)
    movimientos_flujo_ids = fields.One2many('ctm.movimientos_flujos', 'flujo_id', string='Movimientos Flujos')
    fecha_cierre = fields.Date('Fecha')
    rendimiento_cierre = fields.Float('Rendimiento de Cierre')
    rendimiento_acumulado_cierre = fields.Float('Rendimiento Acumulado de Cierre')
    cdg_cierre = fields.Float('CDG de Cierre')
    cdg_acumulado_cierre = fields.Float('CDG Acumulado de Cierre')
    valor_activo_cierre = fields.Float('Valor Activo de Cierre')

    def button_cerrar_movimientos_flujos(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ctm.cerrar_movimientos_flujos.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_date': fields.Date.today(),
                'active_ids': self.ids,
            },
        }

    def cerrar_movimientos_flujos(self, date):
        for record in self:
            movimientos_abiertos = record.movimientos_flujo_ids.filtered(lambda x: x.state == 'abierto')
            for movimiento in movimientos_abiertos:
                if movimiento.fecha_final <= date:
                    movimiento.state = 'cerrado'


class MovimientosFlujos(models.Model):
    _name = 'ctm.movimientos_flujos'
    _description = 'Movimientos Flujos'

    flujo_id = fields.Many2one('ctm.flujos', string='Flujo', required=True, ondelete='cascade')
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
    aplicacion_id = fields.Many2one('ctm.aplicaciones', string='Aplicación')
    compra_id = fields.Many2one('ctm.compras', string='Compra')
    tipo = fields.Selection(
        [
            ('compra', 'Compra'),
            ('aplicación', 'Aplicación')
        ], string='Tipo', required=True, default='compra'
    )
    state = fields.Selection(
        [
            ('abierto', 'Abierto'),
            ('cerrado', 'Cerrado')
        ], string='Estado', required=True, default='abierto', index=True
    )
