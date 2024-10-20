from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64
import logging
_logger = logging.getLogger(__name__)



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
        for cliente in self.create_extractos_users_ids:
            exists_extracto= self.env['ati.extracto'].sudo().search([
                ('cliente', '=', cliente.cliente.id),
                ('month', '=', self.month),
                ('year', '=', self.year)
            ])

            if not exists_extracto:
                created_extracto = self.env['ati.extracto'].sudo().create({
                    'cliente': cliente.cliente.id,
                    'month': self.month,
                    'year': self.year,

                })
                try:
                    created_extracto.generar_extracto()
                except Exception as e:
                    raise ValidationError('Error al crear extracto: {0}. cliente {1}'.format(e, cliente.cliente.name))

        self.status = 'creados'





    def action_cargar_clientes(self):
        self.ensure_one()
        if not self.delimiter:
            raise ValidationError('Debe ingresar el delimitador')
        if not self.client_file:
            raise ValidationError('Debe seleccionar el archivo')

        self.file_content = base64.decodebytes(self.client_file)
        lines = self.file_content.split('\r')

        for detalle  in self.create_extractos_users_ids:
            detalle.unlink()

        for i,line in enumerate(lines):
            if self.skip_first_line and i == 0:
                continue
            lista = line.split(self.delimiter)
            vat = lista[0].split('\n')[1]

            clients = self.env['res.partner'].sudo().search(
                [('vat', '=', str(vat))])

            # Agregando clientes al detalle de seguidores
            for y in clients:
                self.env['ati.detalle_create_extractos'].create({
                    'create_extractos_id': self.id,
                    'cliente': y.id,
                    'vat': y.vat,
                })


    @api.model
    def create(self, var):
        res = super(CreateExtractos, self).create(var)
        res.name = 'Extractos ' + res.month + '/' + res.year
        return res


class DetalleCreateExtractos(models.Model):
    _name = 'ati.detalle_create_extractos'

    create_extractos_id = fields.Many2one('ati.create_extractos', 'Create Extractos')
    cliente = fields.Many2one('res.partner', 'Cliente')
    vat = fields.Char('NIT')