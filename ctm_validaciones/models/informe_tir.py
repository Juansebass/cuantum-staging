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
            self.env['informe.detalle.tir'].create({
                'informe_tir_id': self.id,
                'cliente': extracto.cliente.id,
                'tir_mensual': extracto.tir_mensual,
                'tir_trimestral': extracto.tir_trimestral,
                'tir_semestral': extracto.tir_semestral,
                'tir_anual': extracto.tir_anual,
            })

        self.responsible = self.env.user.partner_id
        self.state = 'processed'

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

        sheet.set_column(0, 0, 50)
        sheet.set_column(1, 10, 20)

        # Write data
        row = 1
        for detalle in self.detalle_tir_ids:
            sheet.write(row, 0, detalle.cliente.name)
            sheet.write(row, 1, detalle.tir_mensual, money)
            sheet.write(row, 2, detalle.tir_trimestral, money)
            sheet.write(row, 3, detalle.tir_semestral, money)
            sheet.write(row, 4, detalle.tir_anual, money)
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
