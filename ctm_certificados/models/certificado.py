 # -*- coding: utf-8 -*-

from email.policy import default
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
import base64


logger = logging.getLogger(__name__)

class Certificado(models.Model):
    _name = 'ctm.certificado'
    _description = "Certificado"
    _inherit = ['portal.mixin', 'mail.thread','mail.activity.mixin']

    name = fields.Char('Nombre')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    cliente = fields.Many2one('res.partner', 'Cliente', required=1)
    year = fields.Char('Año', required=1)
    type = fields.Selection(selection=[('retencion','Retención'),('comprador','Comprador')],string='Tipo de Certificado',default='comprador')
    state = fields.Selection(
        selection=[('draft', 'Borrador'), ('processed', 'Procesado')],
        string='Estado', default='draft')

    #Comprador
    facturas_valor = fields.Float('Facturas Total')
    facturas_rendimiento = fields.Float('Facturas Rendimiento')
    sentencias_valor = fields.Float('Sentencias Total')
    sentencias_rendimiento = fields.Float('Sentencias Rendimiento')
    libranzas_valor = fields.Float('Libranzas Total')
    libranzas_rendimiento = fields.Float('Libranzas Rendimiento')
    mutuos_valor = fields.Float('Mutuos Total')
    mutuos_rendimiento = fields.Float('Mutuos Rendimiento')
    rpr_valor = fields.Float('RPR Total')
    rpr_rendimiento = fields.Float('RPR Rendimiento')

    #Retención
    concepto = fields.Char('CONCEPTO DEL PAGO SUJETO A LA RETENCION')
    porcentaje = fields.Char('PORCENTAJE APLICADO')
    cuantia = fields.Float(' CUANTIA DE LA RETENCION ')

    def _compute_access_url(self):
        super(Certificado, self)._compute_access_url()
        for order in self:
            order.access_url = '/my/certificate/%s' % (order.id)

    def _get_report_base_filename(self):
        self.ensure_one()
        return 'Certificado %s' % (self.name)

    def generar_certificado(self):
        if self.type == 'comprador':
            #Extractos año
            extractos = self.env['ati.extracto'].search([
                ('cliente', '=', self.cliente.id),
                ('year', '=', self.year),
            ])
            #último extracto del año
            extracto_id = self.env['ati.extracto'].search([
                ('cliente', '=', self.cliente.id),
                ('year', '=', self.year),
                ('month', '=', 12),
            ], limit=1)

            #Para obtener valores
            products = extracto_id.resumen_inversion_ids.filtered(
                lambda x: x.gestor.code == 'CUANTUM' or x.name == 'RPR CSF'
            )
            for product in products:
                if product.producto.code == 'FAC':
                    self.facturas_valor = product.valor_actual
                elif product.producto.code == 'SEN':
                    self.sentencias_valor = product.valor_actual
                elif product.producto.code == 'LIB':
                    self.libranzas_valor = product.valor_actual
                elif product.producto.code == 'MUT':
                    self.mutuos_valor = product.valor_actual
                elif product.name == 'RPR CSF':
                    self.rpr_valor = product.valor_actual

            #Para calcular rendimientos
            facturas_rendimiento = 0
            sentencias_rendimiento = 0
            libranzas_rendimiento = 0
            mutuos_rendimiento = 0
            rpr_rendimiento = 0
            for extracto in extractos:
                products = extracto.resumen_inversion_ids.filtered(
                    lambda x: x.gestor.code == 'CUANTUM' or x.name == 'RPR CSF'
                )
                for product in products:
                    if product.producto.code == 'FAC':
                        facturas_rendimiento += product.rendimiento_causado
                    elif product.producto.code == 'SEN':
                        sentencias_rendimiento += product.rendimiento_causado
                    elif product.producto.code == 'LIB':
                        libranzas_rendimiento += product.rendimiento_causado
                    elif product.producto.code == 'MUT':
                        mutuos_rendimiento += product.rendimiento_causado
                    elif product.name == 'RPR CSF':
                        rpr_rendimiento += product.rendimiento_causado

            self.facturas_rendimiento = facturas_rendimiento
            self.sentencias_rendimiento = sentencias_rendimiento
            self.libranzas_rendimiento = libranzas_rendimiento
            self.mutuos_rendimiento = mutuos_rendimiento
            self.rpr_rendimiento = rpr_rendimiento

        if self.type == 'retencion':
            retencion = self.env['ctm.retencion'].search([
                ('retenido', '=', self.cliente.id),
                ('year', '=', self.year),
            ], limit=1)

            if not retencion:
                raise ValidationError('No existe una retención para {0}-{1}'.format(self.cliente.name, self.year))

            self.concepto = retencion.concepto
            self.porcentaje = retencion.porcentaje
            self.cuantia = retencion.cuantia
        self.state = 'processed'

    @api.model
    def create(self, var):
        res = super(Certificado, self).create(var)
        res.name = 'Certificado/' + res.type + '/' + res.cliente.name + '/' + res.year
        return res


class CreateCertificates(models.Model):
    _name = 'ctm.create_certificates'
    _description = "Crear varios certificados a la vez"
    _inherit = []

    responsible = fields.Many2one('res.partner', 'Responsable')
    year = fields.Char('Año de Periodo', required=1)
    type = fields.Selection(selection=[('retencion', 'Retención'), ('comprador', 'Comprador')],
                            string='Tipo de Certificado', default='comprador')
    status = fields.Selection([('sin_crear', 'Sin Crear'), ('creados', 'Creados')], default='sin_crear', string='Estado')

    name = fields.Char('Nombre')
    create_certificates_users_ids = fields.One2many('ctm.detalle_create_certificates','create_certificates_id', 'Clientes')
    client_file = fields.Binary('Archivo')
    file_content = fields.Text('Texto archivo')
    delimiter = fields.Char('Delimitador', default=";")
    skip_first_line = fields.Boolean('Saltar primera linea', default=True)

    def crear_certificados(self):
        for cliente in self.create_certificates_users_ids:
            exists_certificate= self.env['ctm.certificado'].sudo().search([
                ('cliente', '=', cliente.cliente.id),
                ('year', '=', self.year),
                ('type', '=', self.type)
            ])

            if not exists_certificate:
                created_certificate = self.env['ctm.certificado'].sudo().create({
                    'cliente': cliente.cliente.id,
                    'year': self.year,
                    'type': self.type

                })
                created_certificate.generar_certificado()
            else:
                raise ValidationError(
                    'Ya existe un certificado para {0}-{1}'.format( cliente.cliente.name, self.year))


        self.status = 'creados'


    def action_cargar_clientes(self):
        self.ensure_one()
        if not self.delimiter:
            raise ValidationError('Debe ingresar el delimitador')
        if not self.client_file:
            raise ValidationError('Debe seleccionar el archivo')

        self.file_content = base64.decodebytes(self.client_file)
        lines = self.file_content.split('\r')

        for detalle  in self.create_certificates_users_ids:
            detalle.unlink()

        for i,line in enumerate(lines):
            if self.skip_first_line and i == 0:
                continue
            lista = line.split(self.delimiter)
            vat = lista[0].split('\n')[1]

            clients = self.env['res.partner'].sudo().search(
                [('vat', '=', str(vat))])

            # Agregando clientes al detalle de seguidores
            for y in clients:
                self.env['ati.detalle_create_certificates'].create({
                    'create_certificates_id': self.id,
                    'cliente': y.id,
                    'vat': y.vat,
                })


    @api.model
    def create(self, var):
        res = super(CreateCertificates, self).create(var)
        res.name = 'Certificados/ ' + res.type + '/' + res.year
        return res


class DetalleCreateExtractos(models.Model):
    _name = 'ctm.detalle_create_certificates'

    create_certificates_id = fields.Many2one('ati.create_certificates', 'Crear Certificados')
    cliente = fields.Many2one('res.partner', 'Cliente')
    vat = fields.Char('NIT')
