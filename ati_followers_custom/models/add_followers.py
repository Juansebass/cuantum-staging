from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64
import logging
_logger = logging.getLogger(__name__)


class AddFollowers(models.Model):
    _name = 'ati.add_followers'
    _description = "Agregar Seguidores en el módulo de contactos"
    _inherit = []

    name = fields.Char('Nombre')
    user = fields.Many2one('res.partner', 'Usuario')
    status = fields.Selection([('sin_asignar', 'Sin Asignar'), ('asignado', 'Asignado')], default='sin_asignar', string='Estado')

    add_followers_users_ids = fields.One2many('ati.detalle_add_followers',
                                                         'add_followers_id', 'Clientes')

    client_file = fields.Binary('Archivo')
    file_content = fields.Text('Texto archivo')
    delimiter = fields.Char('Delimitador', default=";")
    skip_first_line = fields.Boolean('Saltear primera linea', default=True)

    def action_cargar_clientes(self):
        self.ensure_one()
        if not self.delimiter:
            raise ValidationError('Debe ingresar el delimitador')
        if not self.client_file:
            raise ValidationError('Debe seleccionar el archivo')

        self.file_content = base64.decodebytes(self.client_file)
        lines = self.file_content.split('\n')
        _logger.error(self.lines)

        for detalle  in self.add_followers_users_ids:
            detalle.unlink()

        for i,line in enumerate(lines):
            if self.skip_first_line and i == 0:
                continue
            temp_cliente = line
            _logger.error(temp_cliente)
            clients = self.env['res.partner'].search(
                [('name', '=', temp_cliente)])
            #Agregando clientes al detalle de seguidores
            for y in clients:
                self.env['ati.detalle_add_followers'].create({
                    'add_followers_id': self.id,
                    'cliente': y.id,
                })


    def asignar(self):
        for cliente in self.add_followers_users_ids:
            exists_relation = self.env['mail.followers'].sudo().search([
                ('partner_id', '=', self.user.id),
                ('res_model', '=', 'res.partner'),
                ('res_id', '=', cliente.cliente.id)
            ])

            if not exists_relation:
                add_user_as_follower = self.env['mail.followers'].sudo().create({
                    'partner_id': self.user.id,
                    'res_model': 'res.partner',
                    'res_id': cliente.cliente.id,
                    'subtype_ids': [1, 2, 3]
                })
        self.status = 'asignado'

    @api.model
    def create(self, var):
        res = super(AddFollowers, self).create(var)
        res.name = 'Agregar como seguidor a ' + res.user.name
        return res


class DetalleAddFollowers(models.Model):
    _name = 'ati.detalle_add_followers'

    add_followers_id = fields.Many2one('ati.add_followers', 'Add Followers')
    cliente = fields.Many2one('res.partner', 'Cliente')
