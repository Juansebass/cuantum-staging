from odoo import models, fields


class CargarMovimientos(models.Model):
    _name = 'ctm.cargar_movimientos'
    _description = 'Cargar Movimientos'

    name = fields.Char(string='Nombre', required=True)
    fecha = fields.Date(string='Fecha', required=True)
    responsable_id = fields.Many2one('res.partner', string='Responsable', required=True)
    tipo = fields.Selection([
        ('compra', 'Compra'),
        ('aplicación', 'Aplicación')
    ], string='Tipo', required=True)
    client_file = fields.Binary(string='Archivo', required=True)
    delimiter = fields.Selection([
        (';', ';'),
        (',', ',')
    ], string='Delimitador', required=True)
    skip_first_line = fields.Boolean('Saltar primera linea', default=True)
    state = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('cargado', 'Cargado')
    ], string='Estado', required=True)
    file_content = fields.Text(string='Contenido', required=True)

    def cargar_movimientos(self):
        pass
