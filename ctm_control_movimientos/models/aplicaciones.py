from odoo import models, fields  # type: ignore
from odoo.exceptions import ValidationError  # type: ignore


class Aplicaciones(models.Model):
    _name = 'ctm.aplicaciones'
    _description = 'Aplicaciones'

    name = fields.Char(string='Nombre', required=True)
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True)
    fecha = fields.Date(string='Fecha', required=True)
    valor = fields.Float(string='Valor', required=True)
    investment_type_id = fields.Many2one('ati.investment.type', string='Tipo de Inversion', required=True)
    gestor_id = fields.Many2one('ati.gestor', string='Gestor', required=True)
    flujo = fields.Float(string='Flujo', required=True)
    cdg = fields.Float(string='CDG', required=True)
    otros = fields.Float(string='Otros', required=True)

    def procesar_movimiento(self):
        for record in self:
            name = f'{self.partner_id.name} - {self.investment_type_id.code} - {self.gestor_id.code} - {self.flujo * 100}% - {self.cdg * 100}%'
            flujo_id = self.env['ctm.flujos'].search([('name', '=', name)])
            if flujo_id:
                record.actualizar_flujo(flujo_id)
            else:
                raise ValidationError(f'FLujo no encontrado: {name}')

    def actualizar_flujo(self, flujo_id):
        self.ensure_one()
        first_movimiento_id = flujo_id.movimientos_flujo_ids.search([], order='fecha_final asc', limit=1)  # TODO VALIDAR
        if first_movimiento_id.fecha_inicial > self.fecha:
            raise ValidationError('La fecha de cargue es anterior a la fecha de creación del flujo')
        past_movimiento_id = flujo_id.movimientos_flujo_ids.search([], order='fecha_final desc', limit=1)  # TODO VALIDAR
        fecha_inicial = past_movimiento_id.fecha_final
        fecha_final = self.fecha
        past_valor_activo = past_movimiento_id.valor_activo
        rendimiento = (((1 + flujo_id.flujo) ** (1 / 365)) - 1) * (fecha_final - fecha_inicial).days * past_valor_activo
        rendimiento_acumulado = past_movimiento_id.rendimiento + rendimiento
        cdg = (((1 + flujo_id.cdg) ** (1 / 365)) - 1) * (fecha_final - fecha_inicial).days * past_valor_activo
        pago_otros_conceptos = self.valor if self.valor > self.otros else self.otros
        cdg_acumulado = past_movimiento_id.cdg + cdg
        pago_cdg = cdg_acumulado if self.valor - pago_otros_conceptos > cdg_acumulado else self.valor - pago_otros_conceptos
        pago_rendimientos = rendimiento_acumulado if self.valor - pago_otros_conceptos - pago_cdg > rendimiento_acumulado else self.valor - pago_otros_conceptos - pago_cdg
        pago_capital = self.valor - pago_otros_conceptos - pago_cdg - pago_rendimientos
        self.env['ctm.movimientos_flujos'].create({
            'flujo_id': flujo_id.id,
            'tipo': 'aplicación',
            'aplicacion_id': self.id,
            'fecha_inicial': fecha_inicial,
            'fecha_final': fecha_final,
            'compra': self.valor,
            'rendimiento': rendimiento,
            'pago_rendimientos': pago_rendimientos,
            'rendimiento_acumulado': rendimiento_acumulado,
            'cdg': cdg,
            'pago_cdg': pago_cdg,
            'cdg_acumulado': cdg_acumulado,
            'pago_otros_conceptos': pago_otros_conceptos,
            'pago_capital': pago_capital if pago_capital > 0 else 0,
            'valor_activo': past_movimiento_id.valor_activo + self.valor + rendimiento_acumulado,
        })
