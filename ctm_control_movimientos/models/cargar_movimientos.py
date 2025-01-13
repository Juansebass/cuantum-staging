from odoo import models, fields
from odoo.exceptions import ValidationError
import base64
from datetime import datetime


class CargarMovimientos(models.Model):
    _name = 'ctm.cargar_movimientos'
    _description = 'Cargar Movimientos'

    name = fields.Char(string='Nombre', required=True)
    fecha = fields.Date(string='Fecha', required=True)
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
    file_content = fields.Text(string='Contenido', required=True)

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
            try:
                line = line.split(self.delimiter)
                cliente = self.env['res.partner'].search([('name', '=', line[0])])
                if not cliente:
                    raise ValidationError(f'Cliente {line[0]} no encontrado')
                fecha = datetime.strptime(line[1], '%d/%m/%Y')
                valor = self._format_money(line[2])
                inversion = self.env['ati.investment.type'].search([('code', '=', line[3])])
                if not inversion:
                    raise ValidationError(f'Inversión {line[3]} no encontrada')
                gestor = self.env['ati.gestor'].search([('code', '=', line[4])])
                if not gestor:
                    raise ValidationError(f'Gestor {line[4]} no encontrado')
                flujo = self._format_percent(line[5])
                cdg = self._format_percent(line[6])
                if self.tipo == 'compra':
                    vals = {
                        'name': line[0],
                        'partner_id': cliente.id,
                        'fecha': fecha,
                        'valor': valor,
                        'investment_type_id': inversion.id,
                        'gestor_id': gestor.id,
                        'flujo': flujo,
                        'cdg': cdg
                    }
                    self.env['ctm.compras'].create(vals)
            except Exception as e:
                raise ValidationError(f'Error en la linea {i + 1}: {e}. Contenido: {line}')

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
