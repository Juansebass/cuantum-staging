 # -*- coding: utf-8 -*-

from email.policy import default
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64
import matplotlib.pyplot as plt
from datetime import datetime
import calendar
import logging
from io import BytesIO ## for Python 3


logger = logging.getLogger(__name__)

class Extracto(models.Model):
    _name = 'ati.extracto'
    _description = "Extracto"
    _inherit = ['portal.mixin', 'mail.thread','mail.activity.mixin']

    name = fields.Char('Nombre')
    company_id = fields.Many2one('res.company', string='Company',  default=lambda self: self.env.company)

    cliente = fields.Many2one('res.partner','Cliente',required=1)
    responsible = fields.Many2one('res.partner','Responsable')
    email_cliente = fields.Char('Email',related='cliente.email')
    month = fields.Char('Mes de Periodo',required=1)
    year = fields.Char('Año de Periodo',required=1)
    pie_composicion_portafolio = fields.Binary('Composicion Portafolio')
    pie_inversiones_fondo = fields.Binary('Inversiones por fondo')
    pie_rpr_fondo = fields.Binary('RPR por fondo')

    #Campos para resumen de inversiones
    resumen_inversion_ids = fields.One2many('ati.extracto.resumen_inversion','extracto_id','Resumen Inversiones Fideicomiso Cuantum Libranzas')

    detalle_movimiento_ids = fields.One2many('ati.extracto.detalle_movimiento','extracto_id','Detalle de Movimientos')

    detalle_titulos_ids = fields.One2many('ati.extracto.detalle_titulos','extracto_id','Detalle de Titulos')

    estado_portafolios_ids = fields.One2many('ati.extracto.estado_portafolios','extracto_id','Estados de Portafolios')

    state = fields.Selection(selection=[('draft','Borrador'),('processed','Procesado'),('validated','Validado'),('send','Enviado')],string='Estado',default='draft')


    # _compute_access_url _get_report_base_filename son utilizadas para generar el extracto desde el portal
    def _compute_access_url(self):
        super(Extracto, self)._compute_access_url()
        for order in self:
            order.access_url = '/my/extracto/%s' % (order.id)

    def _get_report_base_filename(self):
        self.ensure_one()
        return 'Extracto %s' % (self.name)

    def _get_value_before(self,producto,gestor,month,year,recurso_recompra=False):
        #Verificamos que el mes no se Enero, de lo contrario pasamos a diciembre del año anterior
        if month == '1':
            month = '12'
            year = str(int(year) - 1)
        else:
            if (int(month) - 1) > 9 :
                month = str(int(month) - 1)
            else:
                month = '0' + str(int(month) - 1)
        if recurso_recompra:
            value = self.env['ati.extracto.resumen_inversion'].search([('extracto_id.cliente.id','=',self.cliente.id),
                                                                    ('detalle','=',producto),
                                                                    ('extracto_id.month','=',month),
                                                                    ('extracto_id.year','=',year)
                                                                    ])
        else:
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
        #Seteamos fecha de inicio y fin para comparaciones de busquedas segun el periodo seleccionado del extracto
        fecha_inicio = datetime.strptime('01/' + str(self.month) +'/'+ str(self.year), '%d/%m/%Y')
        fecha_fin = datetime.strptime( str(calendar.monthrange(int(self.year), int(self.month))[1])+ '/' + str(self.month) +'/'+ str(self.year), '%d/%m/%Y')

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
                # Buscamos el rendimiento para el tipo de producto en el movimiento
                rendimiento = self.env['ati.rendimientos.administracion'].search([('buyer.id','=',self.cliente.id),('movement_type','=','RENDIMIENTO'),('investment_type','=',moviemiento.investment_type.id),('date','>=',fecha_inicio),('date','<=',fecha_fin)],limit=1)
                # Buscamos el valor de administracion para el tipo de producto en el movimiento
                administracion = self.env['ati.rendimientos.administracion'].search([('buyer.id','=',self.cliente.id),('movement_type','=','ADMINISTRACION'),('investment_type','=',moviemiento.investment_type.id),('date','>=',fecha_inicio),('date','<=',fecha_fin)],limit=1)

                # Recorremos las inversiones en FCL para consultar si el tipo de producto ya se cargo, en tal caso sumamos su vpn al producto ya cargado
                for i in _inversiones:
                    if i[2]['producto'] == moviemiento.investment_type.id:
                        _inversiones[index] = (0,0,{
                            'producto' : moviemiento.investment_type.id,
                            'valor_actual' : moviemiento.value + i[2]['valor_actual'],
                            'valor_anterior' : i[2]['valor_anterior'],
                            'rendimiento_causado' : rendimiento.value,
                            'administracion' : administracion.value,
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
                        'rendimiento_causado' : rendimiento.value,
                        'administracion' : administracion.value,
                        'tasa_rendimiento' : moviemiento.fee,
                        'gestor' : moviemiento.manager.id,
                        'cant_movimientos' : 1
                    }))
        #Promediamos las tasas de inversiones
        for n in range(len(_inversiones)):
            _inversiones[n][2].update({'tasa_rendimiento' : round((_inversiones[n][2]['tasa_rendimiento'] / _inversiones[n][2]['cant_movimientos']), 2)})
        #Agregamos total de Recursos en proceso de recompra
        _inversiones.append((0,0,{
                        'detalle': 'RPR FCL',
                        'valor_actual' : self.cliente.total_fcl,
                        'valor_anterior' : self._get_value_before('RPR FCL',False,self.month,self.year,True),
                        'is_other' : True
                    }))
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
                # Buscamos el rendimiento para el tipo de producto en el movimiento
                rendimiento = self.env['ati.rendimientos.administracion'].search([('buyer.id','=',self.cliente.id),('movement_type','=','RENDIMIENTO'),('investment_type','=',moviemiento.investment_type.id),('date','>=',fecha_inicio),('date','<=',fecha_fin)],limit=1)
                # Buscamos el valor de administracion para el tipo de producto en el movimiento
                administracion = self.env['ati.rendimientos.administracion'].search([('buyer.id','=',self.cliente.id),('movement_type','=','ADMINISTRACION'),('investment_type','=',moviemiento.investment_type.id),('date','>=',fecha_inicio),('date','<=',fecha_fin)],limit=1)

                # Recorremos las inversiones en FCP para consultar si el tipo de producto ya se cargo, en tal caso sumamos su vpn al producto ya cargado
                for i in _inversiones:
                    if i[2]['producto'] == moviemiento.investment_type.id:
                        _inversiones[index] = (0,0,{
                            'producto' : moviemiento.investment_type.id,
                            'valor_actual' : moviemiento.value + i[2]['valor_actual'],
                            'valor_anterior' : i[2]['valor_anterior'],
                            'rendimiento_causado' : rendimiento.value,
                            'administracion' : administracion.value,
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
                        'rendimiento_causado' : rendimiento.value,
                        'administracion' : administracion.value,
                        'tasa_rendimiento' : moviemiento.fee,
                        'gestor' : moviemiento.manager.id,
                        'cant_movimientos' : 1
                    }))
        #Promediamos las tasas de inversiones
        for n in range(len(_inversiones)):
            _inversiones[n][2].update({'tasa_rendimiento' : round((_inversiones[n][2]['tasa_rendimiento'] / _inversiones[n][2]['cant_movimientos']), 2)})
        #Agregamos total de Recursos en proceso de recompra
        _inversiones.append((0,0,{
                        'detalle': 'RPR STATUM',
                        'valor_actual' : self.cliente.total_fcp,
                        'valor_anterior' : self._get_value_before('RPR STATUM',False,self.month,self.year,True),
                        'is_other' : True
                    }))
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
                # Buscamos el rendimiento para el tipo de producto en el movimiento
                rendimiento = self.env['ati.rendimientos.administracion'].search([('buyer.id','=',self.cliente.id),('movement_type','=','RENDIMIENTO'),('investment_type','=',moviemiento.investment_type.id),('date','>=',fecha_inicio),('date','<=',fecha_fin)],limit=1)
                # Buscamos el valor de administracion para el tipo de producto en el movimiento
                administracion = self.env['ati.rendimientos.administracion'].search([('buyer.id','=',self.cliente.id),('movement_type','=','ADMINISTRACION'),('investment_type','=',moviemiento.investment_type.id),('date','>=',fecha_inicio),('date','<=',fecha_fin)],limit=1)

                # Recorremos las inversiones en CUANTUM para consultar si el tipo de producto ya se cargo, en tal caso sumamos su vpn al producto ya cargado
                for i in _inversiones:
                    if i[2]['producto'] == moviemiento.investment_type.id:
                        _inversiones[ind] = (0,0,{
                            'producto' : moviemiento.investment_type.id,
                            'valor_actual' : moviemiento.value + i[2]['valor_actual'],
                            'valor_anterior' : i[2]['valor_anterior'],
                            'rendimiento_causado' : rendimiento.value,
                            'administracion' : administracion.value,
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
                        'valor_anterior' :self._get_value_before(moviemiento.investment_type.id,moviemiento.manager.id,self.month,self.year),
                        'rendimiento_causado' : rendimiento.value,
                        'administracion' : administracion.value,
                        'tasa_rendimiento' : moviemiento.fee,
                        'gestor' : moviemiento.manager.id,
                        'cant_movimientos' : 1
                    }))
        #Promediamos las tasas de inversiones
        for n in range(len(_inversiones)):
            _inversiones[n][2].update({'tasa_rendimiento' : round((_inversiones[n][2]['tasa_rendimiento'] / _inversiones[n][2]['cant_movimientos']), 2)})
        #Agregamos total de Recursos en proceso de recompra
        _inversiones.append((0,0,{
                        'detalle': 'RPR CSF',
                        'valor_actual' : self.cliente.total_csf,
                        'valor_anterior' : self._get_value_before('RPR CSF',False,self.month,self.year,True),
                        'is_other' : True
                    }))
        #Calculamos diferencia 
        for n in range(len(_inversiones)):
            _inversiones[n][2].update({'diferencia' : round((_inversiones[n][2]['valor_actual'] - _inversiones[n][2]['valor_anterior']), 2)})

        
        self.resumen_inversion_ids = _inversiones
        
        #Calculamos totales
        total_valor_actual = 0
        total_valor_anterior = 0
        total_rendimiento_causado = 0
        total_administracion = 0
        total_tasa_rendimiento = 0
        cant_tasas = 0
        total_diferencia = 0

        logger.warning('***** resumen_inversion_ids: {0}'.format(self.resumen_inversion_ids))
        for ri in self.resumen_inversion_ids:
            logger.warning('***** valor: {0}'.format(ri.valor_actual))
            total_valor_actual += ri.valor_actual
            total_valor_anterior += ri.valor_anterior
            total_rendimiento_causado += ri.rendimiento_causado
            total_administracion += ri.administracion
            total_tasa_rendimiento += ri.tasa_rendimiento
            if ri.tasa_rendimiento > 0:
                cant_tasas += 1
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
            'administracion' : total_administracion,
            'tasa_rendimiento' : total_tasa_rendimiento / cant_tasas if cant_tasas != 0 else 0,
            'diferencia' : total_diferencia,
        })]

        #Luego de calcular los totales ya podemos calcular la participacion que lo hacemos en base a la ultima linea del resumen ya que es la que tiene los totales
        #self.resumen_inversion_ids[-1]
        for ri in self.resumen_inversion_ids:
            if ri.id != self.resumen_inversion_ids[-1].id and ri.display_type != 'line_section':# and not ri.is_other:
                ri.participacion = (ri.valor_actual * 100 ) / self.resumen_inversion_ids[-1].valor_actual
                #Sumamos la participacion total
                self.resumen_inversion_ids[-1].participacion += ri.participacion

    def _generar_resumen_movimientos(self):
        #Borramos los datos que puede haber en detalle_movimiento_ids
        for dm in self.detalle_movimiento_ids:
            dm.unlink()
        
        #Variable utilizada para comprar meses segun periodo de extracto
        date_tmp = (datetime.strptime('01/' + self.month + '/' + self.year , '%d/%m/%Y')).date()
        if self.month == '12':
            date_next_tmp = (datetime.strptime('01/' + '01/' + str(int(self.year) + 1) , '%d/%m/%Y')).date()
        else:
            date_next_tmp = (datetime.strptime('01/' + str(int(self.month) + 1) + '/' + self.year , '%d/%m/%Y')).date()


        #  FCP
        self.detalle_movimiento_ids = [(0,0,{ 'name' : 'STATUM', 'display_type' : 'line_section'})]
        compra_fcp = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_fcp_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'COMPRA'))
        if compra_fcp > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Compra', 'valor' : compra_fcp })]
        retiro_fcp = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_fcp_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'RETIRO'))
        if retiro_fcp > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Retiro', 'valor' : retiro_fcp })]
        adicion_fcp = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_fcp_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'APORTE'))
        if adicion_fcp > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Adicion', 'valor' : adicion_fcp })]
        aplicacion_recaudo_fcp = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_fcp_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'APORTE'))
        if aplicacion_recaudo_fcp > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'A. de Recuado', 'valor' : aplicacion_recaudo_fcp })]
        self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Total Statum', 'valor' : sum([adicion_fcp,aplicacion_recaudo_fcp]) - sum([compra_fcp,retiro_fcp]) }),]


        #  FCL
        self.detalle_movimiento_ids = [(0,0,{ 'name' : 'FCL', 'display_type' : 'line_section', })]
        for r in self.cliente.recursos_recompra_fcl_ids:
            logger.warning('******** test date: {0} - {1}'.format(r.date, r))
        compra_fcl = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_fcl_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'COMPRA'))
        if compra_fcl > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Compra', 'valor' : compra_fcl })]
        retiro_fcl = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_fcl_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'RETIRO'))
        if retiro_fcl > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Retiro', 'valor' : retiro_fcl })]
        adicion_fcl = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_fcl_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'APORTE'))
        if adicion_fcl > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Adicion', 'valor' : adicion_fcl })]
        aplicacion_recaudo_fcl = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_fcl_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'APLICACION'))
        if aplicacion_recaudo_fcl > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'A. de Recuado', 'valor' : aplicacion_recaudo_fcl }),]
        self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Total FCL', 'valor' : sum([adicion_fcl,aplicacion_recaudo_fcl]) - sum([compra_fcl,retiro_fcl]) }),]


        #  CSF
        # -- TOTALES
        self.detalle_movimiento_ids = [(0,0,{ 'name' : 'CSF', 'display_type' : 'line_section', }), (0,0,{ 'name' : '-- TOTALES CSF', 'display_type' : 'line_section', })]
        adicion_total_csf = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_csf_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'APORTE'))
        if adicion_total_csf > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Total Adición', 'valor' : adicion_total_csf })]
        retiro_total_csf = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_csf_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'RETIRO'))
        if retiro_total_csf > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Total Retiro', 'valor' : retiro_total_csf })]
        self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Total', 'valor' : adicion_total_csf - retiro_total_csf })]
        # --FACTORING
        self.detalle_movimiento_ids = [(0,0,{ 'name' : '-- Factoring', 'display_type' : 'line_section', })]
        compra_fac_csf = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_csf_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'COMPRA' and x.investment_type.code == 'FAC'))
        if compra_fac_csf > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Compra', 'valor' : compra_fac_csf })]
        aplicacion_fac_recaudo_csf = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_csf_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'APLICACION' and x.investment_type.code == 'FAC'))
        if aplicacion_fac_recaudo_csf > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'A. de Recuado', 'valor' : aplicacion_fac_recaudo_csf })]
        self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Total Factoring CSF', 'valor' :  aplicacion_fac_recaudo_csf - compra_fac_csf}),]

        # --LIBRANZAS
        self.detalle_movimiento_ids = [(0,0,{ 'name' : '-- Libranzas', 'display_type' : 'line_section', })]
        compra_lib_csf = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_csf_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'COMPRA' and x.investment_type.code == 'LIB'))
        if compra_lib_csf > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Compra', 'valor' : compra_lib_csf })]
        aplicacion_lib_recaudo_csf = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_csf_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'APLICACION' and x.investment_type.code == 'LIB'))
        if aplicacion_lib_recaudo_csf > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'A. de Recuado', 'valor' : aplicacion_lib_recaudo_csf })]
        self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Total Libranzas CSF', 'valor' : aplicacion_lib_recaudo_csf - compra_lib_csf }),]

        # --SENTENCIAS
        self.detalle_movimiento_ids = [(0,0,{ 'name' : '-- Sentencias', 'display_type' : 'line_section', })]
        compra_sen_csf = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_csf_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'COMPRA' and x.investment_type.code == 'SEN'))
        if compra_sen_csf > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Compra', 'valor' : compra_sen_csf })]
        aplicacion_sen_recaudo_csf = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_csf_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'APLICACION' and x.investment_type.code == 'SEN'))
        if aplicacion_sen_recaudo_csf > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'A. de Recuado', 'valor' : aplicacion_sen_recaudo_csf })]
        self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Total Sentencias CSF', 'valor' : aplicacion_sen_recaudo_csf - compra_sen_csf }),]

        # --MUTUOS
        self.detalle_movimiento_ids = [(0,0,{ 'name' : '-- Mutuos', 'display_type' : 'line_section', })]
        compra_mut_csf = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_csf_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'COMPRA' and x.investment_type.code == 'MUT'))
        if compra_mut_csf > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Compra', 'valor' : compra_mut_csf })]
        aplicacion_mut_recaudo_csf = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_csf_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'APLICACION' and x.investment_type.code == 'MUT'))
        if aplicacion_mut_recaudo_csf > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'A. de Recuado', 'valor' : aplicacion_mut_recaudo_csf})]
        self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Total Mutuos CSF', 'valor' : aplicacion_sen_recaudo_csf - compra_sen_csf }),]
    
    def _generar_estados_portafolios(self):
        #Borramos los datos que puede haber en estado_portafolios_ids
        for dm in self.estado_portafolios_ids:
            dm.unlink()

        #  CSF
        self.estado_portafolios_ids = [(0,0,{ 'name' : 'Cuantum', 'display_type' : 'line_section', })]
        
        for investment_type in ['FAC','SEN','LIB','MUT']:
            total_valor_csf = 1
            if investment_type == 'FAC':
                self.estado_portafolios_ids = [(0,0,{ 'name' : '-- Factoring', 'display_type' : 'line_section', })]
                total_valor_csf = sum(ladicion['value'] for ladicion in self.detalle_titulos_ids.filtered(lambda x: x.titulo.manager.code == 'CUANTUM' and x.titulo.investment_type.code == 'FAC'))
            elif investment_type == 'SEN':
                self.estado_portafolios_ids = [(0,0,{ 'name' : '-- Sentencias', 'display_type' : 'line_section', })]
                total_valor_csf = sum(ladicion['value'] for ladicion in self.detalle_titulos_ids.filtered(lambda x: x.titulo.manager.code == 'CUANTUM' and x.titulo.investment_type.code == 'SEN'))
            elif investment_type == 'LIB':
                self.estado_portafolios_ids = [(0,0,{ 'name' : '-- Libranzas', 'display_type' : 'line_section', })]
                total_valor_csf = sum(ladicion['value'] for ladicion in self.detalle_titulos_ids.filtered(lambda x: x.titulo.manager.code == 'CUANTUM' and x.titulo.investment_type.code == 'LIB'))
            elif investment_type == 'MUT':
                self.estado_portafolios_ids = [(0,0,{ 'name' : '-- Mutuos', 'display_type' : 'line_section', })]
                total_valor_csf = sum(ladicion['value'] for ladicion in self.detalle_titulos_ids.filtered(lambda x: x.titulo.manager.code == 'CUANTUM' and x.titulo.investment_type.code == 'MUT'))
            for state_titulo in ['FALLE','MORA','NP','O','M1,M2,M2+,APP,T','VI']:
                titulos = self.detalle_titulos_ids.filtered(lambda x: x.titulo.manager.code == 'CUANTUM' and x.titulo.investment_type.code== investment_type and x.titulo.state_titulo.code == state_titulo)
                valor = 0
                porcentaje = 0
                estado = ''
                for cf in titulos:
                    estado = cf.titulo.state_titulo.name
                    valor += cf.titulo.value
                if valor > 0:
                    porcentaje = (valor * 100) / total_valor_csf
                    self.estado_portafolios_ids = [(0,0,{ 'name' : estado, 'valor' : valor, 'porcentaje' : porcentaje })]
        

        #  FCP
        self.estado_portafolios_ids = [(0,0,{ 'name' : 'STATUM', 'display_type' : 'line_section', })]
        total_valor_fcp = sum(ladicion['value'] for ladicion in self.detalle_titulos_ids.filtered(lambda x: x.titulo.manager.code == 'FCP'))
        for state_titulo in ['FALLE','MORA','NP','O','M1,M2,M2+,APP,T','VI']:
            titulos = self.detalle_titulos_ids.filtered(lambda x: x.titulo.manager.code == 'FCP' and x.titulo.state_titulo.code == state_titulo)
            valor = 0
            porcentaje = 0
            estado = ''
            for cf in titulos:
                estado = cf.titulo.state_titulo.name
                valor += cf.titulo.value
            if valor > 0:
                porcentaje = (valor * 100) / total_valor_fcp
                self.estado_portafolios_ids = [(0,0,{ 'name' : estado, 'valor' : valor, 'porcentaje' : porcentaje })]
        

        #  FCL
        self.estado_portafolios_ids = [(0,0,{ 'name' : 'FCL', 'display_type' : 'line_section', })]
        total_valor_fcl = sum(ladicion['value'] for ladicion in self.detalle_titulos_ids.filtered(lambda x: x.titulo.manager.code == 'FCL'))
        for state_titulo in ['FALLE','MORA','NP','O','M1,M2,M2+,APP,T','VI']:
            titulos = self.detalle_titulos_ids.filtered(lambda x: x.titulo.manager.code == 'FCL' and x.titulo.state_titulo.code == state_titulo)
            valor = 0
            porcentaje = 0
            estado = ''
            for cf in titulos:
                estado = cf.titulo.state_titulo.name
                valor += cf.titulo.value
            if valor > 0:
                porcentaje = (valor * 100) / total_valor_fcl
                self.estado_portafolios_ids = [(0,0,{ 'name' : estado, 'valor' : valor, 'porcentaje' : porcentaje })]

    def _generar_pie(self):
        colors = ['yellowgreen', 'gold', 'lightskyblue', 'lightcoral', 'purple']

        #Inversion por fondo

        total_cuantum = sum(value['valor_actual'] for value in self.resumen_inversion_ids.filtered(lambda x: x.gestor.code == 'CUANTUM'))
        total_FCL = sum(value['valor_actual'] for value in self.resumen_inversion_ids.filtered(lambda x: x.gestor.code == 'FCL'))
        total_FCP = sum(value['valor_actual'] for value in self.resumen_inversion_ids.filtered(lambda x: x.gestor.code == 'FCP'))
        
        #Validaciones mayores a 0
        if total_cuantum < 0:
            total_cuantum = 0.0
        if total_FCL < 0:
            total_FCL = 0.0
        if total_FCP < 0:
            total_FCP = 0.0

        if total_cuantum != 0.0 or total_FCL != 0.0 or total_FCP != 0.0:
            plt.pie([total_cuantum, total_FCL, total_FCP], colors=colors, autopct='%1.1f%%', shadow=False, startangle=90, labeldistance=0.1)
            plt.axis('equal')
            plt.legend(labels=['Cuantum', 'FCL', 'STATUM'])
            pic_data = BytesIO()
            plt.savefig(pic_data, bbox_inches='tight')
            self.write({'pie_inversiones_fondo': base64.encodestring(pic_data.getvalue())})
            plt.close()

        #Recursos en proceso de recompra por fondo

        rpr_cuantum = self.resumen_inversion_ids.filtered(lambda x:  x.detalle == 'RPR CSF').valor_actual
        rpr_FCL = self.resumen_inversion_ids.filtered(lambda x:  x.detalle == 'RPR FCL').valor_actual
        rpr_FCP = self.resumen_inversion_ids.filtered(lambda x:  x.detalle == 'RPR STATUM').valor_actual
        
        #Validaciones mayores a 0
        if rpr_cuantum < 0:
            rpr_cuantum = 0.0
        if rpr_FCL < 0:
            rpr_FCL = 0.0
        if rpr_FCP < 0:
            rpr_FCP = 0.0

        if rpr_cuantum != 0.0 or rpr_FCL != 0.0 or rpr_FCP != 0.0:
            plt.pie([rpr_cuantum, rpr_FCL, rpr_FCP], colors=colors, autopct='%1.1f%%', shadow=False, startangle=90, labeldistance=0.1)
            plt.axis('equal')
            plt.legend(labels=['Cuantum', 'FCL', 'STATUM'])
            pic_data = BytesIO()
            plt.savefig(pic_data, bbox_inches='tight')
            self.write({'pie_rpr_fondo': base64.encodestring(pic_data.getvalue())})
            plt.close()

        #Composicion del Portafolio
        total_factoring = sum(value['valor_actual'] for value in self.resumen_inversion_ids.filtered(lambda x: x.producto.code == 'FAC'))
        total_libranzas = sum(value['valor_actual'] for value in self.resumen_inversion_ids.filtered(lambda x: x.producto.code == 'LIB'))
        total_mutuos = sum(value['valor_actual'] for value in self.resumen_inversion_ids.filtered(lambda x: x.producto.code == 'MUT'))
        total_sentencias = sum(value['valor_actual'] for value in self.resumen_inversion_ids.filtered(lambda x: x.producto.code == 'SEN'))
        total_rpr = sum(value['valor_actual'] for value in self.resumen_inversion_ids.filtered(lambda x:  x.is_other))
        #Validaciones mayores a 0
        if total_rpr < 0:
            total_rpr = 0.0
        if total_factoring < 0:
            total_factoring = 0.0
        if total_libranzas < 0:
            total_libranzas = 0.0
        if total_mutuos < 0:
            total_mutuos = 0.0
        if total_sentencias < 0:
            total_sentencias = 0.0

        if total_factoring != 0.0 or total_libranzas != 0.0 or total_mutuos != 0.0 or total_sentencias != 0.0 or total_rpr != 0.0:
            plt.pie([total_factoring, total_libranzas, total_mutuos, total_sentencias, total_rpr], colors=colors, autopct='%1.1f%%', shadow=False, startangle=90, labeldistance=0.1)
            plt.axis('equal')
            plt.legend(labels=['Factoring', 'Libranzas', 'Mutuos', 'Sentencias', 'RPR'])
            pic_data = BytesIO()
            plt.savefig(pic_data, bbox_inches='tight')
            self.write({'pie_composicion_portafolio': base64.encodestring(pic_data.getvalue())})
            plt.close()


        
        return


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
        self._generar_estados_portafolios()

        # INVERSIONES
        self._generar_resumen_inversion()

        #Asignamos responsable
        self.responsible = self.env.user.partner_id

        #Creamos Pie
        self._generar_pie()

        #Cambiamos estado
        self.state = 'processed'


    def validar_extracto(self):
        for rec in self:
            if rec.state == 'processed':
                rec.state = 'validated'
            else:
                raise ValidationError('El extracto debe estar en estado procesado para poder ser validado')

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError('Los extracto debe estar en borrador para poder ser eliminados')
        return super(Extracto, self).unlink()


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
        if self.state not in ['validated','send']:
            raise ValidationError('El extracto debe estar validado para poder ser enviado')


        template_id = self.env.ref('ati_extractos.email_template_extracto').id
        compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
        ctx = {
            'default_model': 'ati.extracto',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            'partner_ids': self.cliente.id
        }

        self.state = 'send'

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }


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
            if rec.display_type and not rec.is_total and not rec.is_other:
                rec.name = rec.gestor.name
            elif rec.is_total:
                rec.name = 'TOTAL'
            elif rec.is_other:
                rec.name = rec.detalle
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
    administracion = fields.Float('Administracion')
    gestor = fields.Many2one('ati.gestor', 'Gestor')
    display_type = fields.Selection([
       ('line_section', "Section"),
       ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    cant_movimientos = fields.Integer('Cantidad de movimientos')
    is_total = fields.Boolean('Linea de TOTAL', default=False)
    is_other = fields.Boolean('Linea de detalle', default=False)
    detalle = fields.Char('Detalle')

class EstadoPortafolios(models.Model):
    _name = 'ati.extracto.estado_portafolios'

    extracto_id = fields.Many2one('ati.extracto','Extracto')
    name = fields.Char('Tipo')
    valor = fields.Float('Valor')
    porcentaje = fields.Float('Porcentaje')
    display_type = fields.Selection([
       ('line_section', "Section"),
       ('line_note', "Note")], default=False, help="Technical field for UX purpose.")

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