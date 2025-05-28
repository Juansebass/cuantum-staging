from odoo import models, fields  # type: ignore


class TirDeseadaWizard(models.TransientModel):
    _name = 'ctm.tir_deseada.wizard'
    _description = 'TIR Deseada Wizard'

    tir_deseada = fields.Float(string='TIR Deseada', required=True)

    def action_set_tir_deseada(self):
        active_ids = self.env.context.get('active_ids')
        if active_ids:
            records = self.env['ctm.sentencias'].browse(active_ids)
            for rec in records:
                rec.generar_tir_deseada(self.tir_deseada)
