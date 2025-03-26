from odoo import models, fields  # type: ignore


class CerrarMovimientosFlujoWizard(models.TransientModel):
    _name = 'ctm.cerrar_movimientos_rpr.wizard'
    _description = 'Cerrar Movimientos RPR Wizard'

    date = fields.Date(string='Fecha de Cierre', required=True)

    def button_cerrar_movimientos_rpr_wizard(self):
        active_ids = self.env.context.get('active_ids')
        if active_ids:
            partnes = self.env['res.partner'].browse(active_ids)
            for rec in partnes:
                rec.cerrar_movimientos_rpr(self.date)
