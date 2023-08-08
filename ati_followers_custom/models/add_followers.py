from odoo import models, fields, api


class AddFollowers(models.Model):
    _name = 'ati.add_followers'
    _description = "Agregar Seguidores en el módulo de contactos"
    _inherit = []

    name = fields.Char('Nombre')
    user = fields.Many2one('res.partner', 'Usuario')
    status = fields.Selection([('sin_asignar', 'Sin Asignar'), ('asignado', 'Asignado')], default='sin_asignar', string='Estado')

    add_followers_users_ids = fields.One2many('ati.detalle_add_followers',
                                                         'add_followers_id', 'Clientes')

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
