from odoo import models, fields  # type: ignore


class CerrarMovimientosFlujoWizard(models.TransientModel):
    _name = 'ctm.cerrar_movimientos_flujos.wizard'
    _description = 'Cerrar Movimientos FLujo Wizard'

    date = fields.Date(string='Fecha de Cierre', required=True)

    def button_cerrar_movimientos_flujos_wizard(self):
        active_ids = self.env.context.get('active_ids')
        if active_ids:
            records = self.env['ctm.flujos'].browse(active_ids)
            for rec in records:
                rec.cerrar_movimientos_flujos(self.date)
