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
        movimientos_flujos = self.env['ctm.movimientos_flujos'].search([
            ('fecha_final', '=', self.date),
            ('gestor_id', '=', self.gestor_id.id),
            ('investment_type_id', '=', self.investment_type_id.id),
        ])

        pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf('ctm_control_movimientos.certificado_recaudos_template', movimientos_flujos.ids)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:

            zip_file.writestr('test.pdf', pdf_content)
            zip_file.writestr('example.txt', 'This is an example file content.')
            zip_file.writestr('example2.txt', 'This is the second example file content.')
            zip_file.writestr('example3.txt', 'This is the third example file content.')

        zip_buffer.seek(0)
        zip_file_content = zip_buffer.read()
        self.zip_file = base64.b64encode(zip_file_content)
        self.zip_filename = 'example.zip'

        attachment = self.env['ir.attachment'].create({
            'name': self.zip_filename,
            'type': 'binary',
            'datas': self.zip_file,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/zip'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
