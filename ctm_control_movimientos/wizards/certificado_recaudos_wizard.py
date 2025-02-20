import io
import zipfile
import base64

from odoo import models, fields  # type: ignore


class CertificadoRecaudosWizard(models.TransientModel):
    _name = 'ctm.certificado_recaudos.wizard'
    _description = 'Certificado Recaudos Wizard'

    date = fields.Date(string='Fecha', required=True)
    gestor_id = fields.Many2one('ati.gestor', string='Gestor', required=True)
    investment_type_id = fields.Many2one('ati.investment.type', string='Tipo de Inversion', required=True)
    zip_file = fields.Binary(string='ZIP File', readonly=True)
    zip_filename = fields.Char(string='ZIP Filename')

    def generate_zip(self):
        # Create in-memory zip file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add files to the zip file
            zip_file.writestr('example.txt', 'This is an example file content.')

        zip_buffer.seek(0)
        self.zip_file = base64.b64encode(zip_buffer.read())
        self.zip_filename = 'example.zip'

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.id}/zip_file/{self.zip_filename}',
            'target': 'self',
        }
