# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64
import io
import xlsxwriter
from datetime import datetime


class InformeTIR(models.Model):
    _name = 'informe.tir'
    _description = 'Informe TIR'

    name = fields.Char('Nombre')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    month = fields.Selection([
        ('01', 'Enero'),
        ('02', 'Febrero'),
        ('03', 'Marzo'),
        ('04', 'Abril'),
        ('05', 'Mayo'),
        ('06', 'Junio'),
        ('07', 'Julio'),
        ('08', 'Agosto'),
        ('09', 'Septiembre'),
        ('10', 'Octubre'),
        ('11', 'Noviembre'),
        ('12', 'Diciembre'),
    ], string='Mes de Periodo', required=True)
    year = fields.Char('Año de Periodo', required=1)
    day = fields.Char('Día de Periodo', required=1)
    state = fields.Selection(selection=[('draft', 'Borrador'), ('processed', 'Procesado')], string='Estado',
                             default='draft')
    responsible = fields.Many2one('res.partner', 'Responsable')

    detalle_tir_ids = fields.One2many('informe.detalle.tir', 'informe_tir_id',
                                             'Detalle TIR')
    xls_output = fields.Binary(
        string='Descargar',
        readonly=True,
    )

    def generar_informe_tir(self):
        if not (self.month and self.year and self.day):
            raise ValidationError('Debe introducir un mes, un año y un día de periodo para este cargue')
        for detalle in self.detalle_tir_ids:
            detalle.unlink()

        extractos = self.env['ati.extracto'].search([
            ('month', '=', self.month),
            ('year', '=', self.year),
            ('state', '!=', 'draft')
        ])

        for extracto in extractos:
            #Extracto totales
            self.env['informe.detalle.tir'].create({
                'informe_tir_id': self.id,
                'cliente': extracto.cliente.id,
                'tir_mensual': extracto.tir_mensual,
                'tir_trimestral': extracto.tir_trimestral,
                'tir_semestral': extracto.tir_semestral,
                'tir_anual': extracto.tir_anual,
            })
            #Extracto por gestores
            #CSF
            gestor = self.env['ati.gestor'].search([('code', '=', 'CUANTUM')])
            for tipo_inv in ['FAC', 'LIB', 'SEN', 'MUT']:
                tipo = self.env['ati.investment.type'].search([('code', '=', tipo_inv)])
                if tipo == 'FAC':
                    mensual = extracto.cuantum_fac_mensual
                    trimestral = extracto.cuantum_fac_trimestral
                    semestral = extracto.cuantum_fac_semestral
                    anual = extracto.cuantum_fac_anual
                elif tipo == 'LIB':
                    mensual = extracto.cuantum_lib_mensual
                    trimestral = extracto.cuantum_lib_trimestral
                    semestral = extracto.cuantum_lib_semestral
                    anual = extracto.cuantum_lib_anual
                elif tipo == 'SEN':
                    mensual = extracto.cuantum_sen_mensual
                    trimestral = extracto.cuantum_sen_trimestral
                    semestral = extracto.cuantum_sen_semestral
                    anual = extracto.cuantum_sen_anual
                elif tipo == 'MUT':
                    mensual = extracto.cuantum_mut_mensual
                    trimestral = extracto.cuantum_mut_trimestral
                    semestral = extracto.cuantum_mut_semestral
                    anual = extracto.cuantum_mut_anual
                self.create_record_tir_gestor(extracto, gestor, tipo, mensual, trimestral, semestral, anual)

            #FCL
            gestor = self.env['ati.gestor'].search([('code', '=', 'FCL')])
            tipo = self.env['ati.investment.type'].search([('code', '=', 'LIB')])
            mensual = extracto.fcl_lib_mensual
            trimestral = extracto.fcl_lib_trimestral
            semestral = extracto.fcl_lib_semestral
            anual = extracto.fcl_lib_anual
            self.create_record_tir_gestor(extracto, gestor, tipo, mensual, trimestral, semestral, anual)

            #FCP
            gestor = self.env['ati.gestor'].search([('code', '=', 'FCP')])
            tipo = self.env['ati.investment.type'].search([('code', '=', 'SEN')])
            mensual = extracto.fcp_sen_mensual
            trimestral = extracto.fcp_sen_trimestral
            semestral = extracto.fcp_sen_semestral
            anual = extracto.fcp_sen_anual
            self.create_record_tir_gestor(extracto, gestor, tipo, mensual, trimestral, semestral, anual)

        self.responsible = self.env.user.partner_id
        self.state = 'processed'

    def create_record_tir_gestor(self, extracto, gestor, tipo, mensual, trimestral, semestral, anual):
        self.env['informe.detalle.tir'].create({
            'informe_tir_id': self.id,
            'cliente': extracto.cliente.id,
            'gestor_id': gestor.id,
            'tipo_id': tipo.id,
            'tir_mensual': mensual,
            'tir_trimestral': trimestral,
            'tir_semestral': semestral,
            'tir_anual': anual,
        })


    def action_exportar_xls(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Detalle TIR')
        money = workbook.add_format({'num_format': '0.000 %'})

        # Write headers
        sheet.write(0, 0, 'Cliente')
        sheet.write(0, 1, 'Gestor')
        sheet.write(0, 2, 'Tipo')
        sheet.write(0, 3, 'TIR Mensual')
        sheet.write(0, 4, 'TIR Trimestral')
        sheet.write(0, 5, 'TIR Semestral')
        sheet.write(0, 6, 'TIR Anual')

        sheet.set_column(0, 0, 50)
        sheet.set_column(1, 10, 20)

        # Write data
        row = 1
        for detalle in self.detalle_tir_ids:
            sheet.write(row, 0, detalle.cliente.name)
            sheet.write(row, 1, detalle.gestor_id.name)
            sheet.write(row, 2, detalle.tipo_id.name)
            sheet.write(row, 3, detalle.tir_mensual / 100, money)
            sheet.write(row, 4, detalle.tir_trimestral / 100, money)
            sheet.write(row, 5, detalle.tir_semestral / 100, money)
            sheet.write(row, 6, detalle.tir_anual / 100, money)
            row += 1

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        # Set xls_output field with the generated Excel file
        self.xls_output = base64.encodestring(generated_file)

        # Return the action for downloading the Excel file
        return {
            'context': self.env.context,
            'name': 'Informe TIR',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'informe.tir',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
        }

    def set_borrador_tir(self):
        for rec in self:
            if self.env.user.id in [8, 2, 10, 108]:
                rec.state = 'draft'
            else:
                raise ValidationError('Usted no tiene permisos para realizar esta acción')

    @api.model
    def create(self, var):
        res = super(InformeTIR, self).create(var)
        res.name = 'Informe TIR' + ' - ' + str(res.day) + "/" + res.month + "/" + res.year
        return res


class DetalleTIR(models.Model):
    _name = 'informe.detalle.tir'
    _description = 'Detalle TIR'

    informe_tir_id = fields.Many2one('informe.tir', string='Informe TIR')
    cliente = fields.Many2one('res.partner', 'Cliente')
    gestor_id = fields.Many2one('ati.gestor', 'Gestor')
    tipo_id = fields.Many2one('ati.investment.type', 'Tipo')
    tir_mensual = fields.Float('TIR Mensual')
    tir_trimestral = fields.Float('TIR Trimestral')
    tir_semestral = fields.Float('TIR Semestral')
    tir_anual = fields.Float('TIR Anual')
