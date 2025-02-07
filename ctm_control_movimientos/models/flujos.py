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

    def recalcular_flujo(self):
        flujos = self.movimientos_flujo_ids.sorted(key=lambda x: x.fecha_final, reverse=False)
        flujos_completed = flujos
        flujos = flujos[1:]
        for i, flujo in enumerate(flujos, start=1):
            if flujo.tipo == 'compra':
                past_movimiento_id = flujos_completed[i - 1]
                fecha_inicial = past_movimiento_id.fecha_final
                fecha_final = flujo.compra_id.fecha
                past_valor_activo = past_movimiento_id.valor_activo
                rendimiento = (((1 + self.flujo) ** (1 / 365)) - 1) * (fecha_final - fecha_inicial).days * past_valor_activo
                rendimiento_acumulado = past_movimiento_id.rendimiento + rendimiento
                cdg = (((1 + self.cdg) ** (1 / 365)) - 1) * (fecha_final - fecha_inicial).days * past_valor_activo
                compra = flujo.compra_id.valor
                pago_otros_conceptos = 0
                pago_cdg = 0
                pago_rendimientos = 0
                pago_capital = 0
                valor_activo = past_movimiento_id.valor_activo + compra + rendimiento - pago_otros_conceptos - pago_cdg - pago_rendimientos - pago_capital

                flujo.write({
                    'fecha_inicial': fecha_inicial,
                    'fecha_final': fecha_final,
                    'compra': compra,
                    'rendimiento': rendimiento,
                    'pago_rendimientos': 0,  # Acá siempre es compras
                    'rendimiento_acumulado': rendimiento_acumulado,
                    'cdg': cdg,
                    'pago_cdg': 0,  # Acá siempre es compras
                    'cdg_acumulado': past_movimiento_id.cdg + cdg,
                    'pago_otros_conceptos': 0,  # Acá siempre es compras
                    'pago_capital': 0,  # Acá siempre es compras
                    'valor_activo': valor_activo,
                })
            elif flujo.tipo == 'aplicación':
                past_movimiento_id = flujos_completed[i - 1]
                fecha_inicial = past_movimiento_id.fecha_final
                fecha_final = flujo.aplicacion_id.fecha
                past_valor_activo = past_movimiento_id.valor_activo
                rendimiento = (((1 + self.flujo) ** (1 / 365)) - 1) * (fecha_final - fecha_inicial).days * past_valor_activo
                rendimiento_acumulado = past_movimiento_id.rendimiento + rendimiento
                cdg = (((1 + self.cdg) ** (1 / 365)) - 1) * (fecha_final - fecha_inicial).days * past_valor_activo
                pago_otros_conceptos = flujo.aplicacion_id.valor if flujo.aplicacion_id.valor < flujo.aplicacion_id.otros else flujo.aplicacion_id.otros
                cdg_acumulado = past_movimiento_id.cdg + cdg
                pago_cdg = cdg_acumulado if flujo.aplicacion_id.valor - pago_otros_conceptos > cdg_acumulado else flujo.aplicacion_id.valor - pago_otros_conceptos
                pago_rendimientos = rendimiento_acumulado if flujo.aplicacion_id.valor - pago_otros_conceptos - pago_cdg > rendimiento_acumulado else flujo.aplicacion_id.valor - pago_otros_conceptos - pago_cdg
                pago_capital = flujo.aplicacion_id.valor - pago_otros_conceptos - pago_cdg - pago_rendimientos
                compra = 0
                valor_activo = past_movimiento_id.valor_activo + compra + rendimiento - pago_otros_conceptos - pago_cdg - pago_rendimientos - pago_capital
                flujo.write({
                    'fecha_inicial': fecha_inicial,
                    'fecha_final': fecha_final,
                    'compra': 0,
                    'rendimiento': rendimiento,
                    'pago_rendimientos': pago_rendimientos,
                    'rendimiento_acumulado': rendimiento_acumulado,
                    'cdg': cdg,
                    'pago_cdg': pago_cdg,
                    'cdg_acumulado': cdg_acumulado,
                    'pago_otros_conceptos': pago_otros_conceptos,
                    'pago_capital': pago_capital if pago_capital > 0 else 0,
                    'valor_activo': valor_activo,
                })


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
