# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


from odoo.exceptions import ValidationError


class Retencion(models.Model):
    _name = 'ctm.retencion'
    _description = "Retenciones"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    concepto = fields.Char('CONCEPTO DEL PAGO SUJETO A LA RETENCION')
    porcentaje = fields.Char('CONCEPTO DEL PAGO SUJETO A LA RETENCION')
    retenido = fields.Many2one('res.partner', 'RETENIDO A')
    cuantia = fields.Float(' CUANTIA DE LA RETENCION ')
    year = fields.Char('Año')
