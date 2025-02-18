from odoo import models, fields, api  # type: ignore
from odoo.exceptions import ValidationError  # type: ignore
import base64
import io
import xlsxwriter  # type: ignore


class CausacionesPagos(models.Model):
    _name = 'ctm.causaciones_pagos'
    _description = 'Causaciones Pagos'

    name = fields.Char(string='Nombre')
    tipo_busqueda = fields.Selection(
        selection=[('fecha_unica', 'Fecha Única'), ('rango_fechas', 'Rango de Fechas')],
        string='Tipo de Búsqueda',
        default='fecha_unica'
    )
    fecha_unica = fields.Date(string='Fecha Única')
    fecha_inicio = fields.Date(string='Fecha Inicio')
    fecha_final = fields.Date(string='Fecha Final')
    gestor_id = fields.Many2one('ctm.gestor', 'Gestor', required=True)
    investment_type_id = fields.Many2one('ctm.investment_type', 'Tipo de Inversión', required=True)

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
        if res.tipo_busqueda == 'fecha_unica':
            res.name = f'{res.fecha_unica.strftime('%Y-%m-%d')} - {res.gestor_id.name} - {res.investment_type_id.name}'
        else:
            res.name = f'{res.fecha_inicio.strftime('%Y-%m-%d')} - {res.fecha_final.strftime('%Y-%m-%d')} - {res.gestor_id.name} - {res.investment_type_id.name}'
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
        pass


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
    cdg_acumulada = fields.Float('CDG Acumulada')
    rendimiento_acumulado = fields.Float('Rendimiento Acumulado')
    pago_otros_conceptos = fields.Float('Pago Otros Conceptos')
    pago_capital = fields.Float('Pago Capital')
    pago_rendimientos = fields.Float('Pago Rendimientos')
    pago_cdg = fields.Float('Pago CDG')
    total_pagos = fields.Float('Total Pagos')
