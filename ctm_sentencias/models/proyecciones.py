from odoo import models, fields
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
from odoo.exceptions import ValidationError
import scipy.optimize as opt


class Proyecciones(models.Model):
    _name = 'ctm.proyecciones'
    _description = 'Proyecciones'

    name = fields.Char(string='Name', required=True)
    sentencia_id = fields.Many2one('ctm.sentencias', string='Sentencia')
    retencion_total = fields.Float(string='Retención Total')
    intermediacion = fields.Float(string='Intermediación')
    estructuracion = fields.Float(string='Estructuración')
    ingreso_anticipado_cuantum = fields.Float('Ingreso Anticipado Cuantum')
    valor_descuento_diluido = fields.Float(string='Valor Descuento Diluido')
    valor_compra_beneficiario = fields.Float(string='Valor Compra Beneficiario')
    valor_venta_inversionista = fields.Float(string='Valor Venta Inversionista')
    total_descuentos = fields.Float(string='Total Descuentos')
    total_descuentos_gastos = fields.Float(string='Total Descuentos Gastos')
    porcentaje_total_descuentos = fields.Float(string='Porcentaje Total Descuentos')
    porcentaje_total_descuentos_gastos = fields.Float(string='Porcentaje Total Descuentos Gastos')
    tir_optimista = fields.Float(string='TIR Optimista')
    tir_neutral = fields.Float(string='TIR Neutral')
    tir_acido = fields.Float(string='TIR Ácido')
    tir_compra = fields.Float(string='TIR Compra')
    valor_esperado_optimista = fields.Float(string='Valor Esperado Optimista')
    valor_esperado_neutral = fields.Float(string='Valor Esperado Neutral')
    valor_esperado_acido = fields.Float(string='Valor Esperado Ácido')
    valor_esperado_compra = fields.Float(string='Valor Esperado Compra')
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
            if record.sentencia_id.fecha_liquidar_optimista <= record.sentencia_id.fecha_liquidar:
                raise ValidationError('La fecha optimista no puede ser menor o igual a la fecha de liquidación')

            record.liquidacion_inicial_ids.unlink()
            record.generar_liquidacion_inicial()
            # Resultados

            record.retencion_total = (
                record.sentencia_id.retencion_total * record.total_intereses
            )
            record.estructuracion = record.sentencia_id.estructuracion
            record.intermediacion = (
                record.sentencia_id.intermediacion * record.resultado
            )
            record.valor_descuento_diluido = (
                record.resultado * record.sentencia_id.descuento_diluido
            )
            record.ingreso_anticipado_cuantum = (
                record.sentencia_id.ingreso_anticipado_cuantum *
                record.resultado
            )
            record.total_descuentos = (
                record.retencion_total +
                record.estructuracion +
                record.intermediacion +
                record.ingreso_anticipado_cuantum +
                record.valor_descuento_diluido
            )
            record.porcentaje_total_descuentos = (
                record.total_descuentos / record.resultado
            )
            record.total_descuentos_gastos = (
                record.retencion_total +
                record.estructuracion +
                record.intermediacion +
                record.ingreso_anticipado_cuantum
            )
            record.porcentaje_total_descuentos_gastos = (
                record.total_descuentos_gastos / record.resultado
            )
            record.valor_compra_beneficiario = (
                record.resultado - record.total_descuentos
            )

            record.valor_venta_inversionista = (
                record.resultado -
                record.total_descuentos +
                record.total_descuentos_gastos
            )

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
            if codigo == "CPACA":
                fecha_periodo_cero = fecha_ejecutoria + \
                    relativedelta(months=+3)

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
            for fecha in unique_fechas_periodos:
                tasa = 0
                interes = 0
                # Buscando tasas
                tasa_conf = self.env['ctm.tasas'].search(
                    [('fecha_inicio', '<=', fecha), ('fecha_final', '>=', fecha)], limit=1
                )

                if not tasa_conf:
                    raise ValidationError('No hay una tasa configurada para la fecha {0}'.format(fecha))

                # Todos los ajustes para CPACA
                if codigo == "CPACA":
                    if fecha <= fecha_periodo_diez:
                        tasa = tasa_conf.dtf
                    else:
                        tasa = tasa_conf.usura

                    if (
                            fecha <= fecha_cuenta_cobro
                            and fecha > fecha_periodo_cero
                            and fecha_cuenta_cobro >= fecha_periodo_cero
                    ):
                        tasa = 0
                if codigo == "CCA":
                    tasa = tasa_conf.usura
                    if (
                            fecha <= fecha_cuenta_cobro
                            and fecha > fecha_periodo_cero
                            and fecha_cuenta_cobro >= fecha_periodo_cero
                    ):
                        tasa = 0
                if cont > 0:
                    dias = (fecha - fecha_anterior).days
                    interes = round(((1 + (tasa / 100)) ** (1 / 365) - 1), 6) * dias * record.valor_condena

                liquidacion_inicial = self.env['ctm.liquidacion_inicial'].create({
                    'proyeccion_id': self.id,
                    'fecha': fecha,
                    'tasa': tasa,
                    'interes': interes,
                })
                record.resultado += interes
                record.total_intereses += interes
                fecha_anterior = fecha
                cont += 1

                liquidacion_inicial.interes_acumulado = record.total_intereses
                liquidacion_inicial.resultado = liquidacion_inicial.interes_acumulado + record.valor_condena
            record.resultado += record.sentencia_id.costas

    def last_day_of_month(self, date):
        _, last_day = calendar.monthrange(date.year, date.month)
        return datetime(date.year, date.month, last_day).date()

    def generate_last_days(self, start_date, end_date):
        current_date = start_date
        last_days = []

        while current_date < end_date:
            last_days.append(self.last_day_of_month(current_date))
            current_date = self.last_day_of_month(current_date) + relativedelta(days=+1)

        return last_days

    def generar_proyeccion_venta(self):
        for record in self:
            record.proyeccion_venta_ids.unlink()
            fecha_liquidar = record.sentencia_id.fecha_liquidar
            fecha_acido = record.sentencia_id.fecha_liquidar_acido
            fecha_neutral = record.sentencia_id.fecha_liquidar_neutral
            fecha_optimista = record.sentencia_id.fecha_liquidar_optimista

            fechas_generacion = [fecha_optimista, fecha_neutral, fecha_acido]
            fecha_liquidar_fin = record.last_day_of_month(fecha_liquidar)
            fechas = [(fecha_liquidar, fecha_liquidar_fin)]
            fecha_final = fecha_liquidar_fin
            fecha_incial = None
            for fecha_validacion in fechas_generacion:
                while fecha_validacion > fecha_final:
                    fecha_incial = fecha_final + relativedelta(days=+1)
                    fecha_final = record.last_day_of_month(fecha_incial)
                    fechas.append((fecha_incial, fecha_final))
                fecha_final = fecha_validacion
                fechas.pop(-1)
                fechas.append((fecha_incial, fecha_final))
            row = 0
            cash_flows = []

            if fecha_liquidar_fin == fecha_optimista:
                raise ValidationError('La fecha de liquidación optimista no puede ser igual a la fecha de liquidación')

            for fecha in fechas:
                # Buscando tasas
                tasa_conf = self.env['ctm.tasas'].search(
                    [('fecha_inicio', '<=', fecha[0]), ('fecha_final', '>=', fecha[0])], limit=1
                )
                if not tasa_conf:
                    raise ValidationError('No hay una tasa configurada para la fecha {0}'.format(fecha))
                tasa = tasa_conf.usura / 100
                interes = record.valor_condena * ((1 + tasa) ** (1 / 365) - 1) * (fecha[1] - fecha[0]).days

                if fecha[1] <= record.sentencia_id.fecha_liquidar_neutral:
                    days_neutral = (record.sentencia_id.fecha_liquidar_neutral - record.sentencia_id.fecha_liquidar).days
                    days_period = (fecha[1] - fecha[0]).days
                    descuento_diluido = (record.valor_descuento_diluido / days_neutral) * days_period
                else:
                    descuento_diluido = 0
                rendimientos_totales = interes + descuento_diluido
                if row == 0:
                    valor_antes_cdg = record.valor_venta_inversionista
                else:
                    valor_antes_cdg = valor_antes_cdg + rendimientos_totales
                valor_comision_gestion = valor_antes_cdg * ((1 + record.sentencia_id.comision_gestion_cuantum) ** (1 / 365) - 1) * (fecha[1] - fecha[0]).days
                valor_esperado = valor_antes_cdg - valor_comision_gestion
                self.env['ctm.proyeccion_venta'].create(
                    {
                        'proyeccion_id': record.id,
                        'fecha_inicial': fecha[0],
                        'fecha_final': fecha[1],
                        'tasa': tasa_conf.usura,
                        'interes': interes,
                        'descuento_diluido': descuento_diluido,
                        'rendimientos_totales': rendimientos_totales,
                        'valor_antes_cdg': valor_antes_cdg,
                        'valor_comision_gestion': valor_comision_gestion,
                        'valor_esperado': valor_esperado
                    }
                )
                # Generando TIR
                if row == 0:
                    cash_flows.append((-valor_esperado, fecha[0]))
                if fecha[1] == record.sentencia_id.fecha_liquidar_optimista:
                    cash_flows.append((valor_esperado, fecha[1]))
                    try:
                        record.tir_optimista = record._generar_tir(cash_flows)
                        record.valor_esperado_optimista = valor_esperado
                        cash_flows.pop(-1)
                    except Exception:
                        raise ValidationError('Error al calcular la TIR Optimista con flujo de caja {0}'.format(cash_flows))
                if fecha[1] == record.sentencia_id.fecha_liquidar_neutral:
                    cash_flows.append((valor_esperado, fecha[1]))
                    try:
                        record.tir_neutral = record._generar_tir(cash_flows)
                        record.valor_esperado_neutral = valor_esperado
                        cash_flows.pop(-1)
                    except Exception:
                        raise ValidationError('Error al calcular la TIR Neutral con flujo de caja {0}'.format(cash_flows))
                if fecha[1] == record.sentencia_id.fecha_liquidar_acido:
                    cash_flows.append((valor_esperado, fecha[1]))
                    try:
                        record.tir_acido = record._generar_tir(cash_flows)
                        record.valor_esperado_acido = valor_esperado
                        cash_flows.pop(-1)
                    except Exception:
                        raise ValidationError('Error al calcular la TIR Ácido con flujo de caja {0}'.format(cash_flows))
                row += 1

            # Para tir de compra
            cash_flows = [(-record.valor_condena, record.sentencia_id.fecha_ejecutoria), (record.resultado, record.sentencia_id.fecha_liquidar)]
            try:
                record.tir_compra = record._generar_tir(cash_flows)
                record.valor_esperado_compra = record.resultado
            except Exception:
                raise ValidationError('Error al calcular la TIR de Compra con flujo de caja {0}'.format(cash_flows))

    def _generar_tir(self, cash_flows):
        tir = 0
        # cash_flows = [(-record.valor_condena, record.fecha_ejecutoria), (record.resultado, record.fecha_liquidar)]
        dates = [cf[1] for cf in cash_flows]
        amounts = [cf[0] for cf in cash_flows]

        def npv(rate):
            # Start with the first date as the base
            base_date = dates[0]
            total_npv = 0

            if rate <= -1:
                return float('inf')  # Return a high value to indicate invalid IRR

            for i, date in enumerate(dates):
                # Calculate the time difference in days
                days_difference = (date - base_date).days

                # Discount factor
                discount_factor = (1 + rate) ** (days_difference / 365.0)

                # Contribution to NPV
                total_npv += amounts[i] / discount_factor

            return total_npv

        irr = opt.root_scalar(npv, bracket=[-0.99, 5], method='brentq').root
        tir = irr * 100
        return tir


class LiquidacionInicial(models.Model):
    _name = 'ctm.liquidacion_inicial'
    _description = 'Liquidación Inicial'

    proyeccion_id = fields.Many2one('ctm.proyecciones', string='Proyección')
    fecha = fields.Date('Fecha', required=1)
    tasa = fields.Float('Tasa', digits=(10, 6))
    interes = fields.Float('Interés')
    interes_acumulado = fields.Float('Interés Acumulado')
    resultado = fields.Float('Resultado')


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
