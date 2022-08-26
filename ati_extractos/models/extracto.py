 # -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

class Extracto(models.Model):
    _name = 'ati.extracto'
    _description = "Extracto"
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char('Nombre')

    cliente = fields.Many2one('res.partner','Cliente',required=1)
    email_cliente = fields.Char('Email',related='cliente.email')
    month = fields.Char('Mes de Periodo',required=1)
    year = fields.Char('Año de Periodo',required=1)

    #Campos para resumen de inversiones
    resumen_inversion_ids = fields.One2many('ati.extracto.resumen_inversion','extracto_id','Resumen Inversiones')

    detalle_movimiento_ids = fields.One2many('ati.extracto.detalle_movimiento','extracto_id','Detalle de Movimientos')

    detalle_titulos_ids = fields.One2many('ati.extracto.detalle_titulos','extracto_id','Detalle de Titulos')

    state = fields.Selection(selection=[('draft','Borrador'),('processed','Procesado'),('send','Enviado')],string='Estado',default='draft')

    def generar_extracto(self):
        # Se valida si existe el periodo al cual se decea hacer un extractos, en el caso de existir se verifica que el 
        # estado del mismo se encuentre en estado abierto de cargue
        if self.month and self.year:
            periodo = self.env['ati.state.periodo'].search([('year','=',self.year),('month','=',self.month)])
            if len(periodo) > 0:
                if periodo.state_consulta_extracto == 'close':
                    raise ValidationError('El estado de extracto para este periodo se encuentra cerrado')
            else:
                raise ValidationError('No existe un periodo creado para el mes y año seleccionado')
        else:
            raise ValidationError('Debe introducir un mes y año de periodo para este cargue')

        # MOVIMIENTOS
        #  FCL
        self.detalle_movimiento_ids = False
        for mfcl in self.cliente.recursos_recompra_fcl_ids:
            self.env['ati.extracto.detalle_movimiento'].create({
                'extracto_id' : self.id,
                'tipo' : mfcl.movement_type.name,
                'valor' : mfcl.value
            })
            
        # TITULOS
        titulos_cliente = self.env['ati.titulo'].search([('client.id','=',self.cliente.id)])
        self.detalle_titulos_ids = False
        for titulos in titulos_cliente:
            self.env['ati.extracto.detalle_titulos'].create({
                'extracto_id' : self.id,
                'titulo' : titulos.id
            })

        #raise ValidationError('Esta funcionalidad generara un extracto {0}'.format(titulos_cliente))

    def enviar_extracto(self):
        # Se valida si existe el periodo al cual se decea hacer un extractos, en el caso de existir se verifica que el 
        # estado del mismo se encuentre en estado abierto de cargue
        if self.month and self.year:
            periodo = self.env['ati.state.periodo'].search([('year','=',self.year),('month','=',self.month)])
            if len(periodo) > 0:
                if periodo.state_envio_extracto == 'close':
                    raise ValidationError('El estado de extracto para este periodo se encuentra cerrado')
            else:
                raise ValidationError('No existe un periodo creado para el mes y año seleccionado')
        else:
            raise ValidationError('Debe introducir un mes y año de periodo para este cargue')


        raise ValidationError('Esta funcionalidad enviara el extracto')

    @api.model
    def create(self, var):

        res = super(Extracto, self).create(var)
        res.name = res.cliente.name + ' - ' + res.month + "/" + res.year

        return res

class ResumenInversiones(models.Model):
    _name = 'ati.extracto.resumen_inversion'

    extracto_id = fields.Many2one('ati.extracto','Extracto')
    producto = fields.Float('Producto')
    valor_actual = fields.Float('Valor Actual')
    valor_anterior = fields.Float('Valor Anterior')
    diferencia = fields.Float('Participacion')
    rendimiento_causado = fields.Float('Rendimiento Causado')
    tasa_rendimiento = fields.Float('Tasa Rendimiento')

class DetalleMovimiento(models.Model):
    _name = 'ati.extracto.detalle_movimiento'

    extracto_id = fields.Many2one('ati.extracto','Extracto')
    tipo = fields.Char('Tipo')
    valor = fields.Float('Valor')

class DetalleTitulos(models.Model):
    _name = 'ati.extracto.detalle_titulos'

    extracto_id = fields.Many2one('ati.extracto','Extracto')
    titulo = fields.Many2one('ati.titulo','Titulo')
    investment_type = fields.Char('Tipo',related="titulo.investment_type.name")
    issuing = fields.Many2one('res.partner','Emisor',related="titulo.issuing")
    payer = fields.Many2one('res.partner','Pagador',related="titulo.payer")
    value = fields.Float('Valor de portafolio',related="titulo.value")
    fee = fields.Float('Tasa',related="titulo.fee")