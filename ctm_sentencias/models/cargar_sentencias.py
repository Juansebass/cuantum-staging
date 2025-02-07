from odoo import models, fields  # type: ignore
from odoo.exceptions import ValidationError  # type: ignore
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
    state = fields.Selection(
        selection=[('draft', 'Borrador'), ('processed', 'Procesado')],
        string='Estado',
        default='draft'
    )
    file_content = fields.Text('Texto archivo')
    not_processed_content = fields.Text('Texto no procesado')
    clientes_creados = fields.Text('Creados')
    skip_first_line = fields.Boolean('Saltear primera linea', default=True)
    client_match = fields.Selection(
        selection=[('name', 'Nombre')],
        string='Buscar clientes por...',
        default='name'
    )

    def btn_process(self):
        _procesados = ""
        _noprocesados = ""
        vals = {}
        self.ensure_one()
        if not self.client_match:
            raise ValidationError(
                'Debe seleccionar metodo de busqueda de clientes'
            )
        if not self.delimiter:
            raise ValidationError('Debe ingresar el delimitador')
        if not self.client_file:
            raise ValidationError('Debe seleccionar el archivo')
        if self.state != 'draft':
            raise ValidationError('Archivo procesado!')

        self.file_content = base64.decodebytes(self.client_file)
        lines = self.file_content.replace('\n', '')
        lines = lines.split('\r')

        for i, line in enumerate(lines):
            new_record = None
            if self.skip_first_line and i == 0:
                continue
            lista = line.split(self.delimiter)

            if len(lista) < 2:
                pass
            elif len(lista) > 6:
                try:
                    titulo = lista[0]
                    emisor = lista[1]
                    pagador = lista[2]
                    codigo = lista[3]
                    statum = lista[4]
                    fecha_ejecutoria = lista[5]
                    fecha_cuenta_cobro = lista[6]
                    fecha_liquidar = lista[7]
                    valor_condena = lista[8]
                    nit_fcp_statum = lista[9]
                    vendedor = lista[10]
                    nemotecnico = lista[11]
                    fecha_vencimiento = lista[12]
                    fecha_compra = lista[13]
                    valor_giro = lista[14]
                    comision = lista[15]
                    costas = lista[16]
                    retencion_total = lista[17]
                    estructuracion = lista[18]
                    intermediacion = lista[19]
                    descuento_diluido = lista[20]
                    comision_gestion_cuantum = lista[21]
                    ingreso_anticipado_cuantum = lista[22]
                    fecha_liquidar_neutral = lista[23]
                    fecha_liquidar_optimista = lista[24]
                    fecha_liquidar_acido = lista[25]

                    vals.clear()

                    emisor = self.env['res.partner'].search(
                        [
                            (self.client_match, '=', emisor),
                            ('act_in', '=', 'activo')
                        ])
                    if len(emisor) > 1:
                        raise ValidationError(
                            "El CSV no se procesara por cliente con nombre repetido en sistema. "
                            "El nombre {0} lo tienen dos o mas clientes".format(emisor))
                    elif len(emisor) == 0:
                        raise ValidationError(
                            "El CSV no se procesara porque no se encuentra emisor o no está vinculado {0}".format(
                                emisor)
                        )
                    pagador = self.env['res.partner'].search(
                        [
                            (self.client_match, '=', pagador),
                            ('act_in', '=', 'activo')
                        ])
                    if len(emisor) > 1:
                        raise ValidationError(
                            "El CSV no se procesara por pagador con nombre repetido en sistema. El nombre {0} lo tienen dos o mas clientes".format(
                                pagador))
                    elif len(pagador) == 0:
                        raise ValidationError(
                            "El CSV no se procesara porque no se encuentra pagador "
                            "o no está vinculado {0}".format(pagador)
                        )

                    titulo_existente = self.env['ctm.sentencias'].search(
                        [('name', '=', titulo)], limit=1)

                    if len(titulo_existente) > 0:
                        vals["fecha_liquidar"] = datetime.strptime(
                            fecha_liquidar, '%d/%m/%Y')
                        titulo_existente.sudo().write(vals)
                    else:
                        formated_valor_condena = self._format_money(
                            valor_condena
                        )
                        formated_valor_giro = self._format_money(
                            valor_giro
                        )
                        formated_comision = self._format_money(
                            comision
                        )
                        formated_estructuracion = self._format_money(
                            estructuracion
                        )
                        formated_costas = self._format_money(
                            costas
                        )
                        vals = {
                            "name": titulo,
                            "emisor": emisor.id,
                            "pagador": pagador.id,
                            "codigo": codigo,
                            "statum": statum,
                            "fecha_ejecutoria": datetime.strptime(
                                fecha_ejecutoria, '%d/%m/%Y'
                            ),
                            "fecha_cuenta_cobro": datetime.strptime(
                                fecha_cuenta_cobro, '%d/%m/%Y'
                            ),
                            "fecha_liquidar": datetime.strptime(
                                fecha_liquidar, '%d/%m/%Y'
                            ),
                            "valor_condena": formated_valor_condena,
                            "nit_fcp_statum": nit_fcp_statum,
                            "vendedor": vendedor,
                            "nemotecnico": nemotecnico,
                            "fecha_vencimiento": datetime.strptime(
                                fecha_vencimiento, '%d/%m/%Y'
                            ) if fecha_vencimiento else None,
                            "fecha_compra": datetime.strptime(
                                fecha_compra, '%d/%m/%Y'
                            ) if fecha_compra else None,
                            "valor_giro": formated_valor_giro,
                            "comision": formated_comision,
                            "costas": formated_costas,
                            "retencion_total": self._format_percent(
                                retencion_total
                            ),
                            "estructuracion": formated_estructuracion,
                            "intermediacion": self._format_percent(
                                intermediacion
                            ),
                            "descuento_diluido": self._format_percent(
                                descuento_diluido
                            ),
                            "comision_gestion_cuantum":
                                self._format_percent(comision_gestion_cuantum),
                            "ingreso_anticipado_cuantum":
                                self._format_percent(
                                    ingreso_anticipado_cuantum
                            ),
                            "fecha_liquidar_neutral": datetime.strptime(
                                fecha_liquidar_neutral, '%d/%m/%Y'
                            ) if fecha_liquidar_neutral else None,
                            "fecha_liquidar_optimista": datetime.strptime(
                                fecha_liquidar_optimista, '%d/%m/%Y'
                            ) if fecha_liquidar_optimista else None,
                            "fecha_liquidar_acido": datetime.strptime(
                                fecha_liquidar_acido, '%d/%m/%Y'
                            ) if fecha_liquidar_acido else None
                        }
                        new_record = self.env['ctm.sentencias'].sudo().create(
                            vals)
                        _procesados += "{0};{1};{2};{3}\n".format(
                            titulo, emisor.name, pagador.name, new_record.id)
                except Exception as e:
                    raise ValidationError(
                        "El CSV no se procesara por el siguente error {0}, "
                        "contenido de linea: {1}.".format(e, line))
            else:
                raise ValidationError(
                    "El CSV no se procesara"
                    "mal formado en la linea {0}, "
                    "contenido de linea: {1}. "
                    "Se necesitan al menos 8 columnas. "
                    "{2}".format(i, line, lista)
                )

        self.clientes_creados = _procesados
        self.not_processed_content = _noprocesados
        self.responsable = self.env.user.partner_id
        self.fch_procesado = datetime.today()
        self.state = 'processed'

    def _format_money(self, money):
        return (
            money.replace('$', '')
            .replace(' ', '')
            .replace('.', '')
            .replace(',', '.')
            .replace('-', '')
        )

    def _format_percent(self, percent):
        return float(
            percent.replace('%', '')
            .replace(' ', '')
            .replace('.', '')
            .replace(',', '.')
            .replace('-', '')
        ) / 100
