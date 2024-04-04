from odoo import models, fields, api

class InformeErroresWizard(models.TransientModel):
    _name = 'informe.errores.wizard'
    _description = 'Wizard To Informe Errores'
    _inherit = ["mail.thread"]

    def confirm_informe_errores(self):
        pass