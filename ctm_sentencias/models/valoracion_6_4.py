# -*- coding: utf-8 -*-

from odoo import models, fields, api  # type: ignore
from odoo.exceptions import ValidationError  # type: ignore
import base64
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import calendar
import scipy.optimize as opt  # type: ignore
import xlsxwriter  # type: ignore
import io
import numpy_financial as npf


class Valoracion64(models.Model):
    _name = 'ctm.valoracion_6_4'
    _description = "Valoración 6.4"
    _inherit = []

    name = fields.Char('Nombre')
    sentencia = fields.Many2one('ctm.sentencias', 'Sentencia', required=1)
    emisor = fields.Many2one('res.partner', 'Emisor')
    pagador = fields.Many2one('ctm.pagador', 'Pagador')
    codigo = fields.Char('Código')
    fecha_ejecutoria = fields.Date('Fecha de Ejecutoría')
    fecha_cuenta_cobro = fields.Date('Fecha de Cuenta de Cobro')
    fecha_liquidar = fields.Date('Fecha a Liquidar')
    valor_condena = fields.Float('Valor Condena')
    resultado = fields.Float('Resultado a Fecha de Vencimiento')
    total_intereses = fields.Float('Total Intereses')
    valoraciones_resumen_ids = fields.One2many('ctm.valoracion_6_4_resumen', 'valoracion_6_4_id', 'Resumen Valoración 6.4')
    responsible = fields.Many2one('res.partner', 'Responsable')
    state = fields.Selection(selection=[('draft', 'Borrador'), ('amortizado', 'Amortizado')], string='Estado', default='draft')
    tir_compra_6_4 = fields.Float('TIR Compra 6.4')

    nit_fcp_statum = fields.Char('NIT FCP STATUM (Comp 1)', related='sentencia.nit_fcp_statum')
    vehiculo = fields.Many2one('ctm.vehiculos', 'Vehículo', required=1, related='sentencia.vehiculo')
    vendedor = fields.Char('Vendedor', related='sentencia.vendedor')
    nemotecnico = fields.Char('Nemotecnico', related='sentencia.nemotecnico')
    fecha_vencimiento = fields.Date('Fecha de Vencimiento', related='sentencia.fecha_vencimiento')
    fecha_compra = fields.Date('Fecha de Compra', related='sentencia.fecha_compra')
    valor_giro = fields.Float('Valor Giro', related='sentencia.valor_giro')
    comision = fields.Float('Comisión', related='sentencia.comision')
    valor_contable_ayer = fields.Float('Valor Contable Ayer')
    precio = fields.Float('Precio', digits=(16, 7))
    valor_actual_6_4 = fields.Float('Valor Actual 6.4')
    simulacion_ids = fields.One2many('ctm.valoracion_simulacion', 'valoracion_6_4_id')

    def generar_valoracion(self):
        self.emisor = self.sentencia.emisor
        self.pagador = self.sentencia.pagador
        self.codigo = self.sentencia.codigo.name
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

        self.valor_actual_6_4 = self.resultado / ((1 + self.tir_compra_6_4 * 0.01) ** ((self.fecha_vencimiento - self.fecha_liquidar).days / 365))
        self.precio = (self.valor_actual_6_4 / self.valor_giro) * 100
        fecha_anterior = self.fecha_liquidar - timedelta(days=1)
        simulacion_anterior = self.simulacion_ids.filtered(lambda x: x.fecha_liquidar == fecha_anterior)
        if len(self.simulacion_ids) == 0:
            self.valor_contable_ayer = 0
        else:
            if len(simulacion_anterior) == 0 and self.state == 'amortizado':
                raise ValidationError("No existe simulación para la fecha anterior para la liquidación {0}".format(self.name))
            self.valor_contable_ayer = simulacion_anterior[0].valor_actual_6_4
        self.state = 'amortizado'
        self.responsible = self.env.user.partner_id

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

    def set_borrador_valoracion(self):
        for rec in self:
            if self.env.user.id in [8, 2, 10, 108]:
                rec.state = 'draft'
            else:
                raise ValidationError('Usted no tiene permisos para realizar esta acción')

    def generar_simulacion(self):
        for rec in self:
            #  Validando que no exista una simulación con la misma fecha a liquidar
            if len(rec.simulacion_ids.filtered(lambda x: x.fecha_liquidar == rec.fecha_liquidar)) > 0:
                raise ValidationError('Ya existe una simulación para la fecha {0}, de la valoración {1}'.format(rec.fecha_liquidar, rec.name))
            self.generar_valoracion()
            self.env['ctm.valoracion_simulacion'].create({
                'name': str(len(self.simulacion_ids) + 1),
                'valoracion_6_4_id': rec.id,
                'fecha_compra': rec.fecha_compra,
                'fecha_vencimiento': rec.fecha_vencimiento,
                'fecha_liquidar': rec.fecha_liquidar,
                'valor_condena': rec.valor_condena,
                'total_intereses': rec.total_intereses,
                'valor_giro': rec.valor_giro,
                'resultado': rec.resultado,
                'valor_actual_6_4': rec.valor_actual_6_4,
                'tir_compra_6_4': rec.tir_compra_6_4,
            })

    def action_view_simulaciones(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Simulaciones',
            'view_mode': 'tree',
            'res_model': 'ctm.valoracion_simulacion',
            'domain': [('valoracion_6_4_id', '=', self.id)],
            'context': "{'create': False}",
        }

    def create_txt(self):
        fechas = self.mapped('fecha_liquidar')

        if len(set(fechas)) > 1:
            raise ValidationError('Todos los registros deben tener la misma fecha a liquidar')

        contenido_txt = ""
        for rec in self:
            fecha = rec.fecha_liquidar.strftime('%Y%m%d')
            nit_fcp_statum = rec.nit_fcp_statum
            descripcion = rec.vehiculo.name
            if descripcion == 'CSF':
                raise ValidationError('Alguna de las sentencias es de Cuantum, por lo que no se genera precio')
            demandante = rec.emisor.name
            vendedor = rec.vendedor
            id_especie = rec.sentencia.name
            nemotecnico = rec.nemotecnico
            fecha_cuenta_cobro = rec.fecha_cuenta_cobro.strftime('%Y%m%d')
            fecha_emision = rec.fecha_ejecutoria.strftime('%Y%m%d')
            fecha_vencimiento = rec.fecha_vencimiento.strftime('%Y%m%d') if rec.fecha_vencimiento else ''
            nit_emisor = rec.pagador.vat
            nombre_emisor = rec.pagador.name
            fecha_compra = rec.fecha_compra.strftime('%Y%m%d') if rec.fecha_compra else ''
            nominal = round(rec.valor_condena, 2)
            valor_giro = round(rec.valor_giro, 2) if rec.valor_giro else 0
            comision = round(rec.comision, 2) if rec.comision else 0
            valor_contable_actual = round(rec.valor_actual_6_4, 2)
            valor_contable_ayer = round(rec.valor_contable_ayer, 2) if rec.valor_contable_ayer else 0
            precio = round(rec.precio, 7)
            contenido_txt += f"{fecha};{nit_fcp_statum};{descripcion};{demandante};{vendedor};{id_especie};{nemotecnico};{fecha_cuenta_cobro};{fecha_emision};{fecha_vencimiento};{nit_emisor};{nombre_emisor};{fecha_compra};{nominal};{valor_giro};{comision};{valor_contable_actual};{valor_contable_ayer};{precio:0.7f}\n"

        archivo_txt = base64.b64encode(contenido_txt.encode('utf-8'))

        attachment = self.env['ir.attachment'].create({
            'name': f"{fecha}.txt",
            'type': 'binary',
            'datas': archivo_txt,
            'res_model': 'ctm.valoracion_6_4',
            'res_id': self[0].id,  # Puedes modificar este ID si es necesario
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }

    def create_excel(self):
        fechas = self.mapped('fecha_liquidar')

        if len(set(fechas)) > 1:
            raise ValidationError('Todos los registros deben tener la misma fecha a liquidar')

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        # Crear formato de título
        title_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 14
        })
        # Formato bastardilla (cursiva)
        italic_format = workbook.add_format({'italic': True})
        worksheet.merge_range(0, 0, 0, 11, 'RELACIÓN DOCUMENTOS A DESCONTAR', title_format)
        row = 1
        worksheet.write(row, 6, 'Valor Futuro', italic_format)
        worksheet.write(row, 10, 'Valor de compra', italic_format)

        row += 1
        worksheet.write(row, 0, 'Fecha Opeación', italic_format)
        worksheet.write(row, 3, fechas[0].strftime('%Y-%m-%d'))

        row += 2
        worksheet.merge_range(row, 4, row, 5, 'Información pagador')
        worksheet.merge_range(row, 6, row, 9, 'Información operación')

        headers = [
            'Tipo Doc.', 'Nro. Doc.', 'Nit. Pagaduria - (GF Emisor)',
            'Pagaduria - EMISOR', 'Nit. Pagador', 'NOMBRES - APELLIDOS',
            'Vr. Futuro', 'Fecha vcmto Operación', 'Tasa Dcto e.a.', 'Plazo',
            'Valor Compra', 'Código CIIU Emisor'
        ]
        row += 1
        for col_num, header in enumerate(headers):
            worksheet.write(row, col_num, header)
        row += 1

        vr_futuro_sum = 0
        valor_compra_sum = 0
        formula_va_sum = 0
        for rec in self:
            tipo_doc = 'SENTENCIAS'
            nro_doc = rec.sentencia.name
            nit_pagaduria_emisor = rec.pagador.name.vat
            pagaduria_emisor = rec.pagador.name.name
            nit_pagador = rec.emisor.vat
            nombres_apellidos = rec.emisor.name
            vr_futuro = rec.resultado
            fecha_vcmto_operacion = rec.fecha_vencimiento.strftime('%Y-%m-%d') if rec.fecha_vencimiento else ''
            tasa_dcto_ea = rec.tir_compra_6_4
            plazo = (rec.fecha_vencimiento - rec.fecha_liquidar).days if rec.fecha_vencimiento and rec.fecha_liquidar else 0
            valor_compra = rec.valor_giro
            codigo_ciiu_emisor = '000'
            formula_va = npf.pv(
                rec.tir_compra_6_4 / 100, plazo / 365, 0, -vr_futuro
            )
            diferencia_formula_va = valor_compra - formula_va

            vr_futuro_sum += vr_futuro
            valor_compra_sum += valor_compra
            formula_va_sum += formula_va
            worksheet.write(row, 0, tipo_doc)
            worksheet.write(row, 1, nro_doc)
            worksheet.write(row, 2, nit_pagaduria_emisor)
            worksheet.write(row, 3, pagaduria_emisor)
            worksheet.write(row, 4, nit_pagador)
            worksheet.write(row, 5, nombres_apellidos)
            worksheet.write(row, 6, vr_futuro)
            worksheet.write(row, 7, fecha_vcmto_operacion)
            worksheet.write(row, 8, tasa_dcto_ea)
            worksheet.write(row, 9, plazo)
            worksheet.write(row, 10, valor_compra)
            worksheet.write(row, 11, codigo_ciiu_emisor)
            worksheet.write(row, 12, formula_va)
            worksheet.write(row, 13, diferencia_formula_va)
            row += 1

        row = 2
        worksheet.write(row, 6, vr_futuro_sum)
        worksheet.write(row, 10, valor_compra_sum)
        worksheet.write(row, 12, formula_va_sum)

        workbook.close()
        output.seek(0)
        archivo_excel = base64.b64encode(output.read())
        attachment = self.env['ir.attachment'].create({
            'name': 'relacion_documentos_a_descontar.xlsx',
            'type': 'binary',
            'datas': archivo_excel,
            'res_model': 'ctm.valoracion_6_4',
            'res_id': self[0].id,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }

    def create_excel_valoracion(self):
        fechas = self.mapped('fecha_liquidar')

        if len(set(fechas)) > 1:
            raise ValidationError('Todos los registros deben tener la misma fecha a liquidar')

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        row = 0
        headers = [
            'ID Portafolio', 'Fecha Reporte YYYY-MM-DD', 'Id Emisor',
            'No titulo', 'Valoración día', 'Valor Mora',
            'Valor deterioro'
        ]
        for col_num, header in enumerate(headers):
            worksheet.write(row, col_num, header)

        row += 1

        for rec in self:
            id_portafolio = '10246'
            fecha_reporte = rec.fecha_liquidar.strftime('%Y%m%d')
            id_emisor = rec.pagador.name.vat
            no_titulo = rec.sentencia.name
            valoracion_dia = rec.valor_actual_6_4
            valor_mora = 0
            valor_deterioro = 0
            worksheet.write(row, 0, id_portafolio)
            worksheet.write(row, 1, fecha_reporte)
            worksheet.write(row, 2, id_emisor)
            worksheet.write(row, 3, no_titulo)
            worksheet.write(row, 4, valoracion_dia)
            worksheet.write(row, 5, valor_mora)
            worksheet.write(row, 6, valor_deterioro)
            row += 1

        workbook.close()
        output.seek(0)
        archivo_excel = base64.b64encode(output.read())
        attachment = self.env['ir.attachment'].create({
            'name': 'valoracion_archivo.xlsx',
            'type': 'binary',
            'datas': archivo_excel,
            'res_model': 'ctm.valoracion_6_4',
            'res_id': self[0].id,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }

    def generate_simulations(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ctm.valoracion_6_4_simulation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_date': fields.Date.today(),
                'active_ids': self.ids,
            },
        }


class Valoracion64Resumen(models.Model):
    _name = 'ctm.valoracion_6_4_resumen'
    _description = "Valoraciones 6.4 Resumen Cuantum"
    _inherit = []

    valoracion_6_4_id = fields.Many2one('ctm.valoracion_6_4', 'Valoración 6.4', ondelete='cascade')
    fecha = fields.Date('Fecha', required=1)
    tasa = fields.Float('Tasa', digits=(10, 6))
    interes = fields.Float('Interés')


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
                    raise ValidationError('error {0}. para sentencia {1}'.format(e, valoracion.sentencia.name))

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


class ValoracionSimulacion(models.Model):
    _name = 'ctm.valoracion_simulacion'
    _description = "Valoración Simulación"
    _inherit = []

    name = fields.Char('Nombre', required=True)
    valoracion_6_4_id = fields.Many2one('ctm.valoracion_6_4', 'Valoración 6.4', required=True, ondelete='cascade')
    fecha_compra = fields.Date('Fecha de Compra')
    fecha_vencimiento = fields.Date('Fecha de Vencimiento')
    fecha_liquidar = fields.Date('Fecha a Liquidar')
    valor_condena = fields.Float('Valor Condena')
    total_intereses = fields.Float('Total Intereses')
    valor_giro = fields.Float('Valor Giro')
    resultado = fields.Float('Resultado a Fecha de Vencimiento')
    valor_actual_6_4 = fields.Float('Valor Actual 6.4')
    tir_compra_6_4 = fields.Float('TIR Compra 6.4')
