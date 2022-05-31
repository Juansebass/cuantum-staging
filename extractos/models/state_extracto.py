 # -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

logger = logging.getLogger(__name__)

class StateExtracto(models.Model):
    _name = 'ati.state.extracto'

    name = fields.Char('Nombre')