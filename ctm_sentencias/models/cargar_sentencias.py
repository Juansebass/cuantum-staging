from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64
from datetime import datetime




class CargarSentencias(models.Model):
    _name = 'ctm.cargar_sentencias'
    _description = "Cargar Sentencias"
    _inherit = []

    name = fields.Char('Nombre')
    client_file = fields.Binary('Archivo')
    delimiter = fields.Char('Delimitador', default=";")
    fch_procesado = fields.Datetime('Fecha procesado')
    responsable = fields.Many2one('res.partner', 'Responsable de proceso')
    state = fields.Selection(selection=[('draft', 'Borrador'), ('processed', 'Procesado')], string='Estado',
                             default='draft')
    file_content = fields.Text('Texto archivo')
    not_processed_content = fields.Text('Texto no procesado')
    clientes_creados = fields.Text('Creados')
    skip_first_line = fields.Boolean('Saltear primera linea', default=True)
    client_match = fields.Selection(selection=[('name', 'Nombre')], string='Buscar clientes por...', default='name')


    def btn_process(self):
        _procesados = ""
        _noprocesados = ""
        vals = {}
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
        lines =  self.file_content.replace('\n', '')
        lines = lines.split('\r')

        for i,line in enumerate(lines):
            new_record = None
            if self.skip_first_line and i == 0:
                continue
            lista = line.split(self.delimiter)

            if len(lista) > 7:
                try:
                    titulo = lista[0]
                    emisor = lista[1]
                    pagador = lista[2]
                    codigo = lista[3]
                    fecha_ejecutoria = lista[4]
                    fecha_cuenta_cobro= lista[5]
                    fecha_liquidar = lista[6]
                    valor_condena = lista[7]

                    vals.clear()

                    emisor = self.env['res.partner'].search(
                        [(self.client_match, '=', emisor), ('vinculado', '=', True)])
                    if len(emisor) > 1:
                        raise ValidationError(
                            "El CSV no se procesara por cliente con nombre repetido en sistema. El nombre {0} lo tienen dos o mas clientes".format(
                                emisor))
                    pagador = self.env['res.partner'].search(
                        [(self.client_match, '=', pagador), ('vinculado', '=', True)])
                    if len(emisor) > 1:
                        raise ValidationError(
                            "El CSV no se procesara por pagador con nombre repetido en sistema. El nombre {0} lo tienen dos o mas clientes".format(
                                pagador))

                    titulo_existente = self.env['ctm.sentencias'].search(
                            [('name', '=', titulo)], limit=1)

                    if len(titulo_existente) > 0:
                        vals["fecha_liquidar"] = fecha_liquidar
                        titulo_existente.sudo().write(vals)
                    else:
                        vals = {
                            "name": titulo,
                            "emisor": emisor.id,
                            "pagador": pagador.id,
                            "codigo": codigo,
                            "fecha_ejecutoria": fecha_ejecutoria,
                            "fecha_cuenta_cobro": fecha_cuenta_cobro,
                            "fecha_liquidar": fecha_liquidar,
                            "valor_condena": valor_condena
                        }
                        new_record = self.env['ctm.sentencias'].sudo().create(vals)
                        _procesados += "{0};{1};{2};{3}\n".format(titulo, emisor.name, pagador.name, new_record.id)
                except Exception as e:
                    raise ValidationError(
                        "El CSV no se procesara por estar mal formado en la linea {0}, contenido de linea: {1}. Se necesitan al menos 18 columnas".format(
                            i, line))


        self.clientes_creados = _procesados
        self.not_processed_content = _noprocesados
        self.responsable = self.env.user.partner_id
        self.fch_procesado = datetime.today()
        self.state = 'processed'


