from odoo import models, fields, api  # type: ignore
from odoo.exceptions import ValidationError  # type: ignore
import base64
import io
import xlsxwriter  # type: ignore


class ValorPortafolio(models.Model):
    _name = 'ctm.valor_portafolio'
    _description = 'Valor Portafolio'

    name = fields.Char(string='Nombre')
    fecha_corte = fields.Date(string='Fecha de Corte', required=True)
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
    cliente_ids = fields.One2many('ctm.valor_portafolio_clientes', 'valor_portafolio_id', 'Clientes')
    informe_cliente_ids = fields.One2many('ctm.valor_portafolio_informe_clientes', 'valor_portafolio_id', 'Informe Clientes')
    xls_output = fields.Binary(
        string='Descargar',
        readonly=True,
    )

    @api.model
    def create(self, var):
        res = super(ValorPortafolio, self).create(var)
        res.name = 'Valor Portafolio ' + res.fecha_corte.strftime('%Y-%m-%d')
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
            self.env['ctm.valor_portafolio_clientes'].create({
                'valor_portafolio_id': self.id,
                'partner_id': partner.id
            })

    def crear_valor_portafolio(self):
        self.ensure_one()
        self.informe_cliente_ids.unlink()
        for cliente in self.cliente_ids:
            informe_cliente = self.env['ctm.valor_portafolio_informe_clientes'].create({
                'valor_portafolio_id': self.id,
                'partner_id': cliente.partner_id.id,
                'freelance_id': cliente.partner_id.freelance.id
            })
            movimientos_flujos = self.env['ctm.movimientos_flujos'].search([
                ('partner_id', '=', cliente.partner_id.id),
                ('fecha_final', '=', self.fecha_corte),
            ])
            csf = movimientos_flujos.filtered(lambda x: x.gestor_id.code == 'CUANTUM')
            fcl = movimientos_flujos.filtered(lambda x: x.gestor_id.code == 'FCL')
            fcp = movimientos_flujos.filtered(lambda x: x.gestor_id.code == 'FCP')
            rpr_csf = cliente.partner_id.recursos_recompra_csf_ids.filtered(lambda x: x.date <= self.fecha_corte)
            rpr_csf_total = 0
            for recurso in rpr_csf:
                if recurso.movement_type.name in ['Adición', 'Aplicación de recaudo', 'Rendimiento']:
                    rpr_csf_total += recurso.value
                else:
                    rpr_csf_total -= recurso.value
            rpr_fcl = cliente.partner_id.recursos_recompra_fcl_ids.filtered(lambda x: x.date <= self.fecha_corte)
            rpr_fcl_total = 0
            for recurso in rpr_fcl:
                if recurso.movement_type.name in ['Adición', 'Aplicación de recaudo', 'Rendimiento']:
                    rpr_fcl_total += recurso.value
                else:
                    rpr_fcl_total -= recurso.value
            rpr_fcp = cliente.partner_id.recursos_recompra_fcp_ids.filtered(lambda x: x.date <= self.fecha_corte)
            rpr_fcp_total = 0
            for recurso in rpr_fcp:
                if recurso.movement_type.name in ['Adición', 'Aplicación de recaudo', 'Rendimiento']:
                    rpr_fcp_total += recurso.value
                else:
                    rpr_fcp_total -= recurso.value

            informe_cliente.factoring_csf = sum(csf.filtered(lambda x: x.investment_type_id.code == 'FAC').mapped('valor_activo'))
            informe_cliente.libranzas_csf = sum(csf.filtered(lambda x: x.investment_type_id.code == 'LIB').mapped('valor_activo'))
            informe_cliente.sentencias_csf = sum(csf.filtered(lambda x: x.investment_type_id.code == 'SEN').mapped('valor_activo'))
            informe_cliente.mutuo_csf = sum(csf.filtered(lambda x: x.investment_type_id.code == 'MUT').mapped('valor_activo'))
            informe_cliente.rpr_csf = rpr_csf_total
            informe_cliente.libranzas_fcl = sum(fcl.filtered(lambda x: x.investment_type_id.code == 'LIB').mapped('valor_activo'))
            informe_cliente.rpr_fcl = rpr_fcl_total
            informe_cliente.s1_fcp = sum(fcp.filtered(lambda x: x.investment_type_id.code == 'S1').mapped('valor_activo'))
            informe_cliente.s2_fcp = sum(fcp.filtered(lambda x: x.investment_type_id.code == 'S2').mapped('valor_activo'))
            informe_cliente.rpr_fcp = rpr_fcp_total
            informe_cliente.total = informe_cliente.factoring_csf + informe_cliente.libranzas_csf + informe_cliente.sentencias_csf + informe_cliente.mutuo_csf + informe_cliente.rpr_csf + informe_cliente.libranzas_fcl + informe_cliente.rpr_fcl + informe_cliente.s1_fcp + informe_cliente.s2_fcp + informe_cliente.rpr_fcp

            sales = self.env['sale.order'].search([
                ('partner_id', '=', cliente.partner_id.id),
                ('state', 'in', ['sale']),
            ])

            informe_cliente.csf_factoring = sum(sales.filtered(lambda x: x.tipo_producto_ofertar.code == 'FAC' and x.gestor_ofertar.code == 'CUANTUM').mapped('amount_total'))
            informe_cliente.csf_sentencias = sum(sales.filtered(lambda x: x.tipo_producto_ofertar.code == 'SEN' and x.gestor_ofertar.code == 'CUANTUM').mapped('amount_total'))
            informe_cliente.fcl_libranzas = sum(sales.filtered(lambda x: x.tipo_producto_ofertar.code == 'LIB' and x.gestor_ofertar.code == 'FCL').mapped('amount_total'))
        self.state = 'processed'

    def action_exportar_xls(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Valor Portafolio')
        money = workbook.add_format({'num_format': '$#,##0'})
        row = 0

        worksheet.write(row, 0, 'Cliente')
        worksheet.write(row, 1, 'Freelance')
        worksheet.write(row, 2, 'Factoring CSF')
        worksheet.write(row, 3, 'Libranzas CSF')
        worksheet.write(row, 4, 'Sentencias CSF')
        worksheet.write(row, 5, 'Mutuo CSF')
        worksheet.write(row, 6, 'RPR CSF')
        worksheet.write(row, 7, 'Libranzas FCL')
        worksheet.write(row, 8, 'RPR FCL')
        worksheet.write(row, 9, 'S1 FCP')
        worksheet.write(row, 10, 'S2 FCP')
        worksheet.write(row, 11, 'RPR FCP')
        worksheet.write(row, 12, 'Total')
        worksheet.write(row, 13, 'CSF Factoring')
        worksheet.write(row, 14, 'CSF Sentencias')
        worksheet.write(row, 15, 'FCL Libranzas')

        row += 1

        for informe_cliente in self.informe_cliente_ids:
            worksheet.write(row, 0, informe_cliente.partner_id.name)
            worksheet.write(row, 1, informe_cliente.freelance_id.name)
            worksheet.write(row, 2, informe_cliente.factoring_csf, money)
            worksheet.write(row, 3, informe_cliente.libranzas_csf, money)
            worksheet.write(row, 4, informe_cliente.sentencias_csf, money)
            worksheet.write(row, 5, informe_cliente.mutuo_csf, money)
            worksheet.write(row, 6, informe_cliente.rpr_csf, money)
            worksheet.write(row, 7, informe_cliente.libranzas_fcl, money)
            worksheet.write(row, 8, informe_cliente.rpr_fcl, money)
            worksheet.write(row, 9, informe_cliente.s1_fcp, money)
            worksheet.write(row, 10, informe_cliente.s2_fcp, money)
            worksheet.write(row, 11, informe_cliente.rpr_fcp, money)
            worksheet.write(row, 12, informe_cliente.total, money)
            worksheet.write(row, 13, informe_cliente.factoring_csf + informe_cliente.sentencias_csf, money)
            worksheet.write(row, 14, informe_cliente.libranzas_fcl, money)
            worksheet.write(row, 15, informe_cliente.libranzas_fcl, money)
            row += 1

        workbook.close()
        output.seek(0)
        self.xls_output = base64.b64encode(output.read())
        output.close()

        return {
            'context': self.env.context,
            'name': 'Valor Protafolio',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ctm.valor_portafolio',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
        }


class ValorPortafolioClientes(models.Model):
    _name = 'ctm.valor_portafolio_clientes'
    _description = 'Clientes del Valor Portafolio'

    valor_portafolio_id = fields.Many2one('ctm.valor_portafolio', 'Valor Portafolio')
    partner_id = fields.Many2one('res.partner', 'Cliente')


class ValorPortafolioInformeClientes(models.Model):
    _name = 'ctm.valor_portafolio_informe_clientes'
    _description = 'Informe de Clientes del Valor Portafolio'

    valor_portafolio_id = fields.Many2one('ctm.valor_portafolio', 'Valor Portafolio')
    partner_id = fields.Many2one('res.partner', 'Cliente')
    freelance_id = fields.Many2one('res.partner', 'Freelance')
    factoring_csf = fields.Float('Factoring CSF')
    libranzas_csf = fields.Float('Libranzas CSF')
    sentencias_csf = fields.Float('Sentencias CSF')
    mutuo_csf = fields.Float('Mutuo CSF')
    rpr_csf = fields.Float('RPR CSF')
    libranzas_fcl = fields.Float('Libranzas FCL')
    rpr_fcl = fields.Float('RPR FCP')
    s1_fcp = fields.Float('S1 FCP')
    s2_fcp = fields.Float('S2 FCP')
    rpr_fcp = fields.Float('RPR FCP')
    total = fields.Float('Total')
    csf_factoring = fields.Float('CSF Factoring')
    csf_sentencias = fields.Float('CSF Sentencias')
    fcl_libranzas = fields.Float('FCL Libranzas')
