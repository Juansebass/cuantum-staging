from odoo import models, fields  # type: ignore
from odoo.exceptions import ValidationError  # type: ignore


class Compras(models.Model):
    _name = 'ctm.compras'
    _description = 'Compras'

    name = fields.Char(string='Nombre', required=True)
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True)
    fecha = fields.Date(string='Fecha', required=True)
    valor = fields.Float(string='Valor', required=True)
    investment_type_id = fields.Many2one('ati.investment.type', string='Tipo de Inversion', required=True)
    gestor_id = fields.Many2one('ati.gestor', string='Gestor', required=True)
    flujo = fields.Float(string='Flujo', required=True)
    cdg = fields.Float(string='CDG', required=True)
    emisor_id = fields.Many2one('res.partner', string='Emisor', required=True)
    pagador_id = fields.Many2one('res.partner', string='Pagador', required=True)
    titulo_id = fields.Char(string='Título', required=True)

    def procesar_movimiento(self):
        for record in self:
            name = f'{self.partner_id.name} - {self.investment_type_id.code} - {self.gestor_id.code}'
            flujo_id = self.env['ctm.flujos'].search([
                ('name', '=', name),
                ('flujo', '=', self.flujo),
                ('cdg', '=', self.cdg)
            ]).limit(1)
            if flujo_id:
                record.actualizar_flujo(flujo_id)
            else:
                record.crear_flujo(name)

    def crear_flujo(self, name):
        self.ensure_one()
        flujo_id = self.env['ctm.flujos'].create({
            'name': name,
            'partner_id': self.partner_id.id,
            'flujo': self.flujo,
            'cdg': self.cdg,
            'gestor_id': self.gestor_id.id,
            'investment_type_id': self.investment_type_id.id,
        })
        self.env['ctm.movimientos_flujos'].create({
            'flujo_id': flujo_id.id,
            'tipo': 'compra',
            'compra_id': self.id,
            'fecha_inicial': self.fecha,
            'fecha_final': self.fecha,
            'compra': self.valor,
            'rendimiento': 0,
            'rendimiento_acumulado': 0,
            'cdg': 0,
            'cdg_acumulado': 0,
            'pago_otros_conceptos': 0,
            'pago_cdg': 0,
            'pago_rendimientos': 0,
            'pago_capital': 0,
            'valor_activo': self.valor,
        })

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
        self.env['ctm.movimientos_flujos'].create({
            'flujo_id': flujo_id.id,
            'tipo': 'compra',
            'compra_id': self.id,
            'fecha_inicial': fecha_inicial,
            'fecha_final': fecha_final,
            'compra': self.valor,
            'rendimiento': rendimiento,
            'pago_rendimientos': 0,  # Acá siempre es compras
            'rendimiento_acumulado': rendimiento_acumulado,
            'cdg': cdg,
            'pago_cdg': 0,  # Acá siempre es compras
            'cdg_acumulado': past_movimiento_id.cdg + cdg,
            'pago_otros_conceptos': 0,  # Acá siempre es compras
            'pago_capital': 0,  # Acá siempre es compras
            'valor_activo': past_movimiento_id.valor_activo + self.valor + rendimiento_acumulado,
        })
        flujo_id.recalcular_flujo()
