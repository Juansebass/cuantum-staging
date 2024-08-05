 # -*- coding: utf-8 -*-
from odoo import fields, models, api

class ResPartnerTir(models.Model):
    """
    Añadir un campo para almacenar la TIR histórica de la FCP
    """
    _inherit = "res.partner"

    fcp_historic_tir_si = fields.Float(string='Statum I')
    fcp_historic_tir_sii = fields.Float(string='Statum II')
