from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64


class CrearSentencias(models.Model):
    _name = 'ctm.crear_sentencias'
    _description = "Crear varias sentencias a la vez"
    _inherit = []

    responsible = fields.Many2one('res.partner', 'Responsable')
    month = fields.Char('Mes de Periodo', required=1)
    year = fields.Char('Año de Periodo', required=1)
    status = fields.Selection([('sin_crear', 'Sin Crear'), ('creados', 'Creados')], default='sin_crear', string='Estado')

    name = fields.Char('Nombre')
    crear_sentencias_ids = fields.One2many('ctm.detalle_crear_sentencias','crear_sentencias_id', 'Sentencias')
    client_file = fields.Binary('Archivo')
    file_content = fields.Text('Texto archivo')
    delimiter = fields.Char('Delimitador', default=";")
    skip_first_line = fields.Boolean('Saltear primera linea', default=True)

    def crear_sentencias(self):
        for sentencia in self.crear_sentencias_ids:
            exists_liquidacion= self.env['ctm.liquidaciones'].sudo().search([
                ('sentencia', '=', sentencia.id),
            ])

            if not exists_liquidacion:
                created_liquidacion = self.env['ctm.liquidaciones'].sudo().create({
                    'sentencia': sentencia.id,
                })
                created_liquidacion.generar_liquidacion()

        self.status = 'creados'



    def action_cargar_sentencias(self):
        self.ensure_one()
        if not self.delimiter:
            raise ValidationError('Debe ingresar el delimitador')
        if not self.client_file:
            raise ValidationError('Debe seleccionar el archivo')

        self.file_content = base64.decodebytes(self.client_file)
        content = self.file_content.replace('\n', '')
        lines = content.split('\r')


        for detalle  in self.crear_sentencias_ids:
            detalle.unlink()

        for i,line in enumerate(lines):
            if self.skip_first_line and i == 0:
                continue
            lista = line.split(self.delimiter)
            sentencia_name = lista[0]

            sentencia = self.env['ctm.sentencias'].sudo().search(
                [('name', '=', sentencia_name)])

            # Agregando clientes al detalle de seguidores

            self.env['ctm.detalle_crear_sentencias'].create({
                'crear_sentencias_id': self.id,
                'sentencia': sentencia.id,
            })


    @api.model
    def create(self, var):
        res = super(CrearSentencias, self).create(var)
        res.name = 'Sentencias ' + res.month + '/' + res.year
        return res


class DetalleCrearSentencias(models.Model):
    _name = 'ctm.detalle_crear_sentencias'

    crear_sentencias_id = fields.Many2one('ctm.crear_sentencias', 'Crear Sentencias')
    sentencia = fields.Many2one('ctm.sentencias', 'Sentencia')