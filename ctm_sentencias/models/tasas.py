 # -*- coding: utf-8 -*-

from odoo import models, fields, api

class Tasas(models.Model):
    _name = 'ctm.tasas'
    _description = "Tasas configuración sentencias"
    _inherit = []

    name = fields.Char('Nombre')
    fecha_inicio = fields.Date('Fecha de Inicio', required=True)
    fecha_final = fields.Date('Fecha Final', required=True)
    dtf = fields.Float('DTF',  digits=(10, 6), required=True, help="Por favor poner las tasas efectivas anuales")
    usura = fields.Float('Usura',  digits=(10, 6), required=True, help="Por favor poner las tasas efectivas anuales")

    @api.model
    def create(self, var):
        res = super(Tasas, self).create(var)
        res.name = "Tasa-{}".format(res.fecha_final)
        return res
