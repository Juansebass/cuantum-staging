# -*- coding: utf-8 -*-

from odoo import models, fields, api  # type: ignore
from odoo.exceptions import ValidationError  # type: ignore
import base64
from dateutil.relativedelta import relativedelta
from datetime import datetime
import calendar
import scipy.optimize as opt  # type: ignore


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
    resultado = fields.Float('Resultado a Fecha de Vencimiento')
    total_intereses = fields.Float('Total Intereses')
    valoraciones_resumen_ids = fields.One2many('ctm.valoracion_6_4_resumen', 'valoracion_6_4_id', 'Resumen Valoración 6.4')
    responsible = fields.Many2one('res.partner', 'Responsable')
    state = fields.Selection(selection=[('draft', 'Borrador'), ('liquidated', 'Liquidado')], string='Estado', default='draft')
    simulacion_ids = fields.One2many('ctm.valoracion_6_4_simulacion', 'valoracion_6_4_id')
    tir_compra_6_4 = fields.Float('TIR Compra 6.4')

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
    valor_actual_6_4 = fields.Float('Valor Actual 6.4')

    def generar_valoracion(self):
        self.emisor = self.sentencia.emisor
        self.pagador = self.sentencia.pagador
        self.codigo = self.sentencia.codigo
        self.fecha_ejecutoria = self.sentencia.fecha_ejecutoria
        self.fecha_cuenta_cobro = self.sentencia.fecha_cuenta_cobro
        self.fecha_vencimiento = self.sentencia.fecha_vencimiento
        self.fecha_liquidar = self.fecha_liquidar if self.fecha_liquidar else self.sentencia.fecha_liquidar
        self.valor_condena = self.sentencia.valor_condena
        self.resultado = self.valor_condena
        self.total_intereses = 0
        self.valor_giro = self.sentencia.valor_giro

        self._generar_valoraciones_resumen()
        self._genera_tir_compra_6_4()

        self.valor_actual_6_4 = self.resultado / ((1 + self.tir_compra_6_4 * 0.01) ** ((self.fecha_compra - self.fecha_liquidar).days / 365))

    def _generar_valoraciones_resumen(self):
        self.valoraciones_resumen_ids.unlink()

        if self.codigo == "CPACA":
            fecha_periodo_cero = self.fecha_ejecutoria + relativedelta(months=+3)

        else:
            fecha_periodo_cero = self.fecha_ejecutoria + relativedelta(months=+6)

        fechas_base = [
            self.fecha_ejecutoria,
            fecha_periodo_cero,
            self.fecha_cuenta_cobro,
            self.fecha_liquidar,
            self.fecha_vencimiento
        ]

        if self.codigo == "CPACA":
            fecha_periodo_diez = self.fecha_ejecutoria + relativedelta(months=+10)
            fechas_base.append(fecha_periodo_diez)

        fechas_periodos = self.generate_last_days(self.fecha_ejecutoria, self.fecha_vencimiento)
        fechas_periodos += fechas_base
        unique_fechas_periodos = sorted(list(set(fechas_periodos)))
        if unique_fechas_periodos[-1].month == unique_fechas_periodos[-2].month:
            unique_fechas_periodos.pop(-1)

        cont = 0
        fecha_anterior = None
        for fecha in unique_fechas_periodos:
            tasa = 0
            interes = 0
            #  Buscando tasas
            tasa_conf = self.env['ctm.tasas'].search(
                [('fecha_inicio', '<=', fecha), ('fecha_final', '>=', fecha)], limit=1
            )
            if not tasa_conf:
                raise ValidationError('No hay una tasa configurada para la fecha {0}'.format(fecha))

            # Todos los ajustes para CPACA
            if self.codigo == "CPACA":
                if fecha <= fecha_periodo_diez:
                    tasa = tasa_conf.dtf
                else:
                    tasa = tasa_conf.usura

                if (
                        fecha <= self.fecha_cuenta_cobro
                        and fecha > fecha_periodo_cero
                        and self.fecha_cuenta_cobro >= fecha_periodo_cero
                ):
                    tasa = 0
            if self.codigo == "CCA":
                tasa = tasa_conf.usura
                if (
                        fecha <= self.fecha_cuenta_cobro
                        and fecha > fecha_periodo_cero
                        and self.fecha_cuenta_cobro >= fecha_periodo_cero
                ):
                    tasa = 0
            if cont > 0:
                dias = (fecha - fecha_anterior).days
                interes = round(((1 + (tasa / 100)) ** (1 / 365) - 1), 6) * dias * self.valor_condena

            self.env['ctm.valoracion_6_4_resumen'].create({
                'valoracion_6_4_id': self.id,
                'fecha': fecha,
                'tasa': tasa,
                'interes': interes,
            })
            self.resultado += interes
            self.total_intereses += interes
            fecha_anterior = fecha
            cont += 1

    def _genera_tir_compra_6_4(self):
        for record in self:
            self.tir_compra_6_4 = 0
            cash_flows = [(-record.valor_giro, record.fecha_compra), (record.resultado, record.fecha_vencimiento)]
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
        self.tir_compra_6_4 = irr * 100

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


class CrearValoracion64(models.Model):
    _name = 'ctm.crear_valoracion_6_4'
    _description = "Crear Valoración 6.4"
    _inherit = []

    responsible = fields.Many2one('res.partner', 'Responsable')
    month = fields.Char('Mes de Periodo', required=1)
    year = fields.Char('Año de Periodo', required=1)
    status = fields.Selection([('sin_crear', 'Sin Crear'), ('creados', 'Creados')], default='sin_crear', string='Estado')

    name = fields.Char('Nombre')
    valoracion_6_4_ids = fields.One2many('ctm.detalle_valoracion_6_4', 'valoracion_6_4_id', 'Valoraciones')
    client_file = fields.Binary('Archivo')
    file_content = fields.Text('Texto archivo')
    delimiter = fields.Char('Delimitador', default=";")
    skip_first_line = fields.Boolean('Saltar primera linea', default=True)

    def crear_valoraciones(self):
        for valoracion in self.valoracion_6_4_ids:
            exists_valoracion = self.env['ctm.valoracion_6_4'].sudo().search([
                ('sentencia', '=', valoracion.sentencia.id),
            ])

            if not exists_valoracion:
                try:
                    created_valoracion = self.env['ctm.valoracion_6_4'].sudo().create({
                        'sentencia': valoracion.sentencia.id,
                    })
                    created_valoracion.generar_valoracion()
                except Exception as e:
                    raise ValidationError('error {0}. para sentencia {1}'.format(e, valoracion.sentencia.id))

        self.status = 'creados'

    def action_cargar_sentencias(self):
        self.ensure_one()
        if not self.delimiter:
            raise ValidationError('Debe ingresar el delimitador')
        if not self.client_file:
            raise ValidationError('Debe seleccionar el archivo')

        self.file_content = base64.decodebytes(self.client_file)
        content = self.file_content.replace('\n', '')
        lines = content.split('\r')

        for detalle in self.valoracion_6_4_ids:
            detalle.unlink()

        for i, line in enumerate(lines):
            if self.skip_first_line and i == 0:
                continue
            lista = line.split(self.delimiter)
            sentencia_name = lista[0]
            sentencia = self.env['ctm.sentencias'].sudo().search([('name', '=', sentencia_name)], limit=1)
            if not sentencia:
                raise ValidationError('No se encontró sentencia con nombre {0}'.format(sentencia_name))

            self.env['ctm.detalle_valoracion_6_4'].sudo().create({
                'valoracion_6_4_id': self.id,
                'sentencia': sentencia.id,
            })

    @api.model
    def create(self, var):
        res = super(CrearValoracion64, self).create(var)
        res.name = 'Valoración ' + res.month + '/' + res.year
        return res


class DetalleValoracion64(models.Model):
    _name = 'ctm.detalle_valoracion_6_4'
    _description = "Detalle Valoración 6.4"
    _inherit = []

    valoracion_6_4_id = fields.Many2one('ctm.crear_valoracion_6_4', 'Valoración 6.4', ondelete='cascade')
    sentencia = fields.Many2one('ctm.sentencias', 'Sentencia', required=1)
