# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = "res.partner"

    #Emisor / Pagador
    emisor = fields.Boolean('Emisor',default=False)
    pagador = fields.Boolean('Pagador',default=False)