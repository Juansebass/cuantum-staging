 # -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64
import matplotlib.pyplot as plt
from datetime import datetime
import calendar
import logging
from io import BytesIO ## for Python 3
import io
import xlsxwriter

class Validacion(models.Model):
    _name = 'ctm.validacion'
    _description = "Validación"
    _inherit = []

    name = fields.Char('Nombre')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    month = fields.Char('Mes de Periodo', required=1)
    year = fields.Char('Año de Periodo', required=1)
    state = fields.Selection(selection=[('draft','Borrador'),('processed','Procesado')],string='Estado',default='draft')
    responsible = fields.Many2one('res.partner', 'Responsable')

    detalle_validacion_ids = fields.One2many('ctm.validacion.detalle_validacion', 'validacion_id', 'Detalle de Validaciones')
    xls_output = fields.Binary(
        string='Descargar',
        readonly=True,
    )

    def generar_validacion(self):
        # Se valida si existe el periodo al cual se decea hacer un extractos, en el caso de existir se verifica que el
        # estado del mismo se encuentre en estado abierto de cargue
        if self.month and self.year:
            #Validación para que existan extractos
            pass
        else:
            raise ValidationError('Debe introducir un mes y año de periodo para este cargue')

        for detalle  in self.detalle_validacion_ids:
            detalle.unlink()

        clientes = self.env['res.partner'].search([('act_in', '=', 'activo'), ('vinculado', '=', True)])
        for cliente in clientes:
            titulo = self.env['ati.titulo'].search([('client.id', '=', cliente.id)])
            factoring_csf = sum(titulo['value'] for titulo in titulo.filtered(
                lambda x: x.manager.code == 'CUANTUM' and x.investment_type.code == 'FAC'))
            libranzas_csf =  sum(titulo['value'] for titulo in titulo.filtered(
                lambda x: x.manager.code == 'CUANTUM' and x.investment_type.code == 'LIB'))
            sentencias_csf =  sum(titulo['value'] for titulo in titulo.filtered(
                lambda x: x.manager.code == 'CUANTUM' and x.investment_type.code == 'SEN'))
            rpr_csf = 0
            libranzas_fcl = sum(titulo['value'] for titulo in titulo.filtered(
                lambda x: x.manager.code == 'FCL' and x.investment_type.code == 'LIB'))
            rpr_fcl = 0
            sentencias_fcp = sum(titulo['value'] for titulo in titulo.filtered(
                lambda x: x.manager.code == 'FCP' and x.investment_type.code == 'SEN'))
            rpr_fcp = 0
            total = sum([factoring_csf, libranzas_csf, sentencias_csf, rpr_csf, libranzas_fcl, rpr_fcl, sentencias_fcp, rpr_fcp])

            self.env['ctm.validacion.detalle_validacion'].create({
                'validacion_id': self.id,
                'cliente': cliente.id,
                'factoring_csf': factoring_csf,
                'libranzas_csf': libranzas_csf,
                'sentencias_csf': sentencias_csf,
                'rpr_csf': rpr_csf,
                'libranzas_fcl': libranzas_fcl,
                'rpr_fcl': rpr_fcl,
                'sentencias_fcp': sentencias_fcp,
                'rpr_fcp': rpr_fcp,
                'total': total,
            })

        self.responsible = self.env.user.partner_id
        self.state = 'processed'

    def set_borrador_validacion(self):
        for rec in self:
            if self.env.user.id in [8, 2, 10, 108]:
                rec.state = 'draft'
            else:
                raise ValidationError('Usted no tiene permisos para realizar esta acción')

    @api.model
    def create(self, var):
        res = super(Validacion, self).create(var)
        res.name = 'Informe Clientes' + ' - ' + res.month + "/" + res.year

        return res

    def action_exportar_xls(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Informe Clientes')
        money = workbook.add_format({'num_format': '$#,##0'})
        row = 1

        worksheet.write(row, 0, 'CLIENTE')
        worksheet.write(row, 1, 'FACTORING - CSF')
        worksheet.write(row, 2, 'LIBRANZAS - CSF')
        worksheet.write(row, 3, 'SENTENCIAS - CSF')
        worksheet.write(row, 4, 'RPR CSF')
        worksheet.write(row, 5, 'LIBRANZAS - FCL')
        worksheet.write(row, 6, 'RPR FCL')
        worksheet.write(row, 7, 'SENTENCIAS - STATUM')
        worksheet.write(row, 8, 'RPR STATUM')
        worksheet.write(row, 9, 'TOTAL')

        row += 1

        for detalle in self.detalle_validacion_ids:
            worksheet.write(row, 0, detalle.cliente.name)
            worksheet.write(row, 1, detalle.factoring_csf)
            worksheet.write(row, 2, detalle.libranzas_csf)
            worksheet.write(row, 3, detalle.sentencias_csf)
            worksheet.write(row, 4, detalle.rpr_csf)
            worksheet.write(row, 5, detalle.libranzas_fcl)
            worksheet.write(row, 6, detalle.rpr_fcl)
            worksheet.write(row, 7, detalle.sentencias_fcp)
            worksheet.write(row, 8, detalle.rpr_fcp)
            worksheet.write(row, 9, detalle.total)

            row += 1


        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()
        self.xls_output = base64.encodebytes(generated_file)

        return {
            'context': self.env.context,
            'name': 'Informe Clientes',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ctm.validacion',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }


class DetalleMovimiento(models.Model):
    _name = 'ctm.validacion.detalle_validacion'

    validacion_id = fields.Many2one('ctm.validacion','Validación')
    cliente = fields.Many2one('res.partner', 'Cliente')
    #CSF
    factoring_csf = fields.Float('FACTORING - CSF')
    libranzas_csf = fields.Float('LIBRANZAS - CSF')
    sentencias_csf = fields.Float('SENTENCIAS - CSF')
    rpr_csf = fields.Float('RPR CSF')
    #FCL
    libranzas_fcl = fields.Float('LIBRANZAS - FCL')
    rpr_fcl = fields.Float('RPR FCL')
    #FCP
    sentencias_fcp = fields.Float('SENTENCIAS - STATUM')
    rpr_fcp = fields.Float('RPR STATUM')

    total = fields.Float('TOTAL')
