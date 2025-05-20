#  -*- coding: utf-8 -*-
from odoo import models, fields  # type: ignore


class Pagador(models.Model):
    _name = 'ctm.pagador'
    _description = 'Pagadores Sentencias'

    name = fields.Many2one('res.partner', 'Pagador', required=1)
    plazo = fields.Integer('Plazo (Meses)', required=1)
