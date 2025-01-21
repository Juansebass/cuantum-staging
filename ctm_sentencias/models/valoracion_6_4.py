# -*- coding: utf-8 -*-

from odoo import models, fields, api  # type: ignore
from odoo.exceptions import ValidationError  # type: ignore
import base64


class Valoracion64(models.Model):
    _name = 'ctm.valoracion_6_4'
    _description = "Valoración 6.4"
    _inherit = []

    name = fields.Char('Nombre')
    sentencia = fields.Many2one('ctm.sentencias', 'Sentencia', required=1)
    emisor = fields.Many2one('res.partner', 'Emisor')
    pagador = fields.Many2one('res.partner', 'Pagador')
    codigo = fields.Char('Código')
    fecha_ejecutoria = fields.Date('Fecha de Ejecutoría')
    fecha_cuenta_cobro = fields.Date('Fecha de Cuenta de Cobro')
    fecha_liquidar = fields.Date('Fecha a Liquidar')
    valor_condena = fields.Float('Valor Condena')
    resultado = fields.Float('Resultado')
    total_intereses = fields.Float('Total Intereses')
    valoraciones_resumen_ids = fields.One2many('ctm.valoracion_6_4_resumen', 'valoracion_6_4_id', 'Resumen Valoración 6.4')
    responsible = fields.Many2one('res.partner', 'Responsable')
    state = fields.Selection(selection=[('draft', 'Borrador'), ('liquidated', 'Liquidado')], string='Estado', default='draft')
    simulacion_ids = fields.One2many('ctm.valoracion_6_4_simulacion', 'valoracion_6_4_id')
    tir_sentencia_bruta = fields.Float('TIR Sentencia Bruta')

    nit_fcp_statum = fields.Char('NIT FCP STATUM (Comp 1)', related='sentencia.nit_fcp_statum')
    statum = fields.Selection(string='Statum', related='sentencia.statum')
    vendedor = fields.Char('Vendedor', related='sentencia.vendedor')
    nemotecnico = fields.Char('Nemotecnico', related='sentencia.nemotecnico')
    fecha_vencimiento = fields.Date('Fecha de Vencimiento', related='sentencia.fecha_vencimiento')
    fecha_compra = fields.Date('Fecha de Compra', related='sentencia.fecha_compra')
    valor_giro = fields.Float('Valor Giro', related='sentencia.valor_giro')
    comision = fields.Float('Comisión', related='sentencia.comision')
    valor_contable_ayer = fields.Float('Valor Contable Ayer')
    precio = fields.Float('Precio', digits=(16, 7))

    def generar_valoracion(self):
        pass


class Valoracion64Resumen(models.Model):
    _name = 'ctm.valoracion_6_4_resumen'
    _description = "Valoraciones 6.4 Resumen Cuantum"
    _inherit = []

    valoracion_6_4_id = fields.Many2one('ctm.valoracion_6_4', 'Valoración 6.4', ondelete='cascade')
    fecha = fields.Date('Fecha', required=1)
    tasa = fields.Float('Tasa', digits=(10, 6))
    interes = fields.Float('Interés')


class Valoracion64Simulacion(models.Model):
    _name = 'ctm.valoracion_6_4_simulacion'
    _description = 'Valoración 6.4 Simulación'

    name = fields.Char('Nombre', required=True)
    valoracion_6_4_id = fields.Many2one('ctm.valoracion_6_4', 'Valoración 6.4', required=True, ondelete='cascade')
    fecha_ejecutoria = fields.Date('Fecha de Ejecutoría')
    fecha_cuenta_cobro = fields.Date('Fecha de Cuenta de Cobro')
    fecha_liquidar = fields.Date('Fecha a Liquidar')
    valor_condena = fields.Float('Valor Condena')
    total_intereses = fields.Float('Total Intereses')
    resultado = fields.Float('Resultado')
    tir_sentencia_bruta = fields.Float('TIR Sentencia Bruta')


class CrearValoracion64(models.Model):
    _name = 'ctm.crear_valoracion_6_4'
    _description = "Crear Valoración 6.4"
    _inherit = []

    responsible = fields.Many2one('res.partner', 'Responsable')
    month = fields.Char('Mes de Periodo', required=1)
    year = fields.Char('Año de Periodo', required=1)
    status = fields.Selection([('sin_crear', 'Sin Crear'), ('creados', 'Creados')], default='sin_crear', string='Estado')

    name = fields.Char('Nombre')
    valoracion_6_4_ids = fields.One2many('ctm.detalle_valoracion_6_4', 'valoracion_6_4_id', 'Valoraciones')
    client_file = fields.Binary('Archivo')
    file_content = fields.Text('Texto archivo')
    delimiter = fields.Char('Delimitador', default=";")
    skip_first_line = fields.Boolean('Saltar primera linea', default=True)

    def crear_valoraciones(self):
        for valoracion in self.valoracion_6_4_ids:
            exists_valoracion = self.env['ctm.valoracion_6_4'].sudo().search([
                ('sentencia', '=', valoracion.sentencia.id),
            ])

            if not exists_valoracion:
                try:
                    created_valoracion = self.env['ctm.valoracion_6_4'].sudo().create({
                        'sentencia': valoracion.sentencia.id,
                    })
                    created_valoracion.generar_valoracion()
                except Exception as e:
                    raise ValidationError('error {0}. para sentencia {1}'.format(e, valoracion.sentencia.id))

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

        for detalle in self.valoracion_6_4_ids:
            detalle.unlink()

        for i, line in enumerate(lines):
            if self.skip_first_line and i == 0:
                continue
            lista = line.split(self.delimiter)
            sentencia_name = lista[0]
            sentencia = self.env['ctm.sentencias'].sudo().search([('name', '=', sentencia_name)], limit=1)
            if not sentencia:
                raise ValidationError('No se encontró sentencia con nombre {0}'.format(sentencia_name))

            self.env['ctm.detalle_valoracion_6_4'].sudo().create({
                'valoracion_6_4_id': self.id,
                'sentencia': sentencia.id,
            })

    @api.model
    def create(self, var):
        res = super(CrearValoracion64, self).create(var)
        res.name = 'Valoración ' + res.month + '/' + res.year
        return res


class DetalleValoracion64(models.Model):
    _name = 'ctm.detalle_valoracion_6_4'
    _description = "Detalle Valoración 6.4"
    _inherit = []

    valoracion_6_4_id = fields.Many2one('ctm.crear_valoracion_6_4', 'Valoración 6.4', ondelete='cascade')
    sentencia = fields.Many2one('ctm.sentencias', 'Sentencia', required=1)
