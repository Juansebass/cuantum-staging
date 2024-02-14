 # -*- coding: utf-8 -*-

from email.policy import default
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Extracto(models.Model):
    _name = 'ctm.certificado'
    _description = "Certificado"
    _inherit = ['portal.mixin', 'mail.thread','mail.activity.mixin']

    name = fields.Char('Nombre')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    cliente = fields.Many2one('res.partner', 'Cliente', required=1)
    year = fields.Char('Año', required=1)
    type = fields.Selection(selection=[('retencion','Retención'),('comprador','Comprador')],string='Tipo de Certificado',default='comprador')
    state = fields.Selection(
        selection=[('draft', 'Borrador'), ('processed', 'Procesado')],
        string='Estado', default='draft')


    facturas_valor = fields.Float('Facturas Total')
    facturas_rendimiento = fields.Float('Facturas Rendimiento')
    sentencias_valor = fields.Float('Sentencias Total')
    sentencias_rendimiento = fields.Float('Sentencias Rendimiento')
    libranzas_valor = fields.Float('Libranzas Total')
    libranzas_rendimiento = fields.Float('Libranzas Rendimiento')
    mutuos_valor = fields.Float('Mutuos Total')
    mutuos_rendimiento = fields.Float('Mutuos Rendimiento')
    rpr_valor = fields.Float('RPR Total')
    rpr_rendimiento = fields.Float('RPR Rendimiento')

    def generar_certificado(self):
        pass

    @api.model
    def create(self, var):
        res = super(Extracto, self).create(var)
        res.name = 'Certificado/' + res.type + '/' + res.cliente + '/' + res.year
        return res