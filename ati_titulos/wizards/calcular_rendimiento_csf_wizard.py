from odoo import models, fields  # type: ignore


class CalcularRendimientoCsfWizard(models.TransientModel):
    _name = 'ctm.calcular_rendimiento_csf.wizard'
    _description = 'Calcular Rendimeinto Wizard'

    date = fields.Date(string='Fecha Rendimiento', required=True)

    def button_calcular_rendimiento_csf_wizard(self):
        active_ids = self.env.context.get('active_ids')
        if active_ids:
            partnes = self.env['res.partner'].browse(active_ids)
            for rec in partnes:
                rec.calcular_rendimiento_csf(date=self.date)
