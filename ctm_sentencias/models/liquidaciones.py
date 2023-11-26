 # -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64
import io
import xlsxwriter
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar

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

        if len(existe_liquidacion) == 2:
            existe_liquidacion[1].unlink()

        #Llenando campos informativos
        self.emisor = self.sentencia.emisor
        self.pagador = self.sentencia.pagador
        self.codigo = self.sentencia.codigo
        self.fecha_ejecutoria = self.sentencia.fecha_ejecutoria
        self.fecha_cuenta_cobro = self.sentencia.fecha_cuenta_cobro
        self.fecha_liquidar = self.sentencia.fecha_liquidar
        self.valor_condena = self.sentencia.valor_condena
        self.resultado = self.valor_condena

        #Generando resumen
        self._generar_resumen_liquidacion()


        self.state = 'liquidated'
        self.responsible = self.env.user.partner_id


    def _generar_resumen_liquidacion(self):
        self.liquidaciones_resumen_ids.unlink()
        if  self.codigo == "CPACA":
            fecha_periodo_cero = self.fecha_ejecutoria + relativedelta(months=+3)

        else:
            fecha_periodo_cero = self.fecha_ejecutoria + relativedelta(months=+6)

        fechas_base =[
            self.fecha_ejecutoria,
            fecha_periodo_cero,
            self.fecha_cuenta_cobro,
            self.fecha_liquidar
        ]
        if self.codigo == "CPACA":
            fecha_periodo_diez = self.fecha_ejecutoria + relativedelta(months=+10)
            fechas_base.append(fecha_periodo_diez)

        fechas_periodos = self.generate_last_days(self.fecha_ejecutoria, self.fecha_liquidar)
        fechas_periodos += fechas_base
        unique_fechas_periodos = sorted(list(set(fechas_periodos)))


        cont = 0
        fecha_anterior = None
        for fecha in  unique_fechas_periodos:
            tasa = 0
            interes = 0
            #Buscando tasas
            tasa_conf = self.env['ctm.tasas'].search(
            [('fecha_inicio', '<=', fecha), ('fecha_final', '>=', fecha)], limit=1)

            if not tasa_conf:
                raise ValidationError('No hay una tasa configurada para la fecha {0}'.format(fecha))

            #Todos los ajustes para CPACA
            if self.codigo == "CPACA":
                if fecha <= fecha_periodo_diez:
                    tasa = tasa_conf.dtf
                else:
                    tasa = tasa_conf.usura

                if (
                        fecha <= self.fecha_cuenta_cobro and
                        fecha > fecha_periodo_cero and
                        self.fecha_cuenta_cobro >=  fecha_periodo_cero
                ):
                    tasa = 0
            if self.codigo == "CCA":
                tasa = tasa_conf.usura
                if (
                        fecha <= self.fecha_cuenta_cobro and
                        fecha > fecha_periodo_cero and
                        self.fecha_cuenta_cobro >= fecha_periodo_cero
                ):
                    tasa = 0
            if cont > 0:
                dias = (fecha - fecha_anterior).days
                interes = ((1 + (tasa/100)) ** (1/365) - 1) * dias * self.valor_condena

            self.env['ctm.liquidaciones_resumen'].create({
                'liquidacion_id': self.id,
                'fecha': fecha,
                'tasa': tasa,
                'interes': interes,
            })
            self.resultado += interes
            fecha_anterior = fecha
            cont += 1

    def last_day_of_month(self, date):
        _, last_day = calendar.monthrange(date.year, date.month)
        return datetime(date.year, date.month, last_day).date()

    def generate_last_days(self,start_date, end_date):
        current_date = start_date
        last_days = []

        while current_date <= end_date:
            last_days.append(self.last_day_of_month(current_date))
            current_date = self.last_day_of_month(current_date) + relativedelta(days=+1)

        return last_days



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
    tasa = fields.Float('Tasa', digits=(10, 3))
    interes = fields.Float('Interés')




