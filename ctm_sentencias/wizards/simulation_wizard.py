from odoo import models, fields, api
from datetime import datetime

class SimulationWizard(models.TransientModel):
    _name = 'simulation.wizard'
    _description = 'Simulation Wizard'

    date = fields.Date(string='Fecha a simular', required=True)

    def action_generate_simulations(self):
        active_ids = self.env.context.get('active_ids')
        if active_ids:
            records = self.env['ctm.liquidaciones'].browse(active_ids)
            for rec in records:
                rec.fecha_liquidar = self.date
                rec.generar_simulacion()

