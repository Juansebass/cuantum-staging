from odoo import models, fields  # type: ignore


class ResPartner(models.Model):
    _inherit = 'res.partner'

    ingresos_mensuales = fields.Float("Ingresos Mensuales")
    gastos_mensuales = fields.Float("Gastos mensuales")
    document_file = fields.Binary("Documento")
    document_filename = fields.Char("Nombre del Documento")
