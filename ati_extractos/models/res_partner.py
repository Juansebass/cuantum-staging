 # -*- coding: utf-8 -*-
from odoo import fields, models, api

class ResPartner(models.Model):
    """
    Añadir un campo para almacenar la TIR histórica de la FCP
    """
    _inherit = "res.partner"

    fcp_historic_tir = fields.Float(string='TIR Histórica FCP')
