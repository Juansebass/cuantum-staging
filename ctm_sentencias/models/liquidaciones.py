 # -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64
import io
import xlsxwriter
from datetime import datetime

class Liquidaciones(models.Model):
    _name = 'ctm.liquidaciones'
    _description = "Liquidaciones Cuantum"
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
    liquidaciones_resumen_ids = fields.One2many('ctm.liquidaciones_resumen','liquidacion_id','Resumen Liquidación Sentencia')
    responsible = fields.Many2one('res.partner', 'Responsable')
    state = fields.Selection(selection=[('draft','Borrador'),('liquidated','Liquidado')],string='Estado',default='draft')

    def generar_liquidacion(self):
        #Revisando si ya existe liquidación
        existe_liquidacion = self.env['ctm.liquidaciones'].search(
            [('sentencia', '=', self.sentencia.id)])

        if existe_liquidacion:
            existe_liquidacion.unlink()

        #Llenando campos informativos
        self.emisor = self.sentencia.emisor
        self.pagador = self.sentencia.pagador
        self.codigo = self.sentencia.codigo
        self.fecha_ejecutoria = self.sentencia.fecha_ejecutoria
        self.fecha_cuenta_cobro = self.sentencia.fecha_cuenta_cobro
        self.fecha_liquidar = self.sentencia.fecha_liquidar
        self.valor_condena = self.sentencia.valor_condena

        self.state = 'liquidated'
        self.responsible = self.env.user.partner_id

    def set_borrador_liquidacion(self):
        for rec in self:
            if self.env.user.id in [8,2,10, 108]:
                rec.state = 'draft'
            else:
                raise ValidationError('Usted no tiene permisos para realizar esta acción')

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError('Los extracto debe estar en borrador para poder ser eliminados')
        return super(Liquidaciones, self).unlink()

    @api.model
    def create(self, var):
        res = super(Liquidaciones, self).create(var)
        res.name = "Liquidación" ' - ' + res.sentencia.name
        return res







class LiquidacionesResumen(models.Model):
    _name = 'ctm.liquidaciones_resumen'
    _description = "Liquidaciones Resumen Cuantum"
    _inherit = []

    liquidacion_id = fields.Many2one('ctm.liquidaciones', 'Liquidación')
    fecha = fields.Date('Fecha', required=1)
    tasa = fields.Float('Tasa', digits=(10, 3), required=True)
    interes = fields.Float('Interés')




