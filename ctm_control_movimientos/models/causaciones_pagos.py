from odoo import models, fields, api  # type: ignore
from odoo.exceptions import ValidationError  # type: ignore
import base64
import io
import xlsxwriter  # type: ignore


class CausacionesPagos(models.Model):
    _name = 'ctm.causaciones_pagos'
    _description = 'Causaciones Pagos'

    name = fields.Char(string='Nombre')
    fecha_unica = fields.Date(string='Fecha Única', required=True)
    gestor_id = fields.Many2one('ati.gestor', 'Gestor', required=True)
    investment_type_id = fields.Many2one('ati.investment.type', 'Tipo de Inversión', required=True)

    client_file = fields.Binary('Archivo')
    file_content = fields.Text('Texto archivo')
    delimiter = fields.Char('Delimitador', default=";")
    responsable = fields.Many2one('res.partner', 'Responsable de proceso')
    state = fields.Selection(
        selection=[('draft', 'Borrador'), ('processed', 'Procesado')],
        string='Estado',
        default='draft'
    )
    skip_first_line = fields.Boolean('Saltar primera linea', default=True)
    cliente_ids = fields.One2many('ctm.causaciones_pagos_clientes', 'causaciones_pagos_id', 'Clientes')
    informe_cliente_ids = fields.One2many('ctm.causaciones_pagos_informe', 'causaciones_pagos_id', 'Informe Causaciones y Pagos')
    xls_output = fields.Binary(
        string='Descargar',
        readonly=True,
    )

    @api.model
    def create(self, var):
        res = super(CausacionesPagos, self).create(var)
        res.name = f'{res.fecha_unica.strftime("%Y-%m-%d")} - {res.gestor_id.name} - {res.investment_type_id.name}'
        return res

    def action_cargar_clientes(self):
        self.ensure_one()
        if not self.delimiter:
            raise ValidationError('Debe ingresar el delimitador')
        if not self.client_file:
            raise ValidationError('Debe seleccionar el archivo')

        self.file_content = base64.decodebytes(self.client_file)
        content = self.file_content.replace('\n', '')
        lines = content.split('\r')

        for cliente in self.cliente_ids:
            cliente.unlink()

        for i, line in enumerate(lines):
            if self.skip_first_line and i == 0:
                continue
            lista = line.split(self.delimiter)
            partner_name = lista[0]
            partner = self.env['res.partner'].search([('name', '=', partner_name)], limit=1)
            if not partner:
                raise ValidationError('No se encontró el cliente {0}'.format(partner_name))
            self.env['ctm.causaciones_pagos_clientes'].create({
                'causaciones_pagos_id': self.id,
                'partner_id': partner.id
            })

    def crear_causaciones_pagos(self):
        self.ensure_one()
        self.informe_cliente_ids.unlink()

        for cliente in self.cliente_ids:
            informe_cliente = self.env['ctm.causaciones_pagos_informe'].create({
                'causaciones_pagos_id': self.id,
                'partner_id': cliente.partner_id.id,
            })
            movimientos_flujos = self.env['ctm.movimientos_flujos'].search([
                ('partner_id', '=', cliente.partner_id.id),
                ('gestor_id', '=', self.gestor_id.id),
                ('investment_type_id', '=', self.investment_type_id.id),
                ('fecha_final', '=', self.fecha_unica),
            ])
            informe_cliente.compras = sum(movimientos_flujos.mapped('compra'))
            informe_cliente.cdg_acumulada = sum(movimientos_flujos.mapped('cdg_acumulado'))
            informe_cliente.rendimiento_acumulado = sum(movimientos_flujos.mapped('rendimiento_acumulado'))
            informe_cliente.pago_otros_conceptos = sum(movimientos_flujos.mapped('pago_otros_conceptos'))
            informe_cliente.pago_capital = sum(movimientos_flujos.mapped('pago_capital'))
            informe_cliente.pago_rendimientos = sum(movimientos_flujos.mapped('pago_rendimientos'))
            informe_cliente.pago_cdg = sum(movimientos_flujos.mapped('pago_cdg'))
            informe_cliente.total_pagos = informe_cliente.pago_otros_conceptos + informe_cliente.pago_capital + informe_cliente.pago_rendimientos + informe_cliente.pago_cdg
        self.state = 'processed'

    def action_draft(self):
        self.state = 'draft'

    def action_exportar_xls(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Causaciones y Pagos')
        money = workbook.add_format({'num_format': '$#,##0'})
        row = 0

        worksheet.write(row, 0, 'Cliente')
        worksheet.write(row, 1, 'Compras')
        worksheet.write(row, 2, 'CDG Acumulada')
        worksheet.write(row, 3, 'Rendimiento Acumulado')
        worksheet.write(row, 4, 'Pago Otros Conceptos')
        worksheet.write(row, 5, 'Pago Capital')
        worksheet.write(row, 6, 'Pago Rendimientos')
        worksheet.write(row, 7, 'Pago CDG')
        worksheet.write(row, 8, 'Total Pagos')
        row += 1

        for informe in self.informe_cliente_ids:
            worksheet.write(row, 0, informe.partner_id.name)
            worksheet.write(row, 1, informe.compras, money)
            worksheet.write(row, 2, informe.cdg_acumulado, money)
            worksheet.write(row, 3, informe.rendimiento_acumulado, money)
            worksheet.write(row, 4, informe.pago_otros_conceptos, money)
            worksheet.write(row, 5, informe.pago_capital, money)
            worksheet.write(row, 6, informe.pago_rendimientos, money)
            worksheet.write(row, 7, informe.pago_cdg, money)
            worksheet.write(row, 8, informe.total_pagos, money)
            row += 1

        workbook.close()
        output.seek(0)
        self.xls_output = base64.b64encode(output.read())
        output.close()

        return {
            'context': self.env.context,
            'name': 'Causaciones y Pagos',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ctm.causaciones_pagos',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
        }


class CausacionesPagosClientes(models.Model):
    _name = 'ctm.causaciones_pagos_clientes'
    _description = 'Causaciones Pagos Clientes'

    causaciones_pagos_id = fields.Many2one('ctm.causaciones_pagos', 'Causaciones y Pagos')
    partner_id = fields.Many2one('res.partner', 'Cliente')


class CausacionesPagosInforme(models.Model):
    _name = 'ctm.causaciones_pagos_informe'
    _description = 'Causaciones Pagos Informe'

    causaciones_pagos_id = fields.Many2one('ctm.causaciones_pagos', 'Causaciones y Pagos')
    partner_id = fields.Many2one('res.partner', 'Cliente')
    compras = fields.Float('Compras')
    cdg_acumulada = fields.Float('CDG Acumulada')
    rendimiento_acumulado = fields.Float('Rendimiento Acumulado')
    pago_otros_conceptos = fields.Float('Pago Otros Conceptos')
    pago_capital = fields.Float('Pago Capital')
    pago_rendimientos = fields.Float('Pago Rendimientos')
    pago_cdg = fields.Float('Pago CDG')
    total_pagos = fields.Float('Total Pagos')
