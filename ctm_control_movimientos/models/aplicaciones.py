from odoo import models, fields


class Aplicaciones(models.Model):
    _name = 'ctm.aplicaciones'
    _description = 'Aplicaciones'

    name = fields.Char(string='Nombre', required=True)
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True)
    fecha = fields.Date(string='Fecha', required=True)
    valor = fields.Float(string='Valor', required=True)
    investment_type_id = fields.Many2one('ati.investment.type', string='Tipo de Inversion', required=True)
    gestor_id = fields.Many2one('ati.gestor', string='Gestor', required=True)
    flujo = fields.Float(string='Flujo', required=True)
    cdg = fields.Float(string='CDG', required=True)
    otros = fields.Float(string='Otros', required=True)
