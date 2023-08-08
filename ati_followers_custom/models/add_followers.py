from odoo import models, fields, api


class InformeAdministracion(models.Model):
    _name = 'ati.add_followers'
    _description = "Agregar Seguidores en el módulo de contactos"
    _inherit = []

    name = fields.Char('Nombre')

