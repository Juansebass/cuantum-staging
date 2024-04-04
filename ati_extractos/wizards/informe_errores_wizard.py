from odoo import models, fields, api
import io
import base64
import xlsxwriter


class InformeErroresWizard(models.TransientModel):
    _name = 'informe.errores.wizard'
    _description = 'Wizard To Informe Errores'
    _inherit = ["mail.thread"]

    fecha_inicio = fields.Date('Fecha de Inicio', required=1)
    fecha_fin = fields.Date('Fecha de Fin', required=1)

    def confirm_informe_errores(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Informe Errores')
        date_default_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'num_format': 'yyyy-mm-dd', 'align': 'right', })

        row = 1
        worksheet.write(row, 0, 'CLIENTE')
        worksheet.write(row, 1, 'VALOR ACTUAL')
        worksheet.write(row, 2, 'VALOR VALIDADO')
        worksheet.write(row, 2, 'VALOR DIFERENCIA')

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        attach_id = self.env['informe.errores.download'].create({
            'name': 'Informe Errores.xlsx',
            'xls_output': base64.encodebytes(generated_file)
        })
        return {
            'context': self.env.context,
            'name': 'Informe Errores',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'informe.errores.download',
            'res_id': attach_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }


class DownloadInformeErrores(models.Model):
    _name = 'informe.errores.download'

    name = fields.Char('File Name')
    xls_output = fields.Binary(string='Download', readonly=True)