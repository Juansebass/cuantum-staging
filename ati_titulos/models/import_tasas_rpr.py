from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime
import base64
import csv
from datetime import date as dt
import logging
import xlsxwriter
import io
_logger = logging.getLogger(__name__)



class ImportTasasRpr(models.Model):
    _name = 'import.tasas.rpr'
    _order = "fch_procesado desc"
    _description = 'Modelo para importacion de tasas RPR'

    def btn_process(self):
        _procesados = ""
        _noprocesados = ""
        vals={}    
        self.ensure_one()
        if not self.client_match:
            raise ValidationError('Debe seleccionar metodo de busqueda de clientes')
        if not self.delimiter:
            raise ValidationError('Debe ingresar el delimitador')
        if not self.client_file:
            raise ValidationError('Debe seleccionar el archivo')
        if self.state != 'draft':
            raise ValidationError('Archivo procesado!')

        self.file_content = base64.decodebytes(self.client_file)
        lines = self.file_content.split('\n')
        for i, line in enumerate(lines):
            if self.skip_first_line and i == 0:
                continue
            lista = line.split(self.delimiter)
            if len(lista) > 6:
                nombre_cliente = lista[0]
                tasa_historica_si = lista[1]
                tasa_historica_sii = lista[2]
                tasa_fcl = lista[3]
                tasa_csf = lista[4]

                vals.clear()

                client = self.env['res.partner'].search(
                    [(self.client_match, '=', nombre_cliente)]
                )
                if len(client) > 1:
                    raise ValidationError(
                        "El CSV no se procesara por estar mal formado en la linea {0}, "
                        "tienes mas de un cliente con el mismo documento, contenido de linea: {1}".format(i, line)
                    )
                if len(client) > 0:
                    client.write({
                        'tasa_historica_si': self._format_percent(tasa_historica_si) if tasa_historica_si != '' else 0,
                        'tasa_historica_sii': self._format_percent(tasa_historica_sii) if tasa_historica_sii != '' else 0,
                        'tasa_fcl': self._format_percent(tasa_fcl) if tasa_fcl != '' else 0,
                        'tasa_csf': self._format_percent(tasa_csf) if tasa_csf != '' else 0,
                    })
                    _procesados += "{0};{1};{2};{3};{4} \n".format(
                        nombre_cliente, tasa_historica_si, tasa_historica_sii, tasa_fcl, tasa_csf
                    )
                else:
                    _noprocesados += "{} \n".format(nombre_cliente)
                    raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, contenido de linea: {1}. El cliente no existe".format(i, line))
            elif len(lista) == 1:
                continue
            else:
                _logger.warning("***** lista: {0}".format(len(lista)))
                raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, contenido de linea: {1}. Se necesitan al menos 6 columnas".format(i, line))
        self.recursos_cargados = _procesados
        self.not_processed_content = _noprocesados
        self.responsable = self.env.user.partner_id
        self.fch_procesado = datetime.today()
        self.state = 'processed'

    def _format_percent(self, percent):
        return float(
            percent.replace('%', '')
            .replace(' ', '')
            .replace('.', '')
            .replace(',', '.')
            .replace('-', '')
        ) / 100

    name = fields.Char('Nombre')
    client_file = fields.Binary('Archivo')
    delimiter = fields.Char('Delimitador', default=";")
    fch_procesado = fields.Datetime('Fecha procesado')
    responsable = fields.Many2one('res.partner', 'Responsable de proceso')
    state = fields.Selection(selection=[('draft', 'Borrador'), ('processed', 'Procesado')], string='Estado', default='draft')
    file_content = fields.Text('Texto archivo')
    not_processed_content = fields.Text('Texto no procesado')
    recursos_cargados = fields.Text('Recursos Cargados')
    skip_first_line = fields.Boolean('Saltar primera linea',default=True)
    client_match = fields.Selection(selection=[('name', 'Nombre')],string='Buscar clientes por...', default='name')
