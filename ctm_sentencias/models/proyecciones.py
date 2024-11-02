from odoo import models, fields


class Proyecciones(models.Model):
    _name = 'ctm.proyecciones'
    _description = 'Proyecciones'

    name = fields.Char(string='Name', required=True)
    sentencia_id = fields.Many2one('ctm_sentencias.sentencia', string='Sentencia')
    retencion_total = fields.Float(string='Retención Total')
    intermediacion = fields.Float(string='Intermediación')
    estructuracion = fields.Float(string='Estructuración')
    valor_descuento_diluido = fields.Float(string='Valor Descuento Diluido')
    valor_compra_beneficiario = fields.Float(string='Valor Compra Beneficiario')
    total_descuentos = fields.Float(string='Total Descuentos')
    porcentaje_total_descuentos = fields.Float(string='Porcentaje Total Descuentos')
    tir_optimista = fields.Float(string='TIR Optimista')
    tir_neutral = fields.Float(string='TIR Neutral')
    tir_acido = fields.Float(string='TIR Ácido')
    tir_compra = fields.Float(string='TIR Compra')

    def calcular_proyeccion(self):
        pass
