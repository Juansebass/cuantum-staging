from odoo import models, fields


class Flujos(models.Model):
    _name = 'ctm.flujos'
    _description = 'Flujos'

    name = fields.Char(string='Nombre', required=True)
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True)
    flujo = fields.Float(string='Flujo', required=True)
    cdg = fields.Float(string='CDG', required=True)
    aplicacion_id = fields.Many2one('ctm.aplicaciones', string='Aplicación')
    compra_id = fields.Many2one('ctm.compras', string='Compra')
