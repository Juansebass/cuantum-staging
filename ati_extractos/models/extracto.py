 # -*- coding: utf-8 -*-

from email.policy import default
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

class Extracto(models.Model):
    _name = 'ati.extracto'
    _description = "Extracto"
    _inherit = ['portal.mixin', 'mail.thread','mail.activity.mixin']

    name = fields.Char('Nombre')

    cliente = fields.Many2one('res.partner','Cliente',required=1)
    email_cliente = fields.Char('Email',related='cliente.email')
    month = fields.Char('Mes de Periodo',required=1)
    year = fields.Char('Año de Periodo',required=1)

    #Campos para resumen de inversiones
    resumen_inversion_ids = fields.One2many('ati.extracto.resumen_inversion','extracto_id','Resumen Inversiones Fideicomiso Cuantum Libranzas')

    detalle_movimiento_ids = fields.One2many('ati.extracto.detalle_movimiento','extracto_id','Detalle de Movimientos')

    detalle_titulos_ids = fields.One2many('ati.extracto.detalle_titulos','extracto_id','Detalle de Titulos')

    state = fields.Selection(selection=[('draft','Borrador'),('processed','Procesado'),('send','Enviado')],string='Estado',default='draft')


    # _compute_access_url _get_report_base_filename son utilizadas para generar el extracto desde el portal
    def _compute_access_url(self):
        super(Extracto, self)._compute_access_url()
        for order in self:
            order.access_url = '/my/extracto/%s' % (order.id)

    def _get_report_base_filename(self):
        self.ensure_one()
        return 'Extracto %s' % (self.name)

    def _get_value_before(self,producto,gestor,month,year):
        #Verificamos que el mes no se Enero, de lo contrario pasamos a diciembre del año anterior
        if month == '1':
            month = '12'
            year = str(int(year) - 1)
        else:
            if (int(month) - 1) > 9 :
                month = str(int(month) - 1)
            else:
                month = '0' + str(int(month) - 1)
        value = self.env['ati.extracto.resumen_inversion'].search([('extracto_id.cliente.id','=',self.cliente.id),
                                                                    ('producto.id','=',producto),
                                                                    ('gestor.id','=',gestor),
                                                                    ('extracto_id.month','=',month),
                                                                    ('extracto_id.year','=',year)
                                                                    ])
        if len(value) > 0:
            return value.valor_actual
        else:
            return 0

    def _generar_resumen_inversion(self):
        #Seteamos el periodo a buscar y obtenemos todos los movimientos del modelo ati.titulo.historico
        periodo = self.month + '/' + self.year
        movimientos = self.env['ati.titulo.historico'].search([('client','=',self.cliente.id),('periodo','=', periodo),('titulo_id','!=',False)])
        
        #Eliminamos todos los registro que pueda tener la tabla inversiones para luego agregar los correspondientes
        for inv in self.resumen_inversion_ids:
            inv.unlink()

        #FCL
        self.resumen_inversion_ids = [(0,0,{
                'gestor' : self.env['ati.gestor'].search([('code','=','FCL')]).id,
                'display_type' : 'line_section'
            })]
        _inversiones = []
        for moviemiento in movimientos:
            if moviemiento.manager.code == 'FCL':
                prod_cargado = False
                index = 0
                # Recorremos las inversiones en FCL para consultar si el tipo de producto ya se cargo, en tal caso sumamos su vpn al producto ya cargado
                for i in _inversiones:
                    if i[2]['producto'] == moviemiento.investment_type.id:
                        _inversiones[index] = (0,0,{
                            'producto' : moviemiento.investment_type.id,
                            'valor_actual' : moviemiento.value + i[2]['valor_actual'],
                            'valor_anterior' : i[2]['valor_anterior'],
                            'rendimiento_causado' : 0,
                            'tasa_rendimiento' : moviemiento.fee + i[2]['tasa_rendimiento'],
                            'gestor' : moviemiento.manager.id,
                            'cant_movimientos' : 1 + i[2]['cant_movimientos']
                        })
                        prod_cargado = True
                    index += 1

                # Cargamos el producto a la lista de inversion si todavia no se cargo
                if not prod_cargado:
                    _inversiones.append((0,0,{
                        'producto' : moviemiento.investment_type.id,
                        'valor_actual' : moviemiento.value,
                        'valor_anterior' : self._get_value_before(moviemiento.investment_type.id,moviemiento.manager.id,self.month,self.year),
                        'rendimiento_causado' : 0,
                        'tasa_rendimiento' : moviemiento.fee,
                        'gestor' : moviemiento.manager.id,
                        'cant_movimientos' : 1
                    }))
        #Promediamos las tasas de inversiones
        for n in range(len(_inversiones)):
            _inversiones[n][2].update({'tasa_rendimiento' : round((_inversiones[n][2]['tasa_rendimiento'] / _inversiones[n][2]['cant_movimientos']), 2)})
        #Calculamos Participacion
        for n in range(len(_inversiones)):
            _inversiones[n][2].update({'diferencia' : round((_inversiones[n][2]['valor_actual'] - _inversiones[n][2]['valor_anterior']), 2)})
        self.resumen_inversion_ids = _inversiones


        #######################
        #FCP
        self.resumen_inversion_ids = [(0,0,{
                'gestor' : self.env['ati.gestor'].search([('code','=','FCP')]).id,
                'display_type' : 'line_section'
            })]
        _inversiones = []
        for moviemiento in movimientos:
            if moviemiento.manager.code == 'FCP':
                prod_cargado = False
                index = 0
                # Recorremos las inversiones en FCP para consultar si el tipo de producto ya se cargo, en tal caso sumamos su vpn al producto ya cargado
                for i in _inversiones:
                    if i[2]['producto'] == moviemiento.investment_type.id:
                        _inversiones[index] = (0,0,{
                            'producto' : moviemiento.investment_type.id,
                            'valor_actual' : moviemiento.value + i[2]['valor_actual'],
                            'valor_anterior' : 0,
                            'rendimiento_causado' : 0,
                            'tasa_rendimiento' : moviemiento.fee + i[2]['tasa_rendimiento'],
                            'gestor' : moviemiento.manager.id,
                            'cant_movimientos' : 1 + i[2]['cant_movimientos']
                        })
                        prod_cargado = True
                    index += 1

                # Cargamos el producto a la lista de inversion si todavia no se cargo
                if not prod_cargado:
                    _inversiones.append((0,0,{
                        'producto' : moviemiento.investment_type.id,
                        'valor_actual' : moviemiento.value,
                        'valor_anterior' : 0,
                        'rendimiento_causado' : 0,
                        'tasa_rendimiento' : moviemiento.fee,
                        'gestor' : moviemiento.manager.id,
                        'cant_movimientos' : 1
                    }))
        #Promediamos las tasas de inversiones
        for n in range(len(_inversiones)):
            _inversiones[n][2].update({'tasa_rendimiento' : round((_inversiones[n][2]['tasa_rendimiento'] / _inversiones[n][2]['cant_movimientos']), 2)})
        #Calculamos Participacion
        for n in range(len(_inversiones)):
            _inversiones[n][2].update({'diferencia' : round((_inversiones[n][2]['valor_actual'] - _inversiones[n][2]['valor_anterior']), 2)})
        self.resumen_inversion_ids = _inversiones
        

        #######################
        #CUANTUM
        self.resumen_inversion_ids = [(0,0,{
            'gestor' : self.env['ati.gestor'].search([('code','=','CUANTUM')]).id,
            'display_type' : 'line_section'
        })]
        _inversiones = []
        for moviemiento in movimientos:
            if moviemiento.manager.code == 'CUANTUM':
                prod_cargado = False
                ind = 0
                # Recorremos las inversiones en CUANTUM para consultar si el tipo de producto ya se cargo, en tal caso sumamos su vpn al producto ya cargado
                for i in _inversiones:
                    if i[2]['producto'] == moviemiento.investment_type.id:
                        _inversiones[ind] = (0,0,{
                            'producto' : moviemiento.investment_type.id,
                            'valor_actual' : moviemiento.value + i[2]['valor_actual'],
                            'valor_anterior' : 0,
                            'rendimiento_causado' : 0,
                            'tasa_rendimiento' : moviemiento.fee + i[2]['tasa_rendimiento'],
                            'gestor' : moviemiento.manager.id,
                            'cant_movimientos' : 1 + i[2]['cant_movimientos']
                        })
                        prod_cargado = True
                    ind += 1

                # Cargamos el producto a la lista de inversion si todavia no se cargo
                if not prod_cargado:
                    _inversiones.append((0,0,{
                        'producto' : moviemiento.investment_type.id,
                        'valor_actual' : moviemiento.value,
                        'valor_anterior' : 0,
                        'rendimiento_causado' : 0,
                        'tasa_rendimiento' : moviemiento.fee,
                        'gestor' : moviemiento.manager.id,
                        'cant_movimientos' : 1
                    }))
        #Promediamos las tasas de inversiones
        for n in range(len(_inversiones)):
            _inversiones[n][2].update({'tasa_rendimiento' : round((_inversiones[n][2]['tasa_rendimiento'] / _inversiones[n][2]['cant_movimientos']), 2)})
        #Calculamos diferencia 
        for n in range(len(_inversiones)):
            _inversiones[n][2].update({'diferencia' : round((_inversiones[n][2]['valor_actual'] - _inversiones[n][2]['valor_anterior']), 2)})
        self.resumen_inversion_ids = _inversiones
        
        #Calculamos totales
        total_valor_actual = 0
        total_valor_anterior = 0
        total_rendimiento_causado = 0
        total_tasa_rendimiento = 0
        total_diferencia = 0

        logger.warning('***** resumen_inversion_ids: {0}'.format(self.resumen_inversion_ids))
        for ri in self.resumen_inversion_ids:
            logger.warning('***** valor: {0}'.format(ri.valor_actual))
            total_valor_actual += ri.valor_actual
            total_valor_anterior += ri.valor_anterior
            total_rendimiento_causado += ri.rendimiento_causado
            total_tasa_rendimiento += ri.tasa_rendimiento
            total_diferencia += ri.diferencia


        #######################
        #TOTALES
        self.resumen_inversion_ids = [(0,0,{
            'is_total' : True,
            'display_type' : 'line_section'
        })]
        self.resumen_inversion_ids = [(0,0,{
            'valor_actual' : total_valor_actual,
            'valor_anterior' : total_valor_anterior,
            'rendimiento_causado' : total_rendimiento_causado,
            'tasa_rendimiento' : total_tasa_rendimiento,
            'diferencia' : total_diferencia,
        })]

        #Luego de calcular los totales ya podemos calcular la participacion que lo hacemos en base a la ultima linea del resumen ya que es la que tiene los totales
        #self.resumen_inversion_ids[-1]
        for ri in self.resumen_inversion_ids:
            if ri.id != self.resumen_inversion_ids[-1].id and ri.display_type != 'line_section':
                ri.participacion = (ri.valor_actual * 100 ) / self.resumen_inversion_ids[-1].valor_actual
                #Sumamos la participacion total
                self.resumen_inversion_ids[-1].participacion += ri.participacion

    def _generar_resumen_movimientos(self):
        #Borramos los datos que puede haber en detalle_movimiento_ids
        for dm in self.detalle_movimiento_ids:
            dm.unlink()

        #  FCL
        self.detalle_movimiento_ids = [(0,0,{
            'name' : 'FCL',
            'display_type' : 'line_section',
        }),(0,0,{
            'name' : 'Compra',
            'valor' : self.cliente.compra_fcl
        }),(0,0,{
            'name' : 'Retiro',
            'valor' : self.cliente.retiro_fcl
        }),(0,0,{
            'name' : 'Adicion',
            'valor' : self.cliente.adicion_fcl
        }),(0,0,{
            'name' : 'A. de Recuado',
            'valor' : self.cliente.aplicacion_recaudo_fcl
        }),]
        #  CSF
        self.detalle_movimiento_ids = [(0,0,{
            'name' : 'CSF',
            'display_type' : 'line_section',
        }),(0,0,{
            'name' : 'Compra',
            'valor' : self.cliente.compra_csf
        }),(0,0,{
            'name' : 'Retiro',
            'valor' : self.cliente.retiro_csf
        }),(0,0,{
            'name' : 'Adicion',
            'valor' : self.cliente.adicion_csf
        }),(0,0,{
            'name' : 'A. de Recuado',
            'valor' : self.cliente.aplicacion_recaudo_csf
        }),]

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
        self._generar_resumen_movimientos()
        
            
        # TITULOS
        titulos_cliente = self.env['ati.titulo'].search([('client.id','=',self.cliente.id)])
        self.detalle_titulos_ids = False
        for titulos in titulos_cliente:
            self.env['ati.extracto.detalle_titulos'].create({
                'extracto_id' : self.id,
                'titulo' : titulos.id
            })

        # INVERSIONES
        self._generar_resumen_inversion()

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

class ResumenInversionesFCL(models.Model):
    _name = 'ati.extracto.resumen_inversion'

    def _compute_name(self):
        for rec in self:
            if rec.display_type and not rec.is_total:
                rec.name = rec.gestor.name
            elif rec.is_total:
                rec.name = 'TOTAL'
            else:
                rec.name = rec.producto.name

    extracto_id = fields.Many2one('ati.extracto','Extracto')
    producto = fields.Many2one('ati.investment.type','Tipo de inversion')
    name = fields.Char('Nombre', compute="_compute_name")
    valor_actual = fields.Float('Valor Actual')
    valor_anterior = fields.Float('Valor Anterior')
    diferencia = fields.Float('Variacion')
    rendimiento_causado = fields.Float('Rendimiento Causado')
    participacion = fields.Float('Participación')
    tasa_rendimiento = fields.Float('Tasa Rendimiento')
    gestor = fields.Many2one('ati.gestor', 'Gestor')
    display_type = fields.Selection([
       ('line_section', "Section"),
       ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    cant_movimientos = fields.Integer('Cantidad de movimientos')
    is_total = fields.Boolean('Linea de TOTAL', default=False)

class DetalleMovimiento(models.Model):
    _name = 'ati.extracto.detalle_movimiento'

    extracto_id = fields.Many2one('ati.extracto','Extracto')
    name = fields.Char('Tipo')
    valor = fields.Float('Valor')
    display_type = fields.Selection([
       ('line_section', "Section"),
       ('line_note', "Note")], default=False, help="Technical field for UX purpose.")

class DetalleTitulos(models.Model):
    _name = 'ati.extracto.detalle_titulos'

    extracto_id = fields.Many2one('ati.extracto','Extracto')
    titulo = fields.Many2one('ati.titulo','Titulo')
    investment_type = fields.Char('Tipo',related="titulo.investment_type.name")
    issuing = fields.Many2one('res.partner','Emisor',related="titulo.issuing")
    payer = fields.Many2one('res.partner','Pagador',related="titulo.payer")
    value = fields.Float('Valor de portafolio',related="titulo.value")
    fee = fields.Float('Tasa',related="titulo.fee")