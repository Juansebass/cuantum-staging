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
                'csf_lib_mensual': extracto.cuantum_lib_mensual,
                'csf_lib_trimestral': extracto.cuantum_lib_trimestral,
                'csf_lib_semestral': extracto.cuantum_lib_semestral,
                'csf_lib_anual': extracto.cuantum_lib_anual,
                'csf_fac_mensual': extracto.cuantum_fac_mensual,
                'csf_fac_trimestral': extracto.cuantum_fac_trimestral,
                'csf_fac_semestral': extracto.cuantum_fac_semestral,
                'csf_fac_anual': extracto.cuantum_fac_anual,
                'csf_sen_mensual': extracto.cuantum_sen_mensual,
                'csf_sen_trimestral': extracto.cuantum_sen_trimestral,
                'csf_sen_semestral': extracto.cuantum_sen_semestral,
                'csf_sen_anual': extracto.cuantum_sen_anual,
                'csf_mut_mensual': extracto.cuantum_mut_mensual,
                'csf_mut_trimestral': extracto.cuantum_mut_trimestral,
                'csf_mut_semestral': extracto.cuantum_mut_semestral,
                'csf_mut_anual': extracto.cuantum_mut_anual,
                'fcl_lib_mensual': extracto.fcl_lib_mensual,
                'fcl_lib_trimestral': extracto.fcl_lib_trimestral,
                'fcl_lib_semestral': extracto.fcl_lib_semestral,
                'fcl_lib_anual': extracto.fcl_lib_anual,
                'fcp_sen_mensual': extracto.fcp_sen_mensual,
                'fcp_sen_trimestral': extracto.fcp_sen_trimestral,
                'fcp_sen_semestral': extracto.fcp_sen_semestral,
                'fcp_sen_anual': extracto.fcp_sen_anual,
            })
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
        sheet.write(0, 1, 'TIR Mensual')
        sheet.write(0, 2, 'TIR Trimestral')
        sheet.write(0, 3, 'TIR Semestral')
        sheet.write(0, 4, 'TIR Anual')
        sheet.write(0, 5, 'CSF-LIB-Mensual')
        sheet.write(0, 6, 'CSF-LIB-Trimestral')
        sheet.write(0, 7, 'CSF-LIB-Semestral')
        sheet.write(0, 8, 'CSF-LIB-Anual')
        sheet.write(0, 9, 'CSF-SEN-Mensual')
        sheet.write(0, 10, 'CSF-SEN-Trimestral')
        sheet.write(0, 11, 'CSF-SEN-Semestral')
        sheet.write(0, 12, 'CSF-SEN-Anual')
        sheet.write(0, 13, 'CSF-MUT-Mensual')
        sheet.write(0, 14, 'CSF-MUT-Trimestral')
        sheet.write(0, 15, 'CSF-MUT-Semestral')
        sheet.write(0, 16, 'CSF-MUT-Anual')
        sheet.write(0, 17, 'CSF-FAC-Mensual')
        sheet.write(0, 18, 'CSF-FAC-Trimestral')
        sheet.write(0, 19, 'CSF-FAC-Semestral')
        sheet.write(0, 20, 'CSF-FAC-Anual')
        sheet.write(0, 21, 'FCL-LIB-Mensual')
        sheet.write(0, 22, 'FCL-LIB-Trimestral')
        sheet.write(0, 23, 'FCL-LIB-Semestral')
        sheet.write(0, 24, 'FCL-LIB-Anual')
        sheet.write(0, 25, 'FCP-SEN-Mensual')
        sheet.write(0, 26, 'FCP-SEN-Trimestral')
        sheet.write(0, 27, 'FCP-SEN-Semestral')
        sheet.write(0, 28, 'FCP-SEN-Anual')




        sheet.set_column(0, 0, 50)
        sheet.set_column(1, 10, 30)

        # Write data
        row = 1
        for detalle in self.detalle_tir_ids:
            sheet.write(row, 0, detalle.cliente.name)
            sheet.write(row, 1, detalle.tir_mensual / 100, money)
            sheet.write(row, 2, detalle.tir_trimestral / 100, money)
            sheet.write(row, 3, detalle.tir_semestral / 100, money)
            sheet.write(row, 4, detalle.tir_anual / 100, money)
            sheet.write(row, 5, detalle.csf_lib_mensual / 100, money)
            sheet.write(row, 6, detalle.csf_lib_trimestral / 100, money)
            sheet.write(row, 7, detalle.csf_lib_semestral / 100, money)
            sheet.write(row, 8, detalle.csf_lib_anual / 100, money)
            sheet.write(row, 9, detalle.csf_sen_mensual / 100, money)
            sheet.write(row, 10, detalle.csf_sen_trimestral / 100, money)
            sheet.write(row, 11, detalle.csf_sen_semestral / 100, money)
            sheet.write(row, 12, detalle.csf_sen_anual / 100, money)
            sheet.write(row, 13, detalle.csf_mut_mensual / 100, money)
            sheet.write(row, 14, detalle.csf_mut_trimestral / 100, money)
            sheet.write(row, 15, detalle.csf_mut_semestral / 100, money)
            sheet.write(row, 16, detalle.csf_mut_anual / 100, money)
            sheet.write(row, 17, detalle.csf_fac_mensual / 100, money)
            sheet.write(row, 18, detalle.csf_fac_trimestral / 100, money)
            sheet.write(row, 19, detalle.csf_fac_semestral / 100, money)
            sheet.write(row, 20, detalle.csf_fac_anual / 100, money)
            sheet.write(row, 21, detalle.fcl_lib_mensual / 100, money)
            sheet.write(row, 22, detalle.fcl_lib_trimestral / 100, money)
            sheet.write(row, 23, detalle.fcl_lib_semestral / 100, money)
            sheet.write(row, 24, detalle.fcl_lib_anual / 100, money)
            sheet.write(row, 25, detalle.fcp_sen_mensual / 100, money)
            sheet.write(row, 26, detalle.fcp_sen_trimestral / 100, money)
            sheet.write(row, 27, detalle.fcp_sen_semestral / 100, money)
            sheet.write(row, 28, detalle.fcp_sen_anual / 100, money)
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
    tir_mensual = fields.Float('TIR Mensual')
    tir_trimestral = fields.Float('TIR Trimestral')
    tir_semestral = fields.Float('TIR Semestral')
    tir_anual = fields.Float('TIR Anual')
    csf_lib_mensual = fields.Float('CSF-LIB-Mensual')
    csf_lib_trimestral = fields.Float('CSF-LIB-Trimestral')
    csf_lib_semestral = fields.Float('CSF-LIB-Semestral')
    csf_lib_anual = fields.Float('CSF-LIB-Anual')
    csf_sen_mensual = fields.Float('CSF-SEN-Mensual')
    csf_sen_trimestral = fields.Float('CSF-SEN-Trimestral')
    csf_sen_semestral = fields.Float('CSF-SEN-Semestral')
    csf_sen_anual = fields.Float('CSF-SEN-Anual')
    csf_mut_mensual = fields.Float('CSF-MUT-Mensual')
    csf_mut_trimestral = fields.Float('CSF-MUT-Trimestral')
    csf_mut_semestral = fields.Float('CSF-MUT-Semestral')
    csf_mut_anual = fields.Float('CSF-MUT-Anual')
    csf_fac_mensual = fields.Float('CSF-FAC-Mensual')
    csf_fac_trimestral = fields.Float('CSF-FAC-Trimestral')
    csf_fac_semestral = fields.Float('CSF-FAC-Semestral')
    csf_fac_anual = fields.Float('CSF-FAC-Anual')
    fcl_lib_mensual = fields.Float('FCL-LIB-Mensual')
    fcl_lib_trimestral = fields.Float('FCL-LIB-Trimestral')
    fcl_lib_semestral = fields.Float('FCL-LIB-Semestral')
    fcl_lib_anual = fields.Float('FCL-LIB-Anual')
    fcp_sen_mensual = fields.Float('FCP-SEN-Mensual')
    fcp_sen_trimestral = fields.Float('FCP-SEN-Trimestral')
    fcp_sen_semestral = fields.Float('FCP-SEN-Semestral')
    fcp_sen_anual = fields.Float('FCP-SEN-Anual')
