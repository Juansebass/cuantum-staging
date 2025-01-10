from odoo import models, fields


class CargarCompras(models.Model):
    _name = 'ctm.cargar_compras'
    _description = 'Cargar Compras'

    name = fields.Char(string='Nombre', required=True)
