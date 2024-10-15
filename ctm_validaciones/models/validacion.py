 # -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64
import io
import xlsxwriter
from datetime import datetime

class Validacion(models.Model):
    _name = 'ctm.validacion'
    _description = "Validación"
    _inherit = []

    name = fields.Char('Nombre')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    month = fields.Char('Mes de Periodo', required=1)
    year = fields.Char('Año de Periodo', required=1)
    day = fields.Char('Día de Periodo', required=1)
    state = fields.Selection(selection=[('draft','Borrador'),('processed','Procesado')],string='Estado',default='draft')
    responsible = fields.Many2one('res.partner', 'Responsable')

    detalle_validacion_ids = fields.One2many('ctm.validacion.detalle_validacion', 'validacion_id', 'Detalle de Validaciones')
    xls_output = fields.Binary(
        string='Descargar',
        readonly=True,
    )
    def _get_total_titlles_period(self, titulos, manager_code, investment_code):
        total = 0
        titulos_temp = titulos.filtered(
            lambda x: x.manager.code == manager_code and x.investment_type.code == investment_code)

        for titulo_mes in titulos_temp:
            if titulo_mes.periodo == self.month + '/' + self.year:
                total += titulo_mes.value

        return total

    def _get_rpr_total_period(self, recursos):
        total = 0
        for recurso in recursos:
            if recurso.movement_type.name in ['Adición', 'Aplicación de recaudo', 'Rendimiento']:
                total += recurso.value
            else:
                total -= recurso.value
        return total

    def generar_validacion(self):
        # Se valida si existe el periodo al cual se decea hacer un extractos, en el caso de existir se verifica que el
        # estado del mismo se encuentre en estado abierto de cargue
        if self.month and self.year and self.day:
            #Validación para que existan extractos
            pass
        else:
            raise ValidationError('Debe introducir un mes un año y un día de periodo para este cargue')

        for detalle  in self.detalle_validacion_ids:
            detalle.unlink()



        clientes = self.env['res.partner'].search([('act_in', '=', 'activo'), ('vinculado', '=', True)])
        for cliente in clientes:
            titulos = self.env['ati.titulo.historico'].search([('client.id', '=', cliente.id)])

            factoring_csf = self._get_total_titlles_period(titulos, 'CUANTUM', 'FAC')
            libranzas_csf = self._get_total_titlles_period(titulos, 'CUANTUM', 'LIB')
            sentencias_csf = self._get_total_titlles_period(titulos, 'CUANTUM', 'SEN')
            mutuos_csf = self._get_total_titlles_period(titulos, 'CUANTUM', 'MUT')
            libranzas_fcl = self._get_total_titlles_period(titulos, 'FCL', 'LIB')
            sentencias_fcp = self._get_total_titlles_period(titulos, 'FCP', 'SEN')
            si_fcp  = self._get_total_titlles_period(titulos, 'FCP', 'S1')
            sii_fcp = self._get_total_titlles_period(titulos, 'FCP', 'S2')

            date_tmp = (datetime.strptime('01/' + self.month + '/' + self.year, '%d/%m/%Y')).date()
            if self.month == '12':
                date_next_tmp = (datetime.strptime('01/' + '01/' + str(int(self.year) + 1), '%d/%m/%Y')).date()
            else:
                date_next_tmp = (
                    datetime.strptime('01/' + str(int(self.month) + 1) + '/' + self.year, '%d/%m/%Y')).date()
            try:
                temp_rpr_fcl = cliente.recursos_recompra_fcl_ids.filtered(lambda x: x.date < date_next_tmp)
                rpr_fcl = self._get_rpr_total_period(temp_rpr_fcl)
                temp_rpr_csf = cliente.recursos_recompra_csf_ids.filtered(lambda x: x.date < date_next_tmp)
                rpr_csf = self._get_rpr_total_period(temp_rpr_csf)
                temp_rpr_fcp = cliente.recursos_recompra_fcp_ids.filtered(lambda x: x.date < date_next_tmp)
                rpr_fcp = self._get_rpr_total_period(temp_rpr_fcp)

                total = sum([factoring_csf, libranzas_csf, sentencias_csf,mutuos_csf, rpr_csf, libranzas_fcl, rpr_fcl, sentencias_fcp, si_fcp, sii_fcp, rpr_fcp])
            except:
                raise ValidationError('El cliente {0} no tiene alguna fecha definida'.format(cliente.name))

            self.env['ctm.validacion.detalle_validacion'].create({
                'validacion_id': self.id,
                'cliente': cliente.id,
                'factoring_csf': factoring_csf,
                'libranzas_csf': libranzas_csf,
                'sentencias_csf': sentencias_csf,
                'mutuos_csf': mutuos_csf,
                'rpr_csf': rpr_csf,
                'libranzas_fcl': libranzas_fcl,
                'rpr_fcl': rpr_fcl,
                'sentencias_fcp': sentencias_fcp,
                'si_fcp': si_fcp,
                'sii_fcp': sii_fcp,
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
        res.name = 'Informe Clientes' + ' - ' + str(res.day) + "/"  + res.month + "/" + res.year

        return res

    def action_exportar_xls(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Informe Clientes')
        money = workbook.add_format({'num_format': '$#,##0'})
        row = 0

        worksheet.write(row, 0, 'CLIENTE')
        worksheet.write(row, 1, 'FACTORING - CSF')
        worksheet.write(row, 2, 'LIBRANZAS - CSF')
        worksheet.write(row, 3, 'SENTENCIAS - CSF')
        worksheet.write(row, 4, 'MUTUOS - CSF')
        worksheet.write(row, 5, 'RPR CSF')
        worksheet.write(row, 6, 'LIBRANZAS - FCL')
        worksheet.write(row, 7, 'RPR FCL')
        worksheet.write(row, 8, 'SENTENCIAS - STATUM')
        worksheet.write(row, 9, 'SI - STATUM')
        worksheet.write(row, 10, 'SII - STATUM')
        worksheet.write(row, 11, 'RPR STATUM')
        worksheet.write(row, 12, 'TOTAL')

        worksheet.set_column(0, 0, 50)
        worksheet.set_column(1, 12, 20)

        row += 1

        for detalle in self.detalle_validacion_ids:
            worksheet.write(row, 0, detalle.cliente.name)
            worksheet.write(row, 1, detalle.factoring_csf, money)
            worksheet.write(row, 2, detalle.libranzas_csf, money)
            worksheet.write(row, 3, detalle.sentencias_csf, money)
            worksheet.write(row, 4, detalle.mutuos_csf, money)
            worksheet.write(row, 5, detalle.rpr_csf, money)
            worksheet.write(row, 6, detalle.libranzas_fcl, money)
            worksheet.write(row, 7, detalle.rpr_fcl, money)
            worksheet.write(row, 8, detalle.sentencias_fcp, money)
            worksheet.write(row, 9, detalle.si_fcp, money)
            worksheet.write(row, 10, detalle.sii_fcp, money)
            worksheet.write(row, 11, detalle.rpr_fcp, money)
            worksheet.write(row, 12, detalle.total, money)

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
        }


class DetalleMovimiento(models.Model):
    _name = 'ctm.validacion.detalle_validacion'

    validacion_id = fields.Many2one('ctm.validacion','Validación')
    cliente = fields.Many2one('res.partner', 'Cliente')
    #CSF
    factoring_csf = fields.Float('FACTORING - CSF')
    libranzas_csf = fields.Float('LIBRANZAS - CSF')
    sentencias_csf = fields.Float('SENTENCIAS - CSF')
    mutuos_csf = fields.Float('MUTUOS - CSF')
    rpr_csf = fields.Float('RPR CSF')
    #FCL
    libranzas_fcl = fields.Float('LIBRANZAS - FCL')
    rpr_fcl = fields.Float('RPR FCL')
    #FCP
    sentencias_fcp = fields.Float('SENTENCIAS - STATUM')
    si_fcp = fields.Float('SI - STATUM')
    sii_fcp = fields.Float('SII - STATUM')
    rpr_fcp = fields.Float('RPR STATUM')

    total = fields.Float('TOTAL')
