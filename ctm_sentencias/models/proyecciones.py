from odoo import models, fields
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar
from odoo.exceptions import ValidationError

class Proyecciones(models.Model):
    _name = 'ctm.proyecciones'
    _description = 'Proyecciones'

    name = fields.Char(string='Name', required=True)
    sentencia_id = fields.Many2one('ctm.sentencias', string='Sentencia')
    retencion_total = fields.Float(string='Retención Total')
    intermediacion = fields.Float(string='Intermediación')
    estructuracion = fields.Float(string='Estructuración')
    ingreso_anticipado_cuantum  = fields.Float('Ingreso Anticipado Cuantum')
    valor_descuento_diluido = fields.Float(string='Valor Descuento Diluido')
    valor_compra_beneficiario = fields.Float(string='Valor Compra Beneficiario')
    valor_venta_inversionista = fields.Float(string='Valor Venta Inversionista')
    total_descuentos = fields.Float(string='Total Descuentos')
    porcentaje_total_descuentos = fields.Float(string='Porcentaje Total Descuentos')
    tir_optimista = fields.Float(string='TIR Optimista')
    tir_neutral = fields.Float(string='TIR Neutral')
    tir_acido = fields.Float(string='TIR Ácido')
    tir_compra = fields.Float(string='TIR Compra')
    # Liquidaciones Iniciales	
    liquidacion_inicial_ids = fields.One2many('ctm.liquidacion_inicial', 'proyeccion_id', string='Liquidaciones Iniciales')
    valor_condena = fields.Float(string='Valor Condena', readonly=True)
    total_intereses = fields.Float(string='Total Intereses', readonly=True)
    resultado = fields.Float(string='Resultado', readonly=True)
    # Proyecciones de Venta
    proyeccion_venta_ids = fields.One2many('ctm.proyeccion_venta', 'proyeccion_id', string='Proyecciones de Venta')


    # TODO Las proyecciones y acciones solo son visibles para sentencias de statum csf


    def calcular_proyeccion(self):
        for record in self:
            record.liquidacion_inicial_ids.unlink()
            record.generar_liquidacion_inicial()
            # Resultados
            
            record.retencion_total = record.sentencia_id.retencion_total * record.total_intereses
            record.estructuracion = record.sentencia_id.estructuracion
            record.intermediacion = record.sentencia_id.intermediacion * record.resultado

            porcentaje_descuentos_parciales = record.sentencia_id.descuento_diluido + record.sentencia_id.ingreso_anticipado_cuantum
            descuento_parcial = record.resultado * porcentaje_descuentos_parciales
            record.total_descuentos = record.retencion_total + record.estructuracion + record.intermediacion  + descuento_parcial
            record.porcentaje_total_descuentos = record.total_descuentos / record.resultado
            record.valor_compra_beneficiario = record.resultado - record.total_descuentos
            record.valor_descuento_diluido = record.valor_compra_beneficiario * record.sentencia_id.descuento_diluido
            record.valor_venta_inversionista = record.valor_compra_beneficiario * (1 - record.sentencia_id.descuento_diluido)
            record.ingreso_anticipado_cuantum = record.sentencia_id.ingreso_anticipado_cuantum * record.resultado

            record.generar_proyeccion_venta()
    
    def generar_liquidacion_inicial(self):
        for record in self:
            codigo = record.sentencia_id.codigo
            fecha_ejecutoria = record.sentencia_id.fecha_ejecutoria
            fecha_periodo_cero = None
            fecha_cuenta_cobro = record.sentencia_id.fecha_cuenta_cobro
            fecha_liquidar = record.sentencia_id.fecha_liquidar
            record.valor_condena = record.sentencia_id.valor_condena
            record.resultado = record.valor_condena
            record.total_intereses = 0
            if  codigo == "CPACA":
                fecha_periodo_cero = fecha_ejecutoria + relativedelta(months=+3)

            else:
                fecha_periodo_cero = fecha_ejecutoria + relativedelta(months=+6)
            fechas_base = [
                fecha_ejecutoria,
                fecha_periodo_cero,
                fecha_cuenta_cobro,
                fecha_liquidar
            ]
            if codigo == "CPACA":
                fecha_periodo_diez = fecha_ejecutoria + relativedelta(months=+10)
                fechas_base.append(fecha_periodo_diez)
            fechas_periodos = self.generate_last_days(fecha_ejecutoria, fecha_liquidar)
            fechas_periodos += fechas_base
            unique_fechas_periodos = sorted(list(set(fechas_periodos)))
            if unique_fechas_periodos[-1].month == unique_fechas_periodos[-2].month:
                unique_fechas_periodos.pop(-1)

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
                if codigo == "CPACA":
                    if fecha <= fecha_periodo_diez:
                        tasa = tasa_conf.dtf
                    else:
                        tasa = tasa_conf.usura

                    if (
                            fecha <= fecha_cuenta_cobro and
                            fecha > fecha_periodo_cero and
                            fecha_cuenta_cobro >=  fecha_periodo_cero
                    ):
                        tasa = 0
                if codigo == "CCA":
                    tasa = tasa_conf.usura
                    if (
                            fecha <= fecha_cuenta_cobro and
                            fecha > fecha_periodo_cero and
                            fecha_cuenta_cobro >= fecha_periodo_cero
                    ):
                        tasa = 0
                if cont > 0:
                    dias = (fecha - fecha_anterior).days
                    interes = round(((1 + (tasa/100)) ** (1/365) - 1), 6) * dias * record.valor_condena

                self.env['ctm.liquidacion_inicial'].create({
                    'proyeccion_id': self.id,
                    'fecha': fecha,
                    'tasa': tasa,
                    'interes': interes,
                })
                record.resultado += interes
                record.total_intereses += interes
                fecha_anterior = fecha
                cont += 1
            record.resultado += record.sentencia_id.costas

    def last_day_of_month(self, date):
        _, last_day = calendar.monthrange(date.year, date.month)
        return datetime(date.year, date.month, last_day).date()

    def generate_last_days(self,start_date, end_date):
        current_date = start_date
        last_days = []

        while current_date < end_date:
            last_days.append(self.last_day_of_month(current_date))
            current_date = self.last_day_of_month(current_date) + relativedelta(days=+1)

        return last_days

    def generar_proyeccion_venta(self):
        for record in self:
            record.proyeccion_venta_ids.unlink()
            fecha_liquidar= record.sentencia_id.fecha_liquidar
            fecha_acido = record.sentencia_id.fecha_liquidar_acido
            fecha_neutral = record.sentencia_id.fecha_liquidar_neutral
            fecha_optimista = record.sentencia_id.fecha_liquidar_optimista

            fechas_generacion = [fecha_liquidar, fecha_acido, fecha_neutral, fecha_optimista]
            fechas = []
            for fecha in fechas_generacion:
                fechas.append((fecha, record.last_day_of_month(fecha)))

            for fecha in fechas:
                self.env['ctm.proyeccion_venta'].create(
                    {
                        'proyeccion_id': record.id,
                        'fecha_inicial': fecha[0],
                        'fecha_final': fecha[1],
                    }
                )
          

class LiquidacionInicial(models.Model):
    _name = 'ctm.liquidacion_inicial'
    _description = 'Liquidación Inicial'

    proyeccion_id = fields.Many2one('ctm.proyecciones', string='Proyección')
    fecha = fields.Date('Fecha', required=1)
    tasa = fields.Float('Tasa', digits=(10, 6))
    interes = fields.Float('Interés')

class ProyeccionVenta(models.Model):
    _name = 'ctm.proyeccion_venta'
    _description = 'Proyección Venta'

    proyeccion_id = fields.Many2one('ctm.proyecciones', string='Proyección')
    fecha_inicial = fields.Date('Fecha Inicial')
    fecha_final = fields.Date('Fecha Final')
    tasa = fields.Float('Tasa', digits=(10, 6))
    interes = fields.Float('Interés')
    descuento_diluido = fields.Float('Descuento Diluido')
    rendimientos_totales = fields.Float('Rendimientos Totales')
    valor_antes_cdg = fields.Float('Valor Antes CDG')
    valor_comision_gestion = fields.Float('Valor Comisión Gestión')
    valor_esperado = fields.Float('Valor Esperado')
