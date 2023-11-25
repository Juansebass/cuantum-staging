 # -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64
import io
import xlsxwriter
from datetime import datetime

class Sentencias(models.Model):
    _name = 'ctm.sentencias'
    _description = "Sentencias Cuantum"
    _inherit = []

    name = fields.Char('Nombre')

