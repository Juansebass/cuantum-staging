 # -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

logger = logging.getLogger(__name__)

class InvestmentType(models.Model):
    _name = 'ati.investment.type'

    name = fields.Char('Nombre')