# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64
import io
import xlsxwriter


class InformeAdministracion(models.Model):
    _name = 'ctm.informe_administracion'
    _description = "Informe Administración"
    _inherit = []

    name = fields.Char('Nombre')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    month = fields.Char('Mes de Periodo', required=1)
    year = fields.Char('Año de Periodo', required=1)
    day = fields.Char('Día de Periodo', required=1)
    state = fields.Selection(selection=[('draft', 'Borrador'), ('processed', 'Procesado')], string='Estado',
                             default='draft')
    responsible = fields.Many2one('res.partner', 'Responsable')

    detalle_informe_administracion_ids = fields.One2many('ctm.validacion.detalle_informe_administracion', 'informe_administracion_id','Detalle de Administración')
    xls_output = fields.Binary(
        string='Descargar',
        readonly=True,
    )

    def generar_informe_administracion(self):

        if self.month and self.year and self.day:
            #Validación para que existan extractos
            pass
        else:
            raise ValidationError('Debe introducir un mes un año y un día de periodo para este cargue')

        for detalle  in self.detalle_informe_administracion_ids:
            detalle.unlink()

        clientes = self.env['res.partner'].search([('act_in', '=', 'activo'), ('vinculado', '=', True)])

        for cliente in clientes:
            objetos = self.env['ati.rendimientos.administracion'].search(
                [('buyer.id', '=', cliente.id)]).filtered(
                lambda x: x.date.month == int(self.month) and
                          x.date.year == int(self.year)
            )

            administracion_factoring_csf = sum(objetos['value'] for objeto in objetos.filtered(
                lambda x: x.manager.code == 'CUANTUM' and x.investment_type.code == 'FAC' and x.movement_type.code == 'ADMINISTRACION'))
            rendimiento_factoring_csf = sum(objetos['value'] for objeto in objetos.filtered(
                lambda
                    x: x.manager.code == 'CUANTUM' and x.investment_type.code == 'FAC' and x.movement_type.code == 'RENDIMIENTO'))
            administracion_libranzas_csf= sum(objetos['value'] for objeto in objetos.filtered(
                lambda
                    x: x.manager.code == 'CUANTUM' and x.investment_type.code == 'LIB' and x.movement_type.code == 'ADMINISTRACION'))
            rendimiento_libranzas_csf = sum(objetos['value'] for objeto in objetos.filtered(
                lambda
                    x: x.manager.code == 'CUANTUM' and x.investment_type.code == 'LIB' and x.movement_type.code == 'RENDIMIENTO'))
            administracion_sentencias_csf = sum(objetos['value'] for objeto in objetos.filtered(
                lambda
                    x: x.manager.code == 'CUANTUM' and x.investment_type.code == 'SEN' and x.movement_type.code == 'ADMINISTRACION'))
            rendimiento_sentencias_csf = sum(objetos['value'] for objeto in objetos.filtered(
                lambda
                    x: x.manager.code == 'CUANTUM' and x.investment_type.code == 'SEN' and x.movement_type.code == 'RENDIMIENTO'))
            administracion_mutuos_csf = sum(objetos['value'] for objeto in objetos.filtered(
                lambda
                    x: x.manager.code == 'CUANTUM' and x.investment_type.code == 'MUT' and x.movement_type.code == 'ADMINISTRACION'))
            rendimiento_mutuos_csf = sum(objetos['value'] for objeto in objetos.filtered(
                lambda
                    x: x.manager.code == 'CUANTUM' and x.investment_type.code == 'MUT' and x.movement_type.code == 'RENDIMIENTO'))

            administracion_libranzas_fcl = sum(objetos['value'] for objeto in objetos.filtered(
                lambda
                    x: x.manager.code == 'FCL' and x.investment_type.code == 'LIB' and x.movement_type.code == 'ADMINISTRACION'))
            rendimiento_libranzas_fcl = sum(objetos['value'] for objeto in objetos.filtered(
                lambda
                    x: x.manager.code == 'FCL' and x.investment_type.code == 'LIB' and x.movement_type.code == 'RENDIMIENTO'))

            administracion_sentencias_fcp  = sum(objetos['value'] for objeto in objetos.filtered(
                lambda
                    x: x.manager.code == 'FCP' and x.investment_type.code == 'SEN' and x.movement_type.code == 'ADMINISTRACION'))
            rendimiento_sentencias_fcp  = sum(objetos['value'] for objeto in objetos.filtered(
                lambda
                    x: x.manager.code == 'FCP' and x.investment_type.code == 'SEN' and x.movement_type.code == 'RENDIMIENTO'))

            administracion_rpr_csf = sum(recurso.value for recurso in cliente.recursos_recompra_csf_ids.filtered(
                lambda x: x.date.month == int(self.month) and
                          x.date.year == int(self.year) and
                          x.movement_type.code == 'ADMINISTRACION'
            ))
            rendimiento_rpr_csf = sum(recurso.value for recurso in cliente.recursos_recompra_csf_ids.filtered(
                lambda x: x.date.month == int(self.month) and
                          x.date.year == int(self.year) and
                          x.movement_type.code == 'RENDIMIENTO'
            ))

            # administracion_rpr_fcl = sum(recurso.value for recurso in cliente.recursos_recompra_fcl_ids.filtered(
            #     lambda x: x.date.month == int(self.month) and
            #               x.date.year == int(self.year) and
            #               x.movement_type.code == 'ADMINISTRACION'
            # ))
            # rendimiento_rpr_fcl = sum(recurso.value for recurso in cliente.recursos_recompra_fcl_ids.filtered(
            #     lambda x: x.date.month == int(self.month) and
            #               x.date.year == int(self.year) and
            #               x.movement_type.code == 'RENDIMIENTO'
            # ))
            administracion_rpr_fcl = 0
            rendimiento_rpr_fcl = 0

            administracion_rpr_fcp = sum(recurso.value for recurso in cliente.recursos_recompra_fcp_ids.filtered(
                lambda x: x.date.month == int(self.month) and
                          x.date.year == int(self.year) and
                          x.movement_type.code == 'ADMINISTRACION'
            ))
            rendimiento_rpr_fcp = sum(recurso.value for recurso in cliente.recursos_recompra_fcp_ids.filtered(
                lambda x: x.date.month == int(self.month) and
                          x.date.year == int(self.year) and
                          x.movement_type.code == 'RENDIMIENTO'
            ))

            administracion_total = sum([
                administracion_factoring_csf,
                administracion_libranzas_csf,
                administracion_sentencias_csf,
                administracion_mutuos_csf,
                administracion_rpr_csf,
                administracion_libranzas_fcl,
                administracion_rpr_fcl,
                administracion_sentencias_fcp,
                administracion_rpr_fcp,
            ])

            rendimiento_total = sum([
                rendimiento_factoring_csf,
                rendimiento_libranzas_csf,
                rendimiento_sentencias_csf,
                rendimiento_mutuos_csf,
                rendimiento_rpr_csf,
                rendimiento_libranzas_fcl,
                rendimiento_rpr_fcl,
                rendimiento_sentencias_fcp,
                rendimiento_rpr_fcp,
            ])



            self.env['ctm.validacion.detalle_informe_administracion'].create({
                'informe_administracion_id': self.id,
                'cliente': cliente.id,
                'administracion_factoring_csf': administracion_factoring_csf,
                'rendimiento_factoring_csf': rendimiento_factoring_csf,
                'administracion_libranzas_csf': administracion_libranzas_csf,
                'rendimiento_libranzas_csf': rendimiento_libranzas_csf,
                'administracion_sentencias_csf': administracion_sentencias_csf,
                'rendimiento_sentencias_csf': rendimiento_sentencias_csf,
                'administracion_mutuos_csf': administracion_mutuos_csf,
                'rendimiento_mutuos_csf': rendimiento_mutuos_csf,
                'administracion_rpr_csf': administracion_rpr_csf,
                'rendimiento_rpr_csf': rendimiento_rpr_csf,
                'administracion_libranzas_fcl': administracion_libranzas_fcl,
                'rendimiento_libranzas_fcl': rendimiento_libranzas_fcl,
                'administracion_rpr_fcl': administracion_rpr_fcl,
                'rendimiento_rpr_fcl': rendimiento_rpr_fcl,
                'administracion_sentencias_fcp': administracion_sentencias_fcp,
                'rendimiento_sentencias_fcp': rendimiento_sentencias_fcp,
                'administracion_rpr_fcp': administracion_rpr_fcp,
                'rendimiento_rpr_fcp': rendimiento_rpr_fcp,
                'administracion_total': administracion_total,
                'rendimiento_total': rendimiento_total,

            })

        self.responsible = self.env.user.partner_id
        self.state = 'processed'
    def set_borrador_informe_administracion(self):
        for rec in self:
            if self.env.user.id in [8, 2, 10, 108]:
                rec.state = 'draft'
            else:
                raise ValidationError('Usted no tiene permisos para realizar esta acción')


    @api.model
    def create(self, var):
        res = super(InformeAdministracion, self).create(var)
        res.name = 'Informe Administración y Rendimiento' + ' - ' + str(res.day) + "/" + res.month + "/" + res.year
        return res

    def action_exportar_xls(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Informe Administración y Rendimientos')
        money = workbook.add_format({'num_format': '$#,##0'})
        row = 0

        worksheet.write(row, 0, 'CLIENTE')
        worksheet.write(row, 1, 'FACTORING - CSF')
        worksheet.write(row, 3, 'LIBRANZAS - CSF')
        worksheet.write(row, 5, 'SENTENCIAS - CSF')
        worksheet.write(row, 7, 'MUTUOS - CSF')
        worksheet.write(row, 9, 'RPR CSF')
        worksheet.write(row, 11, 'LIBRANZAS - FCL')
        worksheet.write(row, 13, 'RPR FCL')
        worksheet.write(row, 15, 'SENTENCIAS - STATUM')
        worksheet.write(row, 17, 'RPR STATUM')
        worksheet.write(row, 19, 'TOTAL')

        row += 1

        worksheet.write(row, 1, 'ADMINISTRACIÓN')
        worksheet.write(row, 2, 'RENDIMIENTO')
        worksheet.write(row, 3, 'ADMINISTRACIÓN')
        worksheet.write(row, 4, 'RENDIMIENTO')
        worksheet.write(row, 5, 'ADMINISTRACIÓN')
        worksheet.write(row, 6, 'RENDIMIENTO')
        worksheet.write(row, 7, 'ADMINISTRACIÓN')
        worksheet.write(row, 8, 'RENDIMIENTO')
        worksheet.write(row, 9, 'ADMINISTRACIÓN')
        worksheet.write(row, 10, 'RENDIMIENTO')
        worksheet.write(row, 11, 'ADMINISTRACIÓN')
        worksheet.write(row, 12, 'RENDIMIENTO')
        worksheet.write(row, 13, 'ADMINISTRACIÓN')
        worksheet.write(row, 14, 'RENDIMIENTO')
        worksheet.write(row, 15, 'ADMINISTRACIÓN')
        worksheet.write(row, 16, 'RENDIMIENTO')
        worksheet.write(row, 17, 'ADMINISTRACIÓN')
        worksheet.write(row, 18, 'RENDIMIENTO')
        worksheet.write(row, 19, 'ADMINISTRACIÓN')
        worksheet.write(row, 20, 'RENDIMIENTO')

        worksheet.set_column(0, 0, 50)
        worksheet.set_column(1, 20, 20)

        row += 1

        for detalle in self.detalle_informe_administracion_ids:
            worksheet.write(row, 0, detalle.cliente.name)
            worksheet.write(row, 1, detalle.administracion_factoring_csf, money)
            worksheet.write(row, 2, detalle.rendimiento_factoring_csf, money)
            worksheet.write(row, 3, detalle.administracion_libranzas_csf, money)
            worksheet.write(row, 4, detalle.rendimiento_libranzas_csf, money)
            worksheet.write(row, 5, detalle.administracion_sentencias_csf, money)
            worksheet.write(row, 6, detalle.rendimiento_sentencias_csf, money)
            worksheet.write(row, 7, detalle.administracion_mutuos_csf, money)
            worksheet.write(row, 8, detalle.rendimiento_mutuos_csf, money)
            worksheet.write(row, 9, detalle.administracion_rpr_csf, money)
            worksheet.write(row, 10, detalle.rendimiento_rpr_csf, money)
            worksheet.write(row, 11, detalle.administracion_libranzas_fcl, money)
            worksheet.write(row, 12, detalle.rendimiento_libranzas_fcl, money)
            worksheet.write(row, 13, detalle.administracion_rpr_fcl, money)
            worksheet.write(row, 14, detalle.rendimiento_rpr_fcl, money)
            worksheet.write(row, 15, detalle.administracion_sentencias_fcp, money)
            worksheet.write(row, 16, detalle.rendimiento_sentencias_fcp, money)
            worksheet.write(row, 17, detalle.administracion_rpr_fcp, money)
            worksheet.write(row, 18, detalle.rendimiento_rpr_fcp, money)
            worksheet.write(row, 19, detalle.administracion_total, money)
            worksheet.write(row, 20, detalle.rendimiento_total, money)

            row += 1

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()
        self.xls_output = base64.encodebytes(generated_file)

        return {
            'context': self.env.context,
            'name': 'Informe Administración y Rendimientos',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ctm.informe_administracion',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
        }


class DetalleMovimiento(models.Model):
    _name = 'ctm.validacion.detalle_informe_administracion'

    informe_administracion_id = fields.Many2one('ctm.informe_administracion','Informe Administracion')
    cliente = fields.Many2one('res.partner', 'Cliente')
    #CSF
    administracion_factoring_csf = fields.Float('ADM FACTORING - CSF')
    rendimiento_factoring_csf = fields.Float('REND FACTORING - CSF')
    administracion_libranzas_csf = fields.Float('ADM LIBRANZAS - CSF')
    rendimiento_libranzas_csf = fields.Float(' REND LIBRANZAS - CSF')
    administracion_sentencias_csf = fields.Float('ADM SENTENCIAS - CSF')
    rendimiento_sentencias_csf = fields.Float('REND SENTENCIAS - CSF')
    administracion_mutuos_csf = fields.Float('ADM MUTUOS - CSF')
    rendimiento_mutuos_csf = fields.Float('REND MUTUOS - CSF')
    administracion_rpr_csf = fields.Float('ADM RPR CSF')
    rendimiento_rpr_csf = fields.Float('REND RPR CSF')
    #FCL
    administracion_libranzas_fcl = fields.Float('ADM LIBRANZAS - FCL')
    rendimiento_libranzas_fcl = fields.Float('REND LIBRANZAS - FCL')
    administracion_rpr_fcl = fields.Float('ADM RPR FCL')
    rendimiento_rpr_fcl = fields.Float('REND RPR FCL')
    #FCP
    administracion_sentencias_fcp = fields.Float('ADM SENTENCIAS - STATUM')
    rendimiento_sentencias_fcp = fields.Float('REND SENTENCIAS - STATUM')
    administracion_rpr_fcp = fields.Float('ADM RPR STATUM')
    rendimiento_rpr_fcp = fields.Float('REND RPR STATUM')

    administracion_total = fields.Float('ADM TOTAL')
    rendimiento_total = fields.Float('REND TOTAL')