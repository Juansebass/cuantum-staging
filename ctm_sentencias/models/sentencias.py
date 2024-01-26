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

    name = fields.Char('Nombre', required=1)
    emisor = fields.Many2one('res.partner','Emisor',required=1)
    pagador = fields.Many2one('res.partner','Pagador',required=1)
    codigo = fields.Char('Código', required=1)
    fecha_ejecutoria = fields.Date('Fecha de Ejecutoría', required=1)
    fecha_cuenta_cobro = fields.Date('Fecha de Cuenta de Cobro', required=1)
    fecha_liquidar = fields.Date('Fecha a Liquidar', required=1)
    valor_condena = fields.Float('Valor Condena', required=1)
