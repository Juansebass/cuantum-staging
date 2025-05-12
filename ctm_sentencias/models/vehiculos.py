#  -*- coding: utf-8 -*-
from odoo import models, fields  # type: ignore


class Vehiculo(models.Model):
    _name = 'ctm.vehiculos'
    _description = 'Vehículos Sentencias'

    name = fields.Char('Nombre', required=True)
    code = fields.Float('Código', required=True)
