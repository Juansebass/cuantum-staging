 # -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class Descuentos(models.Model):
    _name = 'descuentos'
    _description = 'Descuentos'

    name = fields.Char(string='Nombre', required=True)
    liquidacion_id = fields.Many2one('liquidaciones', string='Liquidación', required=True)
    descuento_bruto = fields.Float(
        string='Descuento Bruto',
        required=True,
        domain=[('descuento_bruto', '>=', 0)]
    )
    retencion_total = fields.Float(string='Retención Total', required=True)
    estructuracion = fields.Float(string='Estructuración', required=True)
    intermediacion = fields.Float(string='Intermediación', required=True)
