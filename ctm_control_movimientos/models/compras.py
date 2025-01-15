from odoo import models, fields


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

    def procesar_movimiento(self):
        for record in self:
            name = f'{self.partner_id.name} - {self.investment_type_id.code} - {self.gestor_id.code} - {self.flujo * 100}% - {self.cdg * 100}%'
            record.crear_flujo(name)

    def crear_flujo(self, name):
        self.ensure_one()
        flujo_id = self.env['ctm.flujos'].create({
            'name': name,
            'tipo': 'compra',
            'compra_id': self.id,
            'partner_id': self.partner_id.id,
            'flujo': self.flujo,
            'cdg': self.cdg,
        })
        self.env['ctm.movimientos_flujos'].create({
            'flujo_id': flujo_id.id,
            'fecha_inicial': self.fecha,
            'fecha_final': self.fecha,
            'compra': 0,
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
