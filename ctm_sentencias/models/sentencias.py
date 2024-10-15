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
    statum = fields.Selection(
        string='Statum',
        selection=[
            ('CSF', 'CSF'),
            ('Statum Compartimento 1', 'Statum Compartimento 1'),
            ('Statum Compartimento 2', 'Statum Compartimento 2'),
            ('Statum Compartimento 3', 'Statum Compartimento 3'),
            ('Statum Compartimento 4', 'Statum Compartimento 4'),
            ('Statum Compartimento 5', 'Statum Compartimento 5'),
            ('Statum Compartimento 6', 'Statum Compartimento 6'),
            ('Statum Compartimento 7', 'Statum Compartimento 7'),
            ('Statum Compartimento 8', 'Statum Compartimento 8'),
            ('Statum Compartimento 9', 'Statum Compartimento 9'),
        ],
        default='CSF',
        required=True
    )
    fecha_ejecutoria = fields.Date('Fecha de Ejecutoría', required=1)
    fecha_cuenta_cobro = fields.Date('Fecha de Cuenta de Cobro', required=1)
    fecha_liquidar = fields.Date('Fecha a Liquidar', required=1)
    valor_condena = fields.Float('Valor Condena', required=1)
    nit_fcp_statum = fields.Char('NIT FCP STATUM (Comp 1)', required=1)
    vendedor  = fields.Char('Vendedor')
    nemotecnico = fields.Char('Nemotecnico')
    fecha_vencimiento = fields.Date('Fecha de Vencimiento')
    fecha_compra = fields.Date('Fecha de Compra')
    valor_giro = fields.Float('Valor Giro')
    comision = fields.Float('Comisión')
    valor_contable_ayer = fields.Float('Valor Contable Ayer')
    precio = fields.Float('Precio', required=1)
    costas = fields.Float('Costas')
