from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64
import logging



class CreateExtractos(models.Model):
    _name = 'ati.create_extractos'
    _description = "Crear varios extractos a la vez"
    _inherit = []

    responsible = fields.Many2one('res.partner', 'Responsable')
    month = fields.Char('Mes de Periodo', required=1)
    year = fields.Char('Año de Periodo', required=1)
    status = fields.Selection([('sin_crear', 'Sin Crear'), ('creados', 'Creados')], default='sin_crear', string='Estado')

    name = fields.Char('Nombre')
    create_extractos_users_ids = fields.One2many('ati.detalle_create_extractos','create_extractos_id', 'Clientes')
    client_file = fields.Binary('Archivo')
    file_content = fields.Text('Texto archivo')
    delimiter = fields.Char('Delimitador', default=";")
    skip_first_line = fields.Boolean('Saltear primera linea', default=True)

    def crear_extractos(self):
        pass

    def action_cargar_clientes(self):
        pass

    @api.model
    def create(self, var):
        res = super(CreateExtractos, self).create(var)
        res.name = 'Extractos' + res.month + '/' + res.year
        return res




class DetalleCreateExtractos(models.Model):
    _name = 'ati.detalle_create_extractos'

    create_extractos_id = fields.Many2one('ati.create_extractos', 'Create Extractos')
    cliente = fields.Many2one('res.partner', 'Cliente')
    vat = fields.Char('NIT')