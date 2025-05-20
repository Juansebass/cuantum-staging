#  -*- coding: utf-8 -*-
from odoo import models, fields  # type: ignore


class CodigoLiquidacion(models.Model):
    _name = 'ctm.codigo.liquidacion'
    _description = 'Código Liquidación'

    name = fields.Char('Código', required=True)
