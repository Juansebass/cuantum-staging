# -*- coding: utf-8 -*-

from odoo import models, fields  # type: ignore


class Valoracion64(models.Model):
    _name = 'ctm.valoracion_6_4'
    _description = "Valoración 6.4"
    _inherit = []

    name = fields.Char('Nombre')
    sentencia = fields.Many2one('ctm.sentencias', 'Sentencia', required=1)
    emisor = fields.Many2one('res.partner', 'Emisor')
    pagador = fields.Many2one('res.partner', 'Pagador')
    codigo = fields.Char('Código')
    fecha_ejecutoria = fields.Date('Fecha de Ejecutoría')
    fecha_cuenta_cobro = fields.Date('Fecha de Cuenta de Cobro')
    fecha_liquidar = fields.Date('Fecha a Liquidar')
    valor_condena = fields.Float('Valor Condena')
    resultado = fields.Float('Resultado')
    total_intereses = fields.Float('Total Intereses')
    valoraciones_resumen_ids = fields.One2many('ctm.valoracion_6_4_resumen', 'valoracion_6_4_id', 'Resumen Valoración 6.4')
    responsible = fields.Many2one('res.partner', 'Responsable')
    state = fields.Selection(selection=[('draft', 'Borrador'), ('liquidated', 'Liquidado')], string='Estado', default='draft')
    simulacion_ids = fields.One2many('ctm.valoracion_6_4_simulacion', 'valoracion_6_4_id')
    tir_sentencia_bruta = fields.Float('TIR Sentencia Bruta')

    nit_fcp_statum = fields.Char('NIT FCP STATUM (Comp 1)', related='sentencia.nit_fcp_statum')
    statum = fields.Selection(string='Statum', related='sentencia.statum')
    vendedor = fields.Char('Vendedor', related='sentencia.vendedor')
    nemotecnico = fields.Char('Nemotecnico', related='sentencia.nemotecnico')
    fecha_vencimiento = fields.Date('Fecha de Vencimiento', related='sentencia.fecha_vencimiento')
    fecha_compra = fields.Date('Fecha de Compra', related='sentencia.fecha_compra')
    valor_giro = fields.Float('Valor Giro', related='sentencia.valor_giro')
    comision = fields.Float('Comisión', related='sentencia.comision')
    valor_contable_ayer = fields.Float('Valor Contable Ayer')
    precio = fields.Float('Precio', digits=(16, 7))


class Valoracion64Resumen(models.Model):
    _name = 'ctm.valoracion_6_4_resumen'
    _description = "Valoraciones 6.4 Resumen Cuantum"
    _inherit = []

    valoracion_6_4_id = fields.Many2one('ctm.valoracion_6_4', 'Valoración 6.4', ondelete='cascade')
    fecha = fields.Date('Fecha', required=1)
    tasa = fields.Float('Tasa', digits=(10, 6))
    interes = fields.Float('Interés')


class Valoracion64Simulacion(models.Model):
    _name = 'ctm.valoracion_6_4_simulacion'
    _description = 'Valoración 6.4 Simulación'

    name = fields.Char('Nombre', required=True)
    valoracion_6_4_id = fields.Many2one('ctm.valoracion_6_4', 'Valoración 6.4', required=True, ondelete='cascade')
    fecha_ejecutoria = fields.Date('Fecha de Ejecutoría')
    fecha_cuenta_cobro = fields.Date('Fecha de Cuenta de Cobro')
    fecha_liquidar = fields.Date('Fecha a Liquidar')
    valor_condena = fields.Float('Valor Condena')
    total_intereses = fields.Float('Total Intereses')
    resultado = fields.Float('Resultado')
    tir_sentencia_bruta = fields.Float('TIR Sentencia Bruta')
