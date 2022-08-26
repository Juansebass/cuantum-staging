# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64
import csv
from datetime import date as dt
import logging
_logger = logging.getLogger(__name__)



class ImportSentencias(models.Model):
    _name = 'import.sentencias'
    _description = 'import.sentencias'

    def btn_process(self):
        return

    name = fields.Char('Nombre')
    client_file = fields.Binary('Archivo')
    delimiter = fields.Char('Delimitador',default=";")
    state = fields.Selection(selection=[('draft','Borrador'),('processed','Procesado')],string='Estado',default='draft')
    file_content = fields.Text('Texto archivo')
    not_processed_content = fields.Text('Texto no procesado')
    clientes_creados = fields.Text('Productos Creados')
    skip_first_line = fields.Boolean('Saltear primera linea',default=True)
    client_match = fields.Selection(selection=[('vat','Vat')],string='Buscar clientes por...',default='vat')