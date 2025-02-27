import io
import zipfile
import base64

from odoo import models, fields  # type: ignore
import logging

_logger = logging.getLogger(__name__)


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
        _logger.info(f'movimientos_flujos: {movimientos_flujos}')
        _logger.info(f'movimientos_flujos: {movimientos_flujos.ids}')

        grouped_movimientos = {}
        for movimiento in movimientos_flujos:
            partner_id = movimiento.partner_id.id
            if partner_id not in grouped_movimientos:
                grouped_movimientos[partner_id] = self.env['ctm.movimientos_flujos']
            grouped_movimientos[partner_id] |= movimiento
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for partner_id, movimientos in grouped_movimientos.items():
                partner_name = movimientos[0].partner_id.name
                pdf_content, _ = self.env.ref('ctm_control_movimientos.action_report_certificado_recaudos')._render_qweb_pdf(movimientos.ids)
                zip_file.writestr(f'{partner_name}.pdf', pdf_content)

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
