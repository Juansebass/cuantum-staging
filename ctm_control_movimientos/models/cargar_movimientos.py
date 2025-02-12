from odoo import models, fields  # type: ignore
from odoo.exceptions import ValidationError  # type: ignore
import base64
from datetime import datetime


class CargarMovimientos(models.Model):
    _name = 'ctm.cargar_movimientos'
    _description = 'Cargar Movimientos'

    name = fields.Char(string='Nombre', required=True)
    responsable_id = fields.Many2one('res.partner', string='Responsable')
    tipo = fields.Selection([
        ('compra', 'Compra'),
        ('aplicación', 'Aplicación')
    ], string='Tipo', required=True)
    client_file = fields.Binary(string='Archivo', required=True)
    delimiter = fields.Selection([
        (';', ';'),
        (',', ',')
    ], string='Delimitador', required=True, default=';')
    skip_first_line = fields.Boolean('Saltar primera linea', default=True)
    state = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('cargado', 'Cargado')
    ], string='Estado', required=True, default='pendiente')
    file_content = fields.Text(string='Contenido')

    def cargar_movimientos(self):
        self.ensure_one()
        if not self.delimiter:
            raise ValidationError('Debe ingresar el delimitador')
        if not self.client_file:
            raise ValidationError('Debe seleccionar el archivo')

        self.file_content = base64.decodebytes(self.client_file)
        lines = self.file_content.replace('\n', '')
        lines = lines.split('\r')

        self.responsable_id = self.env.user.partner_id.id

        if self.skip_first_line:
            lines = lines[1:]

        for i, line in enumerate(lines):
            # try:
            line = line.split(self.delimiter)
            fecha = datetime.strptime(line[1], '%d/%m/%Y')
            cliente = self.env['res.partner'].search([('vat', '=', line[2])])
            if not cliente:
                raise ValidationError(f'Cliente {line[2]} no encontrado')
            valor = self._format_money(line[3])
            inversion = self.env['ati.investment.type'].search([('code', '=', line[4])])
            if not inversion:
                raise ValidationError(f'Inversión {line[4]} no encontrada')
            gestor = self.env['ati.gestor'].search([('code', '=', line[5])])
            if not gestor:
                raise ValidationError(f'Gestor {line[5]} no encontrado')
            flujo = self._format_percent(line[6])
            cdg = self._format_percent(line[7])
            if self.tipo == 'compra':
                vals = {
                    'name': line[0],
                    'fecha': fecha,
                    'partner_id': cliente.id,
                    'fecha': fecha,
                    'valor': valor,
                    'investment_type_id': inversion.id,
                    'gestor_id': gestor.id,
                    'flujo': flujo,
                    'cdg': cdg
                }
                compra_id = self.env['ctm.compras'].create(vals)
                compra_id.procesar_movimiento()
            if self.tipo == 'aplicación':
                otros = self._format_money(line[8])
                vals = {
                    'name': line[0],
                    'partner_id': cliente.id,
                    'fecha': fecha,
                    'valor': valor,
                    'investment_type_id': inversion.id,
                    'gestor_id': gestor.id,
                    'flujo': flujo,
                    'cdg': cdg,
                    'otros': otros
                }
                aplicacion_id = self.env['ctm.aplicaciones'].create(vals)
                aplicacion_id.procesar_movimiento()
            # except Exception as e:
            #     raise ValidationError(f'Error en la linea {i + 1}: {e}. Contenido: {line}')

    def _format_money(self, money):
        return (
            money.replace('$', '')
            .replace(' ', '')
            .replace('.', '')
            .replace(',', '.')
            .replace('-', '')
        )

    def _format_percent(self, percent):
        return float(
            percent.replace('%', '')
            .replace(' ', '')
            .replace('.', '')
            .replace(',', '.')
            .replace('-', '')
        ) / 100
