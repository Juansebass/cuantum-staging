 # -*- coding: utf-8 -*-

from email.policy import default
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging


logger = logging.getLogger(__name__)

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
        #Extractos año
        extractos = self.env['ati.extracto'].search([
            ('cliente', '=', self.cliente.id),
            ('year', '=', self.year),
        ])
        #último extracto del año
        extracto_id = self.env['ati.extracto'].search([
            ('cliente', '=', self.cliente.id),
            ('year', '=', self.year),
            ('month', '=', 12),
        ], limit=1)

        #Para obtener valores
        products = extracto_id.resumen_inversion_ids.filtered(
            lambda x: x.gestor.code == 'CUANTUM' or x.name == 'RPR CSF'
        )
        for product in products:
            if product.producto.code == 'FAC':
                self.facturas_valor = product.valor_actual
            elif product.producto.code == 'SEN':
                self.sentencias_valor = product.valor_actual
            elif product.producto.code == 'LIB':
                self.libranzas_valor = product.valor_actual
            elif product.producto.code == 'MUT':
                self.mutuos_valor = product.valor_actual
            elif product.name == 'RPR CSF':
                self.rpr_valor = product.valor_actual

        #Para calcular rendimientos
        facturas_rendimiento = 0
        sentencias_rendimiento = 0
        libranzas_rendimiento = 0
        mutuos_rendimiento = 0
        rpr_rendimiento = 0
        for extracto in extractos:
            products = extracto.resumen_inversion_ids.filtered(
                lambda x: x.gestor.code == 'CUANTUM' or x.name == 'RPR CSF'
            )
            for product in products:
                if product.producto.code == 'FAC':
                    facturas_rendimiento += product.rendimiento_causado
                elif product.producto.code == 'SEN':
                    sentencias_rendimiento += product.rendimiento_causado
                elif product.producto.code == 'LIB':
                    libranzas_rendimiento += product.rendimiento_causado
                elif product.producto.code == 'MUT':
                    mutuos_rendimiento += product.rendimiento_causado
                elif product.name == 'RPR CSF':
                    rpr_rendimiento += product.rendimiento_causado

        self.facturas_rendimiento = facturas_rendimiento
        self.sentencias_rendimiento = sentencias_rendimiento
        self.libranzas_rendimiento = libranzas_rendimiento
        self.mutuos_rendimiento = mutuos_rendimiento
        self.rpr_rendimiento = rpr_rendimiento


    @api.model
    def create(self, var):
        res = super(Extracto, self).create(var)
        res.name = 'Certificado/' + res.type + '/' + res.cliente.name + '/' + res.year
        return res
