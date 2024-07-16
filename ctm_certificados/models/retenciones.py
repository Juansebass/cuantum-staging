# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Retencion(models.Model):
    _name = 'ctm.retencion'
    _description = "Retenciones"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    concepto = fields.Char('CONCEPTO DEL PAGO SUJETO A LA RETENCION')
    porcentaje = fields.Char('PORCENTAJE APLICADO')
    retenido = fields.Many2one('res.partner', 'RETENIDO A')
    cuantia = fields.Float(' CUANTIA DE LA RETENCION ')
    year = fields.Char('AÑO')

    # @api.constrains('retenido', 'year')
    # def _check_unique_record(self):
    #     for record in self:
    #         duplicate_records = self.search([('retenido', '=', record.retenido.id), ('year', '=', record.year)])
    #         if duplicate_records:
    #             raise ValidationError('El registro {0}-{1} ya existe'.format(record.retenido.name, record.year))
