 # -*- coding: utf-8 -*-

from email.policy import default
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import calendar
import logging
from io import BytesIO ## for Python 3
from dateutil.relativedelta import relativedelta
import scipy.optimize as opt


logger = logging.getLogger(__name__)

class Extracto(models.Model):
    _name = 'ati.extracto'
    _description = "Extracto"
    _inherit = ['portal.mixin', 'mail.thread','mail.activity.mixin']

    name = fields.Char('Nombre')
    company_id = fields.Many2one('res.company', string='Company',  default=lambda self: self.env.company)

    #para recursos
    valor_anterior_recursos_csf = fields.Float('Valor Anterior')
    valor_actual_recursos_csf = fields.Float('Valor Actual')

    valor_anterior_recursos_fcl = fields.Float('Valor Anterior')
    valor_actual_recursos_fcl = fields.Float('Valor Actual')
    tir_ids = fields.One2many('ati.tir', 'extracto_id', 'TIR')
    tir_gestor_ids = fields.One2many('ati.tir.gestor', 'extracto_id', 'TIR Gestor')
    recursos_csf = fields.One2many('ati.extracto.recompra.csf', 'extracto_id', 'Recuros de recompra CSF')
    recursos_fcl = fields.One2many('ati.extracto.recompra.fcl', 'extracto_id', 'Recuros de recompra FCL')
    recursos_fcp = fields.One2many('ati.extracto.recompra.fcp', 'extracto_id', 'Recuros de recompra FCP')
    valor_anterior_recursos_fcp = fields.Float('Valor Anterior')
    valor_actual_recursos_fcp = fields.Float('Valor Actual')

    total_cuantum = fields.Float('Valor Total')
    total_FCL = fields.Float('Valor Total')
    total_FCP = fields.Float('Valor Total')
    show_alert = fields.Boolean('Alerta')

    cliente = fields.Many2one('res.partner','Cliente',required=1)
    responsible = fields.Many2one('res.partner','Responsable')
    email_cliente = fields.Char('Email',related='cliente.email')
    month = fields.Char('Mes de Periodo',required=1)
    year = fields.Char('Año de Periodo',required=1)
    pie_composicion_portafolio = fields.Binary('Composicion Portafolio')
    pie_inversiones_fondo = fields.Binary('Inversiones por fondo')
    pie_rpr_fondo = fields.Binary('RPR por fondo')

    show_alert_validation = fields.Boolean('Alerta')
    show_alert_product_validation = fields.Boolean('Alerta')
    message_product_validation = fields.Char()

    #Campos para resumen de inversiones
    resumen_inversion_ids = fields.One2many('ati.extracto.resumen_inversion','extracto_id','Resumen Inversiones Fideicomiso Cuantum Libranzas')

    detalle_movimiento_ids = fields.One2many('ati.extracto.detalle_movimiento','extracto_id','Detalle de Movimientos')

    detalle_titulos_ids = fields.One2many('ati.extracto.detalle_titulos','extracto_id','Detalle de Titulos')

    estado_portafolios_ids = fields.One2many('ati.extracto.estado_portafolios','extracto_id','Estados de Portafolios')

    state = fields.Selection(selection=[('draft','Borrador'),('processed','Procesado'),('validated','Validado'),('send','Enviado')],string='Estado',default='draft')

    valor_actual_total_resumen = fields.Float('Valor Total Actual Resumen')
    valor_anterior_total_resumen = fields.Float('Valor Total Anterior Resumen')
    valor_rendimiento_causado = fields.Float('Valor Total Rendimiento Causado')
    tir_mensual = fields.Float('TIR Mensual', digits=(3, 3))
    tir_trimestral = fields.Float('TIR Trimestral', digits=(3, 3))
    tir_semestral = fields.Float('TIR Semestral', digits=(3, 3))
    tir_anual = fields.Float('TIR Anual', digits=(3, 3))

    cuantum_fac_mensual = fields.Float('CUANTUM FAC Mensual', digits=(3, 3))
    cuantum_fac_trimestral = fields.Float('CUANTUM FAC Trimestral', digits=(3, 3))
    cuantum_fac_semestral = fields.Float('CUANTUM FAC Semestral', digits=(3, 3))
    cuantum_fac_anual = fields.Float('CUANTUM FAC Anual', digits=(3, 3))

    cuantum_lib_mensual = fields.Float('CUANTUM LIB Mensual', digits=(3, 3))
    cuantum_lib_trimestral = fields.Float('CUANTUM LIB Trimestral', digits=(3, 3))
    cuantum_lib_semestral = fields.Float('CUANTUM LIB Semestral', digits=(3, 3))
    cuantum_lib_anual = fields.Float('CUANTUM LIB Anual', digits=(3, 3))

    cuantum_mut_mensual = fields.Float('CUANTUM MUT Mensual', digits=(3, 3))
    cuantum_mut_trimestral = fields.Float('CUANTUM MUT Trimestral', digits=(3, 3))
    cuantum_mut_semestral = fields.Float('CUANTUM MUT Semestral', digits=(3, 3))
    cuantum_mut_anual = fields.Float('CUANTUM MUT Anual', digits=(3, 3))

    cuantum_sen_mensual = fields.Float('CUANTUM SEN Mensual', digits=(3, 3))
    cuantum_sen_trimestral = fields.Float('CUANTUM SEN Trimestral', digits=(3, 3))
    cuantum_sen_semestral = fields.Float('CUANTUM SEN Semestral', digits=(3, 3))
    cuantum_sen_anual = fields.Float('CUANTUM SEN Anual', digits=(3, 3))

    fcl_lib_mensual = fields.Float('FCL LIB Mensual', digits=(3, 3))
    fcl_lib_trimestral = fields.Float('FCL LIB Trimestral', digits=(3, 3))
    fcl_lib_semestral = fields.Float('FCL LIB Semestral', digits=(3, 3))
    fcl_lib_anual = fields.Float('FCL LIB Anual', digits=(3, 3))

    fcp_sen_mensual = fields.Float('FCP SEN Mensual', digits=(3, 3))
    fcp_sen_trimestral = fields.Float('FCP SEN Trimestral', digits=(3, 3))
    fcp_sen_semestral = fields.Float('FCP SEN Semestral', digits=(3, 3))
    fcp_sen_anual = fields.Float('FCP SEN Anual', digits=(3, 3))

    fcp_si_mensual = fields.Float('FCP SI Mensual', digits=(3, 3))
    fcp_si_trimestral = fields.Float('FCP SI Trimestral', digits=(3, 3))
    fcp_si_semestral = fields.Float('FCP SI Semestral', digits=(3, 3))
    fcp_si_anual = fields.Float('FCP SI Anual', digits=(3, 3))

    fcp_sii_mensual = fields.Float('FCP SII Mensual', digits=(3, 3))
    fcp_sii_trimestral = fields.Float('FCP SII Trimestral', digits=(3, 3))
    fcp_sii_semestral = fields.Float('FCP SII Semestral', digits=(3, 3))
    fcp_sii_anual = fields.Float('FCP SII Anual', digits=(3, 3))


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
        if month == '01':
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

    def _valor_actual_rpr(self, gestor):
        """
        gestor:str:CSF, FCL, FCP
        Retorna el valor actual del rpr sumando y restando el histórico dle modulo contactos
        """
        valor_actual = 0
        ultimo_dia = calendar.monthrange(int(self.year), int(self.month))[1]
        fecha_actual = datetime(int(self.year), int(self.month), ultimo_dia).date()

        if gestor == 'CSF':
            _temp_recursos = self.cliente.recursos_recompra_csf_ids.filtered(
                lambda x: x.date <= fecha_actual
            )
            for recurso in _temp_recursos:
                if recurso.movement_type.name in ['Adición', 'Aplicación de recaudo', 'Rendimiento']:
                    valor_actual += recurso.value
                else:
                    valor_actual -= recurso.value
        elif gestor == 'FCL':
            _temp_recursos = self.cliente.recursos_recompra_fcl_ids.filtered(
                lambda x: x.date <= fecha_actual
            )
            for recurso in _temp_recursos:
                if recurso.movement_type.name in ['Adición', 'Aplicación de recaudo', 'Rendimiento']:
                    valor_actual += recurso.value
                else:
                    valor_actual -= recurso.value
        elif gestor == 'FCP':
            _temp_recursos = self.cliente.recursos_recompra_fcp_ids.filtered(
                lambda x: x.date <= fecha_actual and x.investment_type.code == 'SEN'
            )
            for recurso in _temp_recursos:
                if recurso.movement_type.name in ['Adición', 'Aplicación de recaudo', 'Rendimiento']:
                    valor_actual += recurso.value
                else:
                    valor_actual -= recurso.value
        return valor_actual

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
                rendimiento = self.env['ati.rendimientos.administracion'].search([('manager.code','=',moviemiento.manager.code),('buyer.id','=',self.cliente.id),('movement_type','=','RENDIMIENTO'),('investment_type','=',moviemiento.investment_type.id),('date','>=',fecha_inicio),('date','<=',fecha_fin)])
                valor_rendimiento_tmp = 0
                for r in rendimiento:
                    valor_rendimiento_tmp += r.value
                # Buscamos el valor de administracion para el tipo de producto en el movimiento
                administracion = self.env['ati.rendimientos.administracion'].search([('manager.code','=',moviemiento.manager.code),('buyer.id','=',self.cliente.id),('movement_type','=','ADMINISTRACION'),('investment_type','=',moviemiento.investment_type.id),('date','>=',fecha_inicio),('date','<=',fecha_fin)])
                valor_administracion_tmp = 0
                for a in administracion:
                    valor_administracion_tmp += a.value



                # Recorremos las inversiones en CUANTUM para consultar si el tipo de producto ya se cargo, en tal caso sumamos su vpn al producto ya cargado
                for i in _inversiones:
                    if i[2]['producto'] == moviemiento.investment_type.id:
                        _inversiones[ind] = (0,0,{
                            'producto' : moviemiento.investment_type.id,
                            'valor_actual' : moviemiento.value + i[2]['valor_actual'],
                            'valor_anterior' : i[2]['valor_anterior'],
                            'rendimiento_causado' : valor_rendimiento_tmp,
                            'administracion' : valor_administracion_tmp,
                            'tasa_rendimiento' : moviemiento.fee + i[2]['tasa_rendimiento'] if moviemiento.value != None else i[2]['tasa_rendimiento'], #Solamente promediamos los mayores a cero
                            'gestor' : moviemiento.manager.id,
                            'cant_movimientos' : 1 + i[2]['cant_movimientos'] if moviemiento.value != None else i[2]['cant_movimientos']
                        })
                        prod_cargado = True
                    ind += 1

                # Cargamos el producto a la lista de inversion si todavia no se cargo
                if not prod_cargado:
                    _inversiones.append((0,0,{
                        'producto' : moviemiento.investment_type.id,
                        'valor_actual' : moviemiento.value,
                        'valor_anterior' :self._get_value_before(moviemiento.investment_type.id,moviemiento.manager.id,self.month,self.year),
                        'rendimiento_causado' : valor_rendimiento_tmp,
                        'administracion' : valor_administracion_tmp,
                        'tasa_rendimiento' : moviemiento.fee, #Solamente promediamos los mayores a cero
                        'gestor' : moviemiento.manager.id,
                        'cant_movimientos' : 1 if moviemiento.value != None else 0
                    }))
        #Promediamos las tasas de inversiones
        for n in range(len(_inversiones)):
            _inversiones[n][2].update({'tasa_rendimiento' : round((_inversiones[n][2]['tasa_rendimiento'] / _inversiones[n][2]['cant_movimientos']), 2) if _inversiones[n][2]['cant_movimientos'] != 0 else 0})
        #Agregamos total de Recursos en proceso de recompra
        _administracion_rpr_csf = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_csf_ids.filtered(
            lambda x: x.date.month == int(self.month) and x.date.year == int(
                self.year) and x.movement_type.code == 'ADMINISTRACION'))
        _rendimient_rpr_csf = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_csf_ids.filtered(lambda x: x.date.month == int(self.month) and x.date.year == int(self.year) and x.movement_type.code == 'RENDIMIENTO'))
        _inversiones.append((0,0,{
                        'detalle': 'RPR CSF',
                        'valor_actual' : self._valor_actual_rpr('CSF'),
                        'valor_anterior' : self._get_value_before('RPR CSF',False,self.month,self.year,True),
                        'rendimiento_causado' : _rendimient_rpr_csf,
                        'tasa_rendimiento': self.cliente.tasa_rendimiento_csf,
                        'administracion': _administracion_rpr_csf,
                        'is_other' : True
                    }))
        #Calculamos diferencia 
        for n in range(len(_inversiones)):
            _inversiones[n][2].update({'diferencia' : round((_inversiones[n][2]['valor_actual'] - _inversiones[n][2]['valor_anterior']), 2)})


        self.resumen_inversion_ids = _inversiones

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
                rendimiento = self.env['ati.rendimientos.administracion'].search([('manager.code','=',moviemiento.manager.code),('buyer.id','=',self.cliente.id),('movement_type','=','RENDIMIENTO'),('investment_type','=',moviemiento.investment_type.id),('date','>=',fecha_inicio),('date','<=',fecha_fin)])
                valor_rendimiento_tmp = 0
                for r in rendimiento:
                    valor_rendimiento_tmp += r.value
                # Buscamos el valor de administracion para el tipo de producto en el movimiento
                administracion = self.env['ati.rendimientos.administracion'].search([('manager.code','=',moviemiento.manager.code),('buyer.id','=',self.cliente.id),('movement_type','=','ADMINISTRACION'),('investment_type','=',moviemiento.investment_type.id),('date','>=',fecha_inicio),('date','<=',fecha_fin)])
                valor_administracion_tmp = 0
                for a in administracion:
                    valor_administracion_tmp += a.value

                # Recorremos las inversiones en FCL para consultar si el tipo de producto ya se cargo, en tal caso sumamos su vpn al producto ya cargado
                for i in _inversiones:
                    if i[2]['producto'] == moviemiento.investment_type.id:
                        _inversiones[index] = (0,0,{
                            'producto' : moviemiento.investment_type.id,
                            'valor_actual' : moviemiento.value + i[2]['valor_actual'],
                            'valor_anterior' : i[2]['valor_anterior'],
                            'rendimiento_causado' : valor_rendimiento_tmp,
                            'administracion' : valor_administracion_tmp,
                            'tasa_rendimiento' : moviemiento.fee + i[2]['tasa_rendimiento'] if moviemiento.value != None else i[2]['tasa_rendimiento'], #Solamente promediamos los mayores a cero
                            'gestor' : moviemiento.manager.id,
                            'cant_movimientos' : 1 + i[2]['cant_movimientos'] if moviemiento.value != None else i[2]['cant_movimientos']
                        })
                        prod_cargado = True
                    index += 1

                # Cargamos el producto a la lista de inversion si todavia no se cargo
                if not prod_cargado:
                    _inversiones.append((0,0,{
                        'producto' : moviemiento.investment_type.id,
                        'valor_actual' : moviemiento.value,
                        'valor_anterior' : self._get_value_before(moviemiento.investment_type.id,moviemiento.manager.id,self.month,self.year),
                        'rendimiento_causado' : valor_rendimiento_tmp,
                        'administracion' : valor_administracion_tmp,
                        'tasa_rendimiento' : moviemiento.fee, #Solamente promediamos los mayores a cero
                        'gestor' : moviemiento.manager.id,
                        'cant_movimientos' : 1 if moviemiento.value != None else 0
                    }))
        #Promediamos las tasas de inversiones
        for n in range(len(_inversiones)):
            _inversiones[n][2].update({'tasa_rendimiento' : round((_inversiones[n][2]['tasa_rendimiento'] / _inversiones[n][2]['cant_movimientos']), 2) if _inversiones[n][2]['cant_movimientos'] != 0 else 0})
        #Agregamos total de Recursos en proceso de recompra
        _rendimient_rpr_fcl = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_fcl_ids.filtered(lambda x: x.date.month == int(self.month) and x.date.year == int(self.year) and x.movement_type.code == 'RENDIMIENTO'))
        _administracion_rpr_fcl = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_fcl_ids.filtered(
            lambda x: x.date.month == int(self.month) and x.date.year == int(
                self.year) and x.movement_type.code == 'ADMINISTRACION'))
        _inversiones.append((0,0,{
                        'detalle': 'RPR FCL',
                        'valor_actual' : self._valor_actual_rpr('FCL'),
                        'valor_anterior' : self._get_value_before('RPR FCL',False,self.month,self.year,True),
                        'rendimiento_causado' : _rendimient_rpr_fcl,
                        'administracion': _administracion_rpr_fcl,
                        'tasa_rendimiento': self.cliente.tasa_rendimiento_fcl,
                        'is_other' : True
                    }))
        #Calculamos diferencia
        for n in range(len(_inversiones)):
            _inversiones[n][2].update({'diferencia' : round((_inversiones[n][2]['valor_actual'] - _inversiones[n][2]['valor_anterior']), 2)})

        self.resumen_inversion_ids = _inversiones


        #######################
        #Statum
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
                rendimiento = self.env['ati.rendimientos.administracion'].search([('manager.code','=',moviemiento.manager.code),('buyer.id','=',self.cliente.id),('movement_type','=','RENDIMIENTO'),('investment_type','=',moviemiento.investment_type.id),('date','>=',fecha_inicio),('date','<=',fecha_fin)])
                valor_rendimiento_tmp = 0
                for r in rendimiento:
                    valor_rendimiento_tmp += r.value
                # Buscamos el valor de administracion para el tipo de producto en el movimiento
                administracion = self.env['ati.rendimientos.administracion'].search([('manager.code','=',moviemiento.manager.code),('buyer.id','=',self.cliente.id),('movement_type','=','ADMINISTRACION'),('investment_type','=',moviemiento.investment_type.id),('date','>=',fecha_inicio),('date','<=',fecha_fin)])
                valor_administracion_tmp = 0
                for a in administracion:
                    valor_administracion_tmp += a.value

                # Recorremos las inversiones en FCP para consultar si el tipo de producto ya se cargo, en tal caso sumamos su vpn al producto ya cargado
                for i in _inversiones:
                    if i[2]['producto'] == moviemiento.investment_type.id:
                        _inversiones[index] = (0,0,{
                            'producto' : moviemiento.investment_type.id,
                            'valor_actual' : moviemiento.value + i[2]['valor_actual'],
                            'valor_anterior' : i[2]['valor_anterior'],
                            'rendimiento_causado' : valor_rendimiento_tmp,
                            'administracion' : valor_administracion_tmp,
                            'tasa_rendimiento' : moviemiento.fee + i[2]['tasa_rendimiento'] if moviemiento.value != None else i[2]['tasa_rendimiento'], #Solamente promediamos los mayores a cero
                            'gestor' : moviemiento.manager.id,
                            'cant_movimientos' : 1 + i[2]['cant_movimientos'] if moviemiento.value != None else i[2]['cant_movimientos']
                        })
                        prod_cargado = True
                    index += 1

                # Cargamos el producto a la lista de inversion si todavia no se cargo
                if not prod_cargado:
                    _inversiones.append((0,0,{
                        'producto' : moviemiento.investment_type.id,
                        'valor_actual' : moviemiento.value,
                        'valor_anterior' : self._get_value_before(moviemiento.investment_type.id,moviemiento.manager.id,self.month,self.year),
                        'rendimiento_causado' : valor_rendimiento_tmp,
                        'administracion' : valor_administracion_tmp,
                        'tasa_rendimiento' : moviemiento.fee, #Solamente promediamos los mayores a cero
                        'gestor' : moviemiento.manager.id,
                        'cant_movimientos' : 1 if moviemiento.value != None else 0
                    }))
        #Promediamos las tasas de inversiones
        for n in range(len(_inversiones)):
            _inversiones[n][2].update({'tasa_rendimiento' : round((_inversiones[n][2]['tasa_rendimiento'] / _inversiones[n][2]['cant_movimientos']), 2) if _inversiones[n][2]['cant_movimientos'] != 0 else 0})
        #Agregamos total de Recursos en proceso de recompra
        _rendimient_rpr_fcp = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_fcp_ids.filtered(lambda x: x.date.month == int(self.month) and x.date.year == int(self.year) and x.movement_type.code == 'RENDIMIENTO'))
        _rendimient_rpr_fcp = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_fcp_ids.filtered(lambda x: x.date.month == int(self.month) and x.date.year == int(self.year) and x.movement_type.code == 'RENDIMIENTO' and x.investment_type.code == 'SEN'))
        _inversiones.append((0,0,{
                        'detalle': 'RPR STATUM',
                        'valor_actual' : self._valor_actual_rpr('FCP'),
                        'valor_anterior' : self._get_value_before('RPR STATUM',False,self.month,self.year,True),
                        'rendimiento_causado' : _rendimient_rpr_fcp,
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
        total_ponderacion = 0

        logger.warning('***** resumen_inversion_ids: {0}'.format(self.resumen_inversion_ids))
        for ri in self.resumen_inversion_ids:
            logger.warning('***** valor: {0}'.format(ri.valor_actual))
            total_valor_actual += ri.valor_actual
            total_valor_anterior += ri.valor_anterior
            total_rendimiento_causado += ri.rendimiento_causado
            total_administracion += ri.administracion
            total_tasa_rendimiento += ri.tasa_rendimiento
            total_ponderacion += ri.tasa_rendimiento * ri.participacion
            if ri.tasa_rendimiento > 0:
                cant_tasas += 1
            total_diferencia += ri.diferencia

        self.valor_anterior_total_resumen = total_valor_anterior
        self.valor_actual_total_resumen = total_valor_actual
        self.valor_rendimiento_causado = total_rendimiento_causado

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
            'tasa_rendimiento': 0,
            #'tasa_rendimiento' : total_tasa_rendimiento / cant_tasas if cant_tasas != 0 else 0,
            'diferencia' : total_diferencia,
        })]

        #Luego de calcular los totales ya podemos calcular la participacion que lo hacemos en base a la ultima linea del resumen ya que es la que tiene los totales
        #self.resumen_inversion_ids[-1]
        for ri in self.resumen_inversion_ids:
            if ri.id != self.resumen_inversion_ids[-1].id and ri.display_type != 'line_section':# and not ri.is_other:
                if self.resumen_inversion_ids[-1].valor_actual != 0:
                    ri.participacion = (ri.valor_actual * 100 ) / self.resumen_inversion_ids[-1].valor_actual
                else:
                    ri.participacion = 0
                total_ponderacion += ri.tasa_rendimiento * (ri.participacion / 100)
                #Sumamos la participacion total
                self.resumen_inversion_ids[-1].participacion += ri.participacion
        self.resumen_inversion_ids[-1].tasa_rendimiento += total_ponderacion

    def _generar_resumen_movimientos(self):
        ###Asignando recursos recompra
        _temp_recursos_csf = self.cliente.recursos_recompra_csf_ids.filtered(
            lambda x: x.date.month == int(self.month) and x.date.year == int(
                self.year)).sorted(key=lambda x: int(x.date.day))
        self.recursos_csf = [(2, x.id) for x in self.recursos_csf]
        self.recursos_csf = [
            (0, 0,
             {
                'name': x.name,
                'date': x.date,
                'value': x.value,
                'investment_type': x.investment_type.id,
                'movement_type': x.movement_type.id,
                'buyer': x.buyer.id,
                'extracto_id': self.id,
             }
             )
            for x in _temp_recursos_csf
        ]

        _temp_recursos_fcl = self.cliente.recursos_recompra_fcl_ids.filtered(
            lambda x: x.date.month == int(self.month) and x.date.year == int(
                self.year)).sorted(key=lambda x: int(x.date.day))
        self.recursos_fcl = [(2, x.id) for x in self.recursos_fcl]
        self.recursos_fcl = [
            (0, 0,
             {
                'name': x.name,
                'date': x.date,
                'value': x.value,
                'investment_type': x.investment_type.id,
                'movement_type': x.movement_type.id,
                'buyer': x.buyer.id,
                'extracto_id': self.id,
             }
             )
            for x in _temp_recursos_fcl
        ]

        _temp_recursos_fcp = self.cliente.recursos_recompra_fcp_ids.filtered(
            lambda x: x.date.month == int(self.month) and x.date.year == int(
                self.year) and x.investment_type.code == "SEN").sorted(key=lambda x: int(x.date.day))
        self.recursos_fcp = [(2, x.id) for x in self.recursos_fcp]
        self.recursos_fcp = [
            (0, 0,
             {
                'name': x.name,
                'date': x.date,
                'value': x.value,
                'investment_type': x.investment_type.id,
                'movement_type': x.movement_type.id,
                'buyer': x.buyer.id,
                'extracto_id': self.id,
             }
             )
            for x in _temp_recursos_fcp
        ]

        self.valor_anterior_recursos_csf = self._get_value_before('RPR CSF', False, self.month, self.year, True)
        self.valor_actual_recursos_csf = self.valor_anterior_recursos_csf

        for recurso in self.recursos_csf:
            if recurso.movement_type.name in ['Adición', 'Aplicación de recaudo', 'Rendimiento']:
                self.valor_actual_recursos_csf += recurso.value
            else:
                self.valor_actual_recursos_csf -= recurso.value

        self.valor_anterior_recursos_fcl = self._get_value_before('RPR FCL', False, self.month, self.year, True)
        self.valor_actual_recursos_fcl = self.valor_anterior_recursos_fcl
        for recurso in self.recursos_fcl:
            if recurso.movement_type.name in ['Adición', 'Aplicación de recaudo', 'Rendimiento']:
                self.valor_actual_recursos_fcl += recurso.value
            else:
                self.valor_actual_recursos_fcl -= recurso.value

        self.valor_anterior_recursos_fcp = self._get_value_before('RPR STATUM', False, self.month, self.year, True)
        self.valor_actual_recursos_fcp =  self.valor_anterior_recursos_fcp
        for recurso in self.recursos_fcp:
            if recurso.movement_type.name in ['Adición', 'Aplicación de recaudo', 'Rendimiento']:
                self.valor_actual_recursos_fcp += recurso.value
            else:
                self.valor_actual_recursos_fcp -= recurso.value


        #Poner cuidado en la validación
        self.total_cuantum = self.cliente.total_csf
        self.total_FCL = self.cliente.total_fcl
        self.total_FCP = self.cliente.total_fcp


        self.show_alert = True
        if (
                int(self.valor_actual_recursos_csf) == int(self._valor_actual_rpr('CSF')) and
                int(self.valor_actual_recursos_fcl) == int(self._valor_actual_rpr('FCL')) and
                int(self.valor_actual_recursos_fcp) == int(self._valor_actual_rpr('FCP'))
        ):
            self.show_alert = False


        #Borramos los datos que puede haber en detalle_movimiento_ids
        for dm in self.detalle_movimiento_ids:
            dm.unlink()
        
        #Variable utilizada para comprar meses segun periodo de extracto
        date_tmp = (datetime.strptime('01/' + self.month + '/' + self.year , '%d/%m/%Y')).date()
        if self.month == '12':
            date_next_tmp = (datetime.strptime('01/' + '01/' + str(int(self.year) + 1) , '%d/%m/%Y')).date()
        else:
            date_next_tmp = (datetime.strptime('01/' + str(int(self.month) + 1) + '/' + self.year , '%d/%m/%Y')).date()


        #  CSF
        # -- TOTALES
        self.detalle_movimiento_ids = [(0,0,{ 'name' : 'CSF', 'display_type' : 'line_section', }), (0,0,{ 'name' : '-- TOTALES CSF', 'display_type' : 'line_section', })]
        adicion_total_csf = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_csf_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'ADICION'))
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
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'A. de Recaudo', 'valor' : aplicacion_fac_recaudo_csf })]
        self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Total Factoring CSF', 'valor' :  aplicacion_fac_recaudo_csf - compra_fac_csf}),]

        # --LIBRANZAS
        self.detalle_movimiento_ids = [(0,0,{ 'name' : '-- Libranzas', 'display_type' : 'line_section', })]
        compra_lib_csf = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_csf_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'COMPRA' and x.investment_type.code == 'LIB'))
        if compra_lib_csf > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Compra', 'valor' : compra_lib_csf })]
        aplicacion_lib_recaudo_csf = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_csf_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'APLICACION' and x.investment_type.code == 'LIB'))
        if aplicacion_lib_recaudo_csf > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'A. de Recaudo', 'valor' : aplicacion_lib_recaudo_csf })]
        self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Total Libranzas CSF', 'valor' : aplicacion_lib_recaudo_csf - compra_lib_csf }),]

        # --SENTENCIAS
        self.detalle_movimiento_ids = [(0,0,{ 'name' : '-- Sentencias', 'display_type' : 'line_section', })]
        compra_sen_csf = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_csf_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'COMPRA' and x.investment_type.code == 'SEN'))
        if compra_sen_csf > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Compra', 'valor' : compra_sen_csf })]
        aplicacion_sen_recaudo_csf = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_csf_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'APLICACION' and x.investment_type.code == 'SEN'))
        if aplicacion_sen_recaudo_csf > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'A. de Recaudo', 'valor' : aplicacion_sen_recaudo_csf })]
        self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Total Sentencias CSF', 'valor' : aplicacion_sen_recaudo_csf - compra_sen_csf }),]

        # --MUTUOS
        self.detalle_movimiento_ids = [(0,0,{ 'name' : '-- Mutuos', 'display_type' : 'line_section', })]
        compra_mut_csf = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_csf_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'COMPRA' and x.investment_type.code == 'MUT'))
        if compra_mut_csf > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Compra', 'valor' : compra_mut_csf })]
        aplicacion_mut_recaudo_csf = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_csf_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'APLICACION' and x.investment_type.code == 'MUT'))
        if aplicacion_mut_recaudo_csf > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'A. de Recaudo', 'valor' : aplicacion_mut_recaudo_csf})]
        self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Total Mutuos CSF', 'valor' : aplicacion_mut_recaudo_csf - compra_mut_csf }),]

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
        adicion_fcl = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_fcl_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'ADICION'))
        if adicion_fcl > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Adicion', 'valor' : adicion_fcl })]
        aplicacion_recaudo_fcl = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_fcl_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'APLICACION'))
        if aplicacion_recaudo_fcl > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'A. de Recaudo', 'valor' : aplicacion_recaudo_fcl }),]
        self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Total FCL', 'valor' : sum([adicion_fcl,aplicacion_recaudo_fcl]) - sum([compra_fcl,retiro_fcl]) }),]

        #  FCP
        self.detalle_movimiento_ids = [(0,0,{ 'name' : 'STATUM', 'display_type' : 'line_section'})]
        compra_fcp = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_fcp_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'COMPRA'))
        if compra_fcp > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Compra', 'valor' : compra_fcp })]
        retiro_fcp = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_fcp_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'RETIRO'))
        if retiro_fcp > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Retiro', 'valor' : retiro_fcp })]
        adicion_fcp = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_fcp_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'ADICION'))
        if adicion_fcp > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Adicion', 'valor' : adicion_fcp })]
        aplicacion_recaudo_fcp = sum(ldm['value'] for ldm in self.cliente.recursos_recompra_fcp_ids.filtered(lambda x: x.date >= date_tmp and x.date < date_next_tmp and x.movement_type.code == 'ADICION'))
        if aplicacion_recaudo_fcp > 0: 
            self.detalle_movimiento_ids = [(0,0,{ 'name' : 'A. de Recaudo', 'valor' : aplicacion_recaudo_fcp })]
        self.detalle_movimiento_ids = [(0,0,{ 'name' : 'Total Statum', 'valor' : sum([adicion_fcp,aplicacion_recaudo_fcp]) - sum([compra_fcp,retiro_fcp]) }),]

    
    def _generar_estados_portafolios(self):
        #Borramos los datos que puede haber en estado_portafolios_ids
        for dm in self.estado_portafolios_ids:
            dm.unlink()

        #  CSF
        self.estado_portafolios_ids = [(0,0,{ 'name' : 'CSF', 'display_type' : 'line_section', })]
        
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
            for state_titulo in ['FALLE','MORA','NP','O','M1,M2,M2+,APP,T','VI','PAG','OV','MV','PO']:
                titulos = self.detalle_titulos_ids.filtered(lambda x: x.titulo.manager.code == 'CUANTUM' and x.titulo.investment_type.code== investment_type and x.titulo.state_titulo.code == state_titulo)
                valor = 0
                porcentaje = 0
                estado = ''
                for cf in titulos:
                    estado = cf.titulo.state_titulo.name
                    valor += cf.titulo.value
                    #Desglose de titulos por estado
                    #if cf.titulo.value > 0:
                    #    self.estado_portafolios_ids = [(0,0,{ 'name' : cf.titulo.name + ' - ' + estado, 'valor' : cf.titulo.value })]
                if valor > 0:
                    porcentaje = ((valor * 100) / total_valor_csf) if total_valor_csf != 0 else 0
                    self.estado_portafolios_ids = [(0,0,{ 'name' : estado.capitalize(), 'valor' : valor, 'porcentaje' : porcentaje })]
        

        #  FCL
        self.estado_portafolios_ids = [(0,0,{ 'name' : 'FCL', 'display_type' : 'line_section', })]
        total_valor_fcl = sum(ladicion['value'] for ladicion in self.detalle_titulos_ids.filtered(lambda x: x.titulo.manager.code == 'FCL'))
        for state_titulo in ['FALLE','MORA','NP','O','M1,M2,M2+,APP,T','VI','PAG','OV','MV','PO']:
            titulos = self.detalle_titulos_ids.filtered(lambda x: x.titulo.manager.code == 'FCL' and x.titulo.state_titulo.code == state_titulo)
            valor = 0
            porcentaje = 0
            estado = ''
            for cf in titulos:
                estado = cf.titulo.state_titulo.name
                valor += cf.titulo.value
                #Desglose de titulos por estado
                #if cf.titulo.value > 0:
                #    self.estado_portafolios_ids = [(0,0,{ 'name' : cf.titulo.name + ' - ' + estado, 'valor' : cf.titulo.value })]
            if valor > 0:
                porcentaje = (valor * 100) / total_valor_fcl
                self.estado_portafolios_ids = [(0,0,{ 'name' : estado.capitalize(), 'valor' : valor, 'porcentaje' : porcentaje })]

        #  FCP
        self.estado_portafolios_ids = [(0,0,{ 'name' : 'STATUM', 'display_type' : 'line_section', })]
        total_valor_fcp = sum(ladicion['value'] for ladicion in self.detalle_titulos_ids.filtered(lambda x: x.titulo.manager.code == 'FCP'))
        for state_titulo in ['FALLE','MORA','NP','O','M1,M2,M2+,APP,T','VI','PAG','OV','MV','PO']:
            titulos = self.detalle_titulos_ids.filtered(lambda x: x.titulo.manager.code == 'FCP' and x.titulo.state_titulo.code == state_titulo)
            valor = 0
            porcentaje = 0
            estado = ''
            for cf in titulos:
                estado = cf.titulo.state_titulo.name
                valor += cf.titulo.value
                #Desglose de titulos por estado
                #if cf.titulo.value > 0:
                #    self.estado_portafolios_ids = [(0,0,{ 'name' : cf.titulo.name + ' - ' + estado, 'valor' : cf.titulo.value })]
            if valor > 0:
                porcentaje = (valor * 100) / total_valor_fcp
                self.estado_portafolios_ids = [(0,0,{ 'name' : estado.capitalize(), 'valor' : valor, 'porcentaje' : porcentaje })]

    def _generar_pie(self):
        colors = ['green', 'grey', 'darkgreen', 'olive']

        #Inversion por fondo

        total_cuantum = sum(value['valor_actual'] for value in self.resumen_inversion_ids.filtered(lambda x: x.gestor.code == 'CUANTUM'))
        total_FCL = sum(value['valor_actual'] for value in self.resumen_inversion_ids.filtered(lambda x: x.gestor.code == 'FCL'))
        total_FCP = sum(value['valor_actual'] for value in self.resumen_inversion_ids.filtered(lambda x: x.gestor.code == 'FCP'))

        valores = []
        labels_valores = []
        
        #Validaciones mayores a 0
        if total_cuantum > 0:
            valores.append(total_cuantum)
            labels_valores.append('CUANTUM')
        if total_FCL > 0:
            valores.append(total_FCL)
            labels_valores.append('FCL')
        if total_FCP > 0:
            valores.append(total_FCP)
            labels_valores.append('STATUM')

        if len(valores):
            plt.pie(valores, colors=colors, autopct='%1.1f%%', shadow=False, startangle=90, labeldistance=0.1)
            plt.axis('equal')
            plt.legend(labels=labels_valores)
            pic_data = BytesIO()
            plt.savefig(pic_data, bbox_inches='tight')
            self.write({'pie_inversiones_fondo': base64.encodestring(pic_data.getvalue())})
            plt.close()

        #Recursos en proceso de recompra por fondo

        rpr_cuantum = self.resumen_inversion_ids.filtered(lambda x:  x.detalle == 'RPR CSF').valor_actual
        rpr_FCL = self.resumen_inversion_ids.filtered(lambda x:  x.detalle == 'RPR FCL').valor_actual
        rpr_FCP = self.resumen_inversion_ids.filtered(lambda x:  x.detalle == 'RPR STATUM').valor_actual

        valores = []
        labels_valores = []
        
        #Validaciones mayores a 0
        if rpr_cuantum > 0:
            valores.append(rpr_cuantum)
            labels_valores.append('CUANTUM')
        if rpr_FCL > 0:
            valores.append(rpr_FCL)
            labels_valores.append('FCL')
        if rpr_FCP > 0:
            valores.append(rpr_FCP)
            labels_valores.append('STATUM')

        if len(valores):
            plt.pie(valores, colors=colors, autopct='%1.1f%%', shadow=False, startangle=90, labeldistance=0.1)
            plt.axis('equal')
            plt.legend(labels=labels_valores)
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

        valores = []
        labels_valores = []

        #Validaciones mayores a 0
        if total_factoring > 0:
            valores.append(total_factoring)
            labels_valores.append('FACTORING')
        if total_libranzas > 0:
            valores.append(total_libranzas)
            labels_valores.append('LIBRANZAS')
        if total_mutuos > 0:
            valores.append(total_mutuos)
            labels_valores.append('MUTUOS')
        if total_sentencias > 0:
            valores.append(total_sentencias)
            labels_valores.append('SENTENCIAS')
            total_sentencias = 0.0
        if total_rpr > 0:
            valores.append(total_rpr)
            labels_valores.append('RPR')

        if len(valores):
            plt.pie(valores, colors=colors, autopct='%1.1f%%', shadow=False, startangle=90, labeldistance=0.1)
            plt.axis('equal')
            plt.legend(labels=labels_valores)
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
            #Validación de que se encuntre un informe  clientes creado para el periodo
            if not self.env['ctm.validacion'].search([('year','=',self.year),('month','=',self.month)]):
                raise ValidationError('No existe un Informe Clientes para el periodo seleccionado')
        else:
            raise ValidationError('Debe introducir un mes y año de periodo para este cargue')

        # MOVIMIENTOS
        self._generar_resumen_movimientos()
        
            
        # TITULOS
        titulos_cliente = self.env['ati.titulo'].search([('client.id','=',self.cliente.id)])
        self.detalle_titulos_ids = False
        for titulos in titulos_cliente:
            for titulo_mes in titulos.tit_historico_ids:
                if titulo_mes.periodo == self.month + '/' + self.year:
                    self.env['ati.extracto.detalle_titulos'].create({
                        'extracto_id' : self.id,
                        'titulo' : titulos.id,
                        'investment_type': titulo_mes.investment_type.id,
                        'issuing': titulo_mes.issuing.id,
                        'payer': titulo_mes.payer.id,
                        'sale_value': titulo_mes.sale_value,
                        'value': titulo_mes.value,
                        'fee': titulo_mes.fee,
                        'bonding_date': titulo_mes.bonding_date,
                        'redemption_date': titulo_mes.redemption_date,
                        'paid_value': titulo_mes.recaudo,
                        'state_titulo': titulo_mes.state_titulo.id,
                    })
        
        #si el titulo esta en esado pagado con valor pagado cero no lo incluimos
        for titulo in self.detalle_titulos_ids:
            if titulo.state_titulo.code == 'PAG' and titulo.paid_value == 0:
                titulo.unlink()

        self._generar_estados_portafolios()

        # INVERSIONES
        self._generar_resumen_inversion()

        #Asignamos responsable
        self.responsible = self.env.user.partner_id

        #Creamos Pie
        self._generar_pie()

        #Validacioón contra informes cllientes
        self.validacion_informes_clientes()

        #Validación Totales Factoring, libranzas sentencias
        self.validacion_totales()

        # try:
        #     self._generar_tir()
        # except Exception as e:
        #     raise ValidationError('No sepuede generar extracto {}'.format(self.name))

        if not (self.month == '01' and self.year== '2023'):
            self._generar_tir()
        #Cambiamos estado
        self.state = 'processed'


    def _add_record_tir(self, rec, gestor=None):
        if rec.movement_type.code == 'ADICION':
            self.env['ati.tir'].create({
                'extracto_id': self.id,
                'date': rec.date,
                'move': rec.value,
            })
        elif rec.movement_type.code == 'RETIRO':
            self.env['ati.tir'].create({
                'extracto_id': self.id,
                'date': rec.date,
                'move': rec.value * -1,
            })

        gestor = self.env['ati.gestor'].search([('code', '=', gestor)])
        #Agregando por Gestor
        if rec.movement_type.code == 'COMPRA':
            self.env['ati.tir.gestor'].create({
                'extracto_id': self.id,
                'date': rec.date,
                'move': rec.value,
                'gestor_id': gestor.id,
                'tipo_id': rec.investment_type.id,
            })
        elif rec.movement_type.code == 'APLICACION':
            self.env['ati.tir.gestor'].create({
                'extracto_id': self.id,
                'date': rec.date,
                'move': rec.value * -1,
                'gestor_id': gestor.id,
                'tipo_id': rec.investment_type.id,
            })

    def calculate_tir_function(self, cash_flows):
        dates = [cf[1] for cf in cash_flows]
        amounts = [cf[0] for cf in cash_flows]

        def npv(rate):
            # Start with the first date as the base
            base_date = dates[0]
            total_npv = 0

            if rate <= -1:
                return float('inf')  # Return a high value to indicate invalid IRR

            for i, date in enumerate(dates):
                # Calculate the time difference in days
                days_difference = (date - base_date).days

                # Discount factor
                discount_factor = (1 + rate) ** (days_difference / 365.0)

                # Contribution to NPV
                total_npv += amounts[i] / discount_factor

            return total_npv

        initial_guess = 0.1
        irr = opt.root_scalar(npv, bracket=[-0.99, 5], method='brentq').root
        return irr * 100
    
    def calulate_mutuos_cuantum(self, extractos_ids):
        values = []
        tir = 0
        for extracto in extractos_ids:
            line = extracto.resumen_inversion_ids.filtered(lambda x: x.gestor.code == 'CUANTUM' and x.producto.code == 'MUT')
            valor = line.valor_actual
            tasa =  line.tasa_rendimiento
            values.append((valor, tasa))
        total = sum([x[0] for x in values])
        if total > 0:
            for i in values:
                tir += (i[0] / total) * i[1]  
        return tir



    def calculate_tir_gestor(self):
        #CSF
        for tipo in ['FAC', 'LIB', 'SEN']:
            # Mensual
            cash_flows = [
                (line.move + line.valor, line.date) for line in self.tir_gestor_ids.filtered(
                    lambda x: x.gestor_id.code == 'CUANTUM' and x.tipo_id.code == tipo
                )
            ]
            logger.error('flows CSF MENSUAL')
            to_print = [(x[0], x[1].strftime('%Y-%m-%d')) for x in cash_flows]
            logger.error(tipo)
            logger.error(to_print)
            value = self.calculate_tir_function(cash_flows) if len(cash_flows) > 0 else 0
            if tipo == 'FAC':
                self.cuantum_fac_mensual = value
            elif tipo == 'LIB':
                self.cuantum_lib_mensual = value
            elif tipo == 'SEN':
                self.cuantum_sen_mensual = value

        #Para mutuos CUANTUM
        self.cuantum_mut_mensual = self.resumen_inversion_ids.filtered(lambda x: x.gestor.code == 'CUANTUM' and x.producto.code == 'MUT').tasa_rendimiento

        #FCL
        cash_flows = [
            (line.move + line.valor, line.date) for line in self.tir_gestor_ids.filtered(
                lambda x: x.gestor_id.code == 'FCL' and x.tipo_id.code == 'LIB'
            )
        ]
        logger.error('flows FCL MENSUAL')
        to_print = [(x[0], x[1].strftime('%Y-%m-%d')) for x in cash_flows]
        logger.error('Libranzas')
        logger.error(to_print)
        self.fcl_lib_mensual = self.calculate_tir_function(cash_flows) if len(cash_flows) > 0 else 0

        #FCP
        cash_flows = [
            (line.move + line.valor, line.date) for line in self.tir_gestor_ids.filtered(
                lambda x: x.gestor_id.code == 'FCP' and x.tipo_id.code == 'SEN'
            )
        ]
        
        self.fcp_sen_mensual = self.calculate_tir_function(cash_flows) if len(cash_flows) > 0 else 0

        cash_flows = [
            (line.move + line.valor, line.date) for line in self.tir_gestor_ids.filtered(
                lambda x: x.gestor_id.code == 'FCP' and x.tipo_id.code == 'S1'
            )
        ]
        self.fcp_si_mensual = self.calculate_tir_function(cash_flows) if len(cash_flows) > 0 else 0
        cash_flows = [
            (line.move + line.valor, line.date) for line in self.tir_gestor_ids.filtered(
                lambda x: x.gestor_id.code == 'FCP' and x.tipo_id.code == 'S2'
            )
        ]
        logger.error('flows FCP MENSUAL')
        to_print = [(x[0], x[1].strftime('%Y-%m-%d')) for x in cash_flows]
        logger.error('S2')
        logger.error(to_print)
        self.fcp_sii_mensual = self.calculate_tir_function(cash_flows) if len(cash_flows) > 0 else 0
        logger.error(self.fcp_sii_mensual)


        #TRIMESTRAL
        date = datetime(int(self.year), int(self.month), 1)
        past_extractos = self.env['ati.extracto']
        for i in range(0, 3):
            previous_date = date - relativedelta(months=i)
            past_extracto = self.env['ati.extracto'].search([
                ('cliente', '=', self.cliente.id),
                ('year', '=', str(previous_date.year)),
                ('month', '=', str(previous_date.month).zfill(2)),

            ], limit=1)
            past_extractos += past_extracto

        tir_gestor_ids = past_extractos.mapped('tir_gestor_ids')

        for tipo in ['FAC', 'LIB', 'SEN']:
            # Mensual
            cash_flows = [
                (line.move + line.valor, line.date) for line in tir_gestor_ids.filtered(
                    lambda x: x.gestor_id.code == 'CUANTUM' and x.tipo_id.code == tipo
                )
            ]
            if len(past_extractos) == 3:
                value = self.calculate_tir_function(cash_flows) if len(cash_flows) > 0 else 0
                if tipo == 'FAC':
                    tir_cuantum_fac_mensual_past_extracto = [x for x in past_extractos.mapped('cuantum_fac_mensual') if x != 0]
                    self.cuantum_fac_trimestral = value if len(tir_cuantum_fac_mensual_past_extracto) == 3 else 0
                elif tipo == 'LIB':
                    tir_cuantum_lib_mensual_past_extracto = [x for x in past_extractos.mapped('cuantum_lib_mensual') if x!= 0]
                    self.cuantum_lib_trimestral = value if len(tir_cuantum_lib_mensual_past_extracto) == 3 else 0
                elif tipo == 'SEN':
                    tir_cuantum_sen_mensual_past_extracto = [x for x in past_extractos.mapped('cuantum_sen_mensual') if x!= 0]
                    self.cuantum_sen_trimestral = value if len(tir_cuantum_sen_mensual_past_extracto) == 3 else 0
            else:
                self.cuantum_fac_trimestral = 0
                self.cuantum_lib_trimestral = 0
                self.cuantum_sen_trimestral = 0

        #Para mutuos CUANTUM
        self.cuantum_mut_trimestral = self.calulate_mutuos_cuantum(past_extractos)

        # FCL
        tir_si_mensual_past_extracto = [x for x in past_extractos.mapped('fcp_si_mensual') if x != 0]
        tir_sii_mensual_past_extracto =[x for x in past_extractos.mapped('fcp_sii_mensual') if x!= 0]
        tir_fcl_lib_mensual_past_extracto = [x for x in past_extractos.mapped('fcl_lib_mensual') if x!= 0]
        if len(past_extractos) == 3:
            if len(tir_fcl_lib_mensual_past_extracto) == 3:
                cash_flows = [
                    (line.move + line.valor, line.date) for line in tir_gestor_ids.filtered(
                        lambda x: x.gestor_id.code == 'FCL' and x.tipo_id.code == 'LIB'
                    )
                ]
                self.fcl_lib_trimestral = self.calculate_tir_function(cash_flows) if len(cash_flows) > 0 else 0

            # FCP
            cash_flows = [
                (line.move + line.valor, line.date) for line in tir_gestor_ids.filtered(
                    lambda x: x.gestor_id.code == 'FCP' and x.tipo_id.code == 'SEN'
                )
            ]
            self.fcp_sen_trimestral = self.calculate_tir_function(cash_flows) if len(cash_flows) > 0 else 0
            if len(tir_si_mensual_past_extracto) == 3:
                cash_flows = [
                    (line.move + line.valor, line.date) for line in tir_gestor_ids.filtered(
                        lambda x: x.gestor_id.code == 'FCP' and x.tipo_id.code == 'S1'
                    )
                ]
                self.fcp_si_trimestral = self.calculate_tir_function(cash_flows) if len(cash_flows) > 0 else 0
            if len(tir_sii_mensual_past_extracto) == 3:
                cash_flows = [
                    (line.move + line.valor, line.date) for line in tir_gestor_ids.filtered(
                        lambda x: x.gestor_id.code == 'FCP' and x.tipo_id.code == 'S2'
                    )
                ]
                self.fcp_sii_trimestral = self.calculate_tir_function(cash_flows) if len(cash_flows) > 0 else 0
        else:
            self.fcl_lib_trimestral = 0
            self.fcp_sen_trimestral = 0
            self.fcp_si_trimestral = 0
            self.fcp_sii_trimestral = 0

        #SEMESTRAL
        past_extractos = self.env['ati.extracto']
        for i in range(0, 6):
            previous_date = date - relativedelta(months=i)
            past_extracto = self.search([
                ('cliente', '=', self.cliente.id),
                ('month', '=', str(previous_date.month).zfill(2)),
                ('year', '=', str(previous_date.year)),
            ], limit=1)
            past_extractos += past_extracto

        tir_gestor_ids = past_extractos.mapped('tir_gestor_ids')

        for tipo in ['FAC', 'LIB', 'SEN']:
            # Mensual
            cash_flows = [
                (line.move + line.valor, line.date) for line in tir_gestor_ids.filtered(
                    lambda x: x.gestor_id.code == 'CUANTUM' and x.tipo_id.code == tipo
                )
            ]
            if len(past_extractos) == 6:
                value = self.calculate_tir_function(cash_flows) if len(cash_flows) > 0 else 0
                if tipo == 'FAC':
                    tir_cuantum_fac_mensual_past_extracto = [x for x in past_extractos.mapped('cuantum_fac_mensual') if x!= 0]
                    self.cuantum_fac_semestral = value if len(tir_cuantum_fac_mensual_past_extracto) == 6 else 0
                elif tipo == 'LIB':
                    tir_cuantum_lib_mensual_past_extracto = [x for x in past_extractos.mapped('cuantum_lib_mensual') if x!= 0]
                    self.cuantum_lib_semestral = value if len(tir_cuantum_lib_mensual_past_extracto) == 6 else 0
                elif tipo == 'SEN':
                    tir_cuantum_sen_mensual_past_extracto = [x for x in past_extractos.mapped('cuantum_sen_mensual') if x!= 0]
                    self.cuantum_sen_semestral = value if len(tir_cuantum_sen_mensual_past_extracto) == 6 else 0
            else:
                self.cuantum_fac_semestral = 0
                self.cuantum_lib_semestral = 0
                self.cuantum_sen_semestral = 0

        # Para mutuos CUANTUM
        self.cuantum_mut_semestral = self.calulate_mutuos_cuantum(past_extractos)

        # FCL
        tir_si_mensual_past_extracto = [x for x in past_extractos.mapped('fcp_si_mensual') if x != 0]
        tir_sii_mensual_past_extracto = [x for x in past_extractos.mapped('fcp_sii_mensual') if x != 0]
        tir_fcl_lib_mensual_past_extracto = [x for x in past_extractos.mapped('fcl_lib_mensual') if x!= 0]
        if len (past_extractos) == 6:
            if len(tir_fcl_lib_mensual_past_extracto) == 6:
                cash_flows = [
                    (line.move + line.valor, line.date) for line in tir_gestor_ids.filtered(
                        lambda x: x.gestor_id.code == 'FCL' and x.tipo_id.code == 'LIB'
                    )
                ]
                self.fcl_lib_semestral = self.calculate_tir_function(cash_flows) if len(cash_flows) > 0 else 0

            # FCP
            cash_flows = [
                (line.move + line.valor, line.date) for line in tir_gestor_ids.filtered(
                    lambda x: x.gestor_id.code == 'FCP' and x.tipo_id.code == 'SEN'
                )
            ]
            self.fcp_sen_semestral = self.calculate_tir_function(cash_flows) if len(cash_flows) > 0 else 0
            if len(tir_si_mensual_past_extracto) == 6:
                cash_flows = [
                    (line.move + line.valor, line.date) for line in tir_gestor_ids.filtered(
                        lambda x: x.gestor_id.code == 'FCP' and x.tipo_id.code == 'S1'
                    )
                ]
                self.fcp_si_semestral = self.calculate_tir_function(cash_flows) if len(cash_flows) > 0 else 0
            if len(tir_sii_mensual_past_extracto) == 6:
                cash_flows = [
                    (line.move + line.valor, line.date) for line in tir_gestor_ids.filtered(
                        lambda x: x.gestor_id.code == 'FCP' and x.tipo_id.code == 'S2'
                    )
                ]
                self.fcp_sii_semestral = self.calculate_tir_function(cash_flows) if len(cash_flows) > 0 else 0
        else:
            self.fcl_lib_semestral = 0
            self.fcp_sen_semestral = 0
            self.fcp_si_semestral = 0
            self.fcp_sii_semestral = 0

        #ANUAL
        past_extractos = self.env['ati.extracto']
        for i in range(0, 12):
            previous_date = date - relativedelta(months=i)
            past_extracto = self.search([
                ('cliente', '=', self.cliente.id),
                ('month', '=', str(previous_date.month).zfill(2)),
                ('year', '=', str(previous_date.year)),
            ], limit=1)
            past_extractos += past_extracto
        tir_gestor_ids = past_extractos.mapped('tir_gestor_ids')

        for tipo in ['FAC', 'LIB', 'SEN']:
            # Mensual
            cash_flows = [
                (line.move + line.valor, line.date) for line in tir_gestor_ids.filtered(
                    lambda x: x.gestor_id.code == 'CUANTUM' and x.tipo_id.code == tipo
                )
            ]
            if len(past_extractos) == 12:
                value = self.calculate_tir_function(cash_flows) if len(cash_flows) > 0 else 0
                if tipo == 'FAC':
                    tir_cuantum_fac_mensual_past_extracto = [x for x in past_extractos.mapped('cuantum_fac_mensual') if x!= 0]
                    self.cuantum_fac_anual = value if len(tir_cuantum_fac_mensual_past_extracto) == 12 else 0
                elif tipo == 'LIB':
                    tir_cuantum_lib_mensual_past_extracto = [x for x in past_extractos.mapped('cuantum_lib_mensual') if x!= 0]
                    self.cuantum_lib_anual = value if len(tir_cuantum_lib_mensual_past_extracto) == 12 else 0
                elif tipo == 'SEN':
                    tir_cuantum_sen_mensual_past_extracto = [x for x in past_extractos.mapped('cuantum_sen_mensual') if x!= 0]
                    self.cuantum_sen_anual = value if len(tir_cuantum_sen_mensual_past_extracto) == 12 else 0
            else:
                self.cuantum_fac_anual = 0
                self.cuantum_lib_anual = 0
                self.cuantum_sen_anual = 0
        
        # Para mutuos CUANTUM
        self.cuantum_mut_anual = self.calulate_mutuos_cuantum(past_extractos)

        # FCL
        tir_si_mensual_past_extracto = [x for x in past_extractos.mapped('fcp_si_mensual') if x!= 0]
        tir_sii_mensual_past_extracto = [x for x in past_extractos.mapped('fcp_sii_mensual') if x!= 0]
        tir_fcl_lib_mensual_past_extracto = [x for x in past_extractos.mapped('fcl_lib_mensual') if x!= 0]
        if len(past_extractos) == 12:
            if len(tir_fcl_lib_mensual_past_extracto) == 12:
                cash_flows = [
                    (line.move + line.valor, line.date) for line in tir_gestor_ids.filtered(
                        lambda x: x.gestor_id.code == 'FCL' and x.tipo_id.code == 'LIB'
                    )
                ]
                self.fcl_lib_anual = self.calculate_tir_function(cash_flows) if len(cash_flows) > 0 else 0

            # FCP
            cash_flows = [
                (line.move + line.valor, line.date) for line in tir_gestor_ids.filtered(
                    lambda x: x.gestor_id.code == 'FCP' and x.tipo_id.code == 'SEN'
                )
            ]
            self.fcp_sen_anual = self.calculate_tir_function(cash_flows) if len(cash_flows) > 0 else 0
            if len(tir_si_mensual_past_extracto) == 12:
                cash_flows = [
                    (line.move + line.valor, line.date) for line in tir_gestor_ids.filtered(
                        lambda x: x.gestor_id.code == 'FCP' and x.tipo_id.code == 'S1'
                    )
                ]
                self.fcp_si_anual = self.calculate_tir_function(cash_flows) if len(cash_flows) > 0 else 0
            if len(tir_sii_mensual_past_extracto) == 12:
                cash_flows = [
                    (line.move + line.valor, line.date) for line in tir_gestor_ids.filtered(
                        lambda x: x.gestor_id.code == 'FCP' and x.tipo_id.code == 'S2'
                    )
                ]
                self.fcp_sii_anual = self.calculate_tir_function(cash_flows) if len(cash_flows) > 0 else 0
        else:
            self.fcl_lib_anual = 0
            self.fcp_sen_anual = 0
            self.fcp_si_anual = 0
            self.fcp_sii_anual = 0


    def _generar_tir(self):
        for dm in self.tir_ids:
            dm.unlink()
        for dm in self.tir_gestor_ids :
            dm.unlink()
        range = calendar.monthrange(int(self.year), int(self.month))
        last_day = range[1]
        #Primer día
        #valor_anterior = self.valor_anterior_total_resumen if self.valor_anterior_total_resumen != 0 else self.valor_actual_total_resumen - self.valor_rendimiento_causado
        valor_anterior = self.valor_anterior_total_resumen
        past_extractos = self.env['ati.extracto'].search([('cliente', '=', self.cliente.id)])
        for resumen in self.resumen_inversion_ids:
            if resumen.gestor.code in ['FCP'] and resumen.valor_anterior == 0:
                valor_anterior += resumen.valor_actual - resumen.rendimiento_causado
        # if len(past_extractos) == 1:
        #     valor_anterior = self.valor_anterior_total_resumen if self.valor_anterior_total_resumen != 0 else self.valor_actual_total_resumen - self.valor_rendimiento_causado
        self.env['ati.tir'].create({
            'extracto_id': self.id,
            'date': datetime(int(self.year),int(self.month), 1) - timedelta(days=1),
            'valor': valor_anterior,
        })

        #Recorriendo detalle d emovimiento
        for rec in self.recursos_csf:
            self._add_record_tir(rec, 'CUANTUM')
        for rec in self.recursos_fcl:
            self._add_record_tir(rec, 'FCL')
        # for rec in self.recursos_fcp:
        #     self._add_record_tir(rec, 'FCP')
        
        recursos_si_sii = self.cliente.recursos_recompra_fcp_ids.filtered(
            lambda x: x.date.month == int(self.month) and x.date.year == int(
                self.year)).sorted(key=lambda x: int(x.date.day))

        for rec in recursos_si_sii:
            self._add_record_tir(rec, 'FCP')

       
        

        #último día
        self.env['ati.tir'].create({
            'extracto_id': self.id,
            'date': datetime(int(self.year),int(self.month), last_day).date(),
            'valor': self.valor_actual_total_resumen * -1,
        })

        #Generando Flujo de caja por gestor último y primer día
        for line in self.resumen_inversion_ids:
            if line.producto.code in ['FAC', 'LIB', 'SEN', 'S1', 'S2']:
                if line.producto.code in ['SEN', 'S1', 'S2'] and line.gestor.code == 'FCP':
                    valor_anterior = line.valor_anterior if line.valor_anterior != 0 else line.valor_actual - line.rendimiento_causado
                else:
                    valor_anterior = line.valor_anterior
                self.env['ati.tir.gestor'].create({
                    'extracto_id': self.id,
                    'date': datetime(int(self.year), int(self.month), 1) - timedelta(days=1),
                    'gestor_id': line.gestor.id,
                    'valor': valor_anterior,
                    'tipo_id': line.producto.id,
                })
                self.env['ati.tir.gestor'].create({
                    'extracto_id': self.id,
                    'date': datetime(int(self.year),int(self.month), last_day).date(),
                    'gestor_id': line.gestor.id,
                    'valor': line.valor_actual * -1,
                    'tipo_id': line.producto.id,
                })

        self.calculate_tir_gestor()


        #Calculando TIR
        cash_flows = [(x.move + x.valor, x.date) for x in self.tir_ids]
        logger.error('cash_flows')
        to_print = [(x[0], x[1].strftime('%Y-%m-%d')) for x in cash_flows]
        logger.error(to_print)

        dates = [cf[1] for cf in cash_flows]
        amounts = [cf[0] for cf in cash_flows]

        def npv(rate):
            # Start with the first date as the base
            base_date = dates[0]
            total_npv = 0

            if rate <= -1:
                return float('inf')  # Return a high value to indicate invalid IRR

            for i, date in enumerate(dates):
                # Calculate the time difference in days
                days_difference = (date - base_date).days

                # Discount factor
                discount_factor = (1 + rate) ** (days_difference / 365.0)

                # Contribution to NPV
                total_npv += amounts[i] / discount_factor

            return total_npv

        initial_guess = 0.1
        irr = opt.root_scalar(npv, bracket=[-0.99, 5], method='brentq').root
        self.tir_mensual = irr * 100

        self.calculate_tir_trimestral()
        self.calculate_tir_semestral()
        self.calculate_tir_anual()

    def calculate_tir_trimestral(self):
        # Calculando
        date = datetime(int(self.year), int(self.month), 1)
        past_extractos = self.env['ati.extracto']
        for i in range(0, 3):
            previous_date = date - relativedelta(months=i)
            past_extracto = self.env['ati.extracto'].search([
                ('cliente', '=', self.cliente.id),
                ('year', '=', str(previous_date.year)),
                ('month', '=', str(previous_date.month).zfill(2)),

            ], limit=1)
            past_extractos += past_extracto
        if len(past_extractos) == 3:

            tir_ids = past_extractos.mapped('tir_ids')
            cash_flows = [(x.move + x.valor, x.date) for x in tir_ids]

            dates = [cf[1] for cf in cash_flows]
            amounts = [cf[0] for cf in cash_flows]

            def npv(rate):
                # Start with the first date as the base
                base_date = dates[0]
                total_npv = 0

                if rate <= -1:
                    return float('inf')  # Return a high value to indicate invalid IRR

                for i, date in enumerate(dates):
                    # Calculate the time difference in days
                    days_difference = (date - base_date).days

                    # Discount factor
                    discount_factor = (1 + rate) ** (days_difference / 365.0)

                    # Contribution to NPV
                    total_npv += amounts[i] / discount_factor

                return total_npv

            initial_guess = 0.1
            irr = opt.root_scalar(npv, bracket=[-0.99, 5], method='brentq').root
            self.tir_trimestral = irr * 100
        else:
            self.tir_trimestral = 0

    def calculate_tir_semestral(self):
        # Calculando
        date = datetime(int(self.year), int(self.month), 1)
        past_extractos = self.env['ati.extracto']
        for i in range(0, 6):
            previous_date = date - relativedelta(months=i)
            past_extracto = self.search([
                ('cliente', '=', self.cliente.id),
                ('month', '=', str(previous_date.month).zfill(2)),
                ('year', '=', str(previous_date.year)),
            ], limit=1)
            past_extractos += past_extracto
        if len(past_extractos) == 6:
            tir_ids = past_extractos.mapped('tir_ids')
            cash_flows = [(x.move + x.valor, x.date) for x in tir_ids]

            dates = [cf[1] for cf in cash_flows]
            amounts = [cf[0] for cf in cash_flows]

            def npv(rate):
                # Start with the first date as the base
                base_date = dates[0]
                total_npv = 0

                if rate <= -1:
                    return float('inf')  # Return a high value to indicate invalid IRR

                for i, date in enumerate(dates):
                    # Calculate the time difference in days
                    days_difference = (date - base_date).days

                    # Discount factor
                    discount_factor = (1 + rate) ** (days_difference / 365.0)

                    # Contribution to NPV
                    total_npv += amounts[i] / discount_factor

                return total_npv

            initial_guess = 0.1
            irr = opt.root_scalar(npv, bracket=[-0.99, 5], method='brentq').root
            self.tir_semestral = irr * 100
        else:
            self.tir_semestral = 0

    def calculate_tir_anual(self):
        # Calculando
        date = datetime(int(self.year), int(self.month), 1)
        past_extractos = self.env['ati.extracto']
        for i in range(0, 12):
            previous_date = date - relativedelta(months=i)
            past_extracto = self.search([
                ('cliente', '=', self.cliente.id),
                ('month', '=', str(previous_date.month).zfill(2)),
                ('year', '=', str(previous_date.year)),
            ], limit=1)
            past_extractos += past_extracto
        if len(past_extractos) == 12:
            tir_ids = past_extractos.mapped('tir_ids')
            cash_flows = [(x.move + x.valor, x.date) for x in tir_ids]

            dates = [cf[1] for cf in cash_flows]
            amounts = [cf[0] for cf in cash_flows]

            def npv(rate):
                # Start with the first date as the base
                base_date = dates[0]
                total_npv = 0

                if rate <= -1:
                    return float('inf')  # Return a high value to indicate invalid IRR

                for i, date in enumerate(dates):
                    # Calculate the time difference in days
                    days_difference = (date - base_date).days

                    # Discount factor
                    discount_factor = (1 + rate) ** (days_difference / 365.0)

                    # Contribution to NPV
                    total_npv += amounts[i] / discount_factor

                return total_npv

            initial_guess = 0.1
            irr = opt.root_scalar(npv, bracket=[-0.99, 5], method='brentq').root
            self.tir_anual = irr * 100
        else:
            self.tir_anual = 0


    def validacion_totales(self):
        self.show_alert_product_validation = False
        self.message_product_validation = ''

        productos = self.resumen_inversion_ids.filtered(
            lambda x: x.gestor and x.producto
        )

        for line in productos:
            #Para CSF
            if line.gestor.code == 'CUANTUM':
                #Factoring
                if line.name == 'Factoring':
                    compras = sum( [recurso.value for recurso in self.recursos_csf.filtered(
                        lambda x: x.investment_type.name == 'Factoring' and x.movement_type.name == 'Compra'
                    )])
                    recaudos = sum( [recurso.value for recurso in self.recursos_csf.filtered(
                        lambda x: x.investment_type.name == 'Factoring' and x.movement_type.name == 'Aplicación de recaudo'
                    )])
                    valor_validado = (
                        line.valor_anterior + compras + line.rendimiento_causado - recaudos - line.administracion
                    )
                    validation = line.valor_actual != valor_validado
                    if validation:
                        self.message_product_validation += 'Validación de totales para gestor CUANTUM producto Factoring no es correcta. Actual={0} Validado={1} \n'.format(line.valor_actual,valor_validado )
                #Libranzas
                if line.name == 'Libranzas':
                    compras = sum( [recurso.value for recurso in self.recursos_csf.filtered(
                        lambda x: x.investment_type.name == 'Libranzas' and x.movement_type.name == 'Compra'
                    )])
                    recaudos = sum( [recurso.value for recurso in self.recursos_csf.filtered(
                        lambda x: x.investment_type.name == 'Libranzas' and x.movement_type.name == 'Aplicación de recaudo'
                    )])
                    valor_validado = (
                            line.valor_anterior + compras + line.rendimiento_causado - recaudos - line.administracion
                    )
                    validation = line.valor_actual != valor_validado
                    if validation:
                        self.message_product_validation += 'Validación de totales para gestor CUANTUM producto Libranzas no es correcta. Actual={0} Validado={1} \n'.format(line.valor_actual,valor_validado)
                #Sentencias
                if line.name == 'Sentencias':
                    compras = sum( [recurso.value for recurso in self.recursos_csf.filtered(
                        lambda x: x.investment_type.name == 'Sentencias' and x.movement_type.name == 'Compra'
                    )])
                    recaudos = sum( [recurso.value for recurso in self.recursos_csf.filtered(
                        lambda x: x.investment_type.name == 'Sentencias' and x.movement_type.name == 'Aplicación de recaudo'
                    )])
                    valor_validado = (
                            line.valor_anterior + compras + line.rendimiento_causado - recaudos - line.administracion
                    )
                    validation = line.valor_actual != valor_validado
                    if validation:
                        self.message_product_validation += 'Validación de totales para gestor CUANTUM producto Sentencias no es correcta. Actual={0} Validado={1} \n'.format(line.valor_actual,valor_validado )

                # Sentencias
                if line.name == 'Mutuos':
                    compras = sum([recurso.value for recurso in self.recursos_csf.filtered(
                        lambda x: x.investment_type.name == 'Mutuos' and x.movement_type.name == 'Compra'
                    )])
                    recaudos = sum([recurso.value for recurso in self.recursos_csf.filtered(
                        lambda
                            x: x.investment_type.name == 'Mutuos' and x.movement_type.name == 'Aplicación de recaudo'
                    )])
                    valor_validado = (
                            line.valor_anterior + compras + line.rendimiento_causado - recaudos - line.administracion
                    )
                    validation = line.valor_actual != valor_validado
                    if validation:
                        self.message_product_validation += 'Validación de totales para gestor CUANTUM producto Mutuos no es correcta. Actual={0} Validado={1} \n'.format(
                            line.valor_actual, valor_validado)
            # Para FCL
            if line.gestor.code == 'FCL':
                # Libranzas
                if line.name == 'Libranzas':
                    compras = sum([recurso.value for recurso in self.recursos_fcl.filtered(
                        lambda x: x.investment_type.name == 'Libranzas' and x.movement_type.name == 'Compra'
                    )])
                    recaudos = sum([recurso.value for recurso in self.recursos_fcl.filtered(
                        lambda
                            x: x.investment_type.name == 'Libranzas' and x.movement_type.name == 'Aplicación de recaudo'
                    )])
                    valor_validado = (
                            line.valor_anterior + compras + line.rendimiento_causado - recaudos - line.administracion
                    )
                    validation = line.valor_actual != valor_validado
                    if validation:
                        self.message_product_validation += 'Validación de totales para gestor FCL producto Libranzas no es correcta. Actual={0} Validado={1} \n'.format(line.valor_actual,valor_validado )
            # Para FCP
            if line.gestor.code == 'FCP':
                if line.name == 'Statum I':
                    compras = sum( [recurso.value for recurso in self.recursos_fcp.filtered(
                        lambda x: x.investment_type.name == 'Statum I' and x.movement_type.name == 'Compra'
                    )])
                    recaudos = sum( [recurso.value for recurso in self.recursos_fcp.filtered(
                        lambda x: x.investment_type.name == 'Statum I' and x.movement_type.name == 'Aplicación de recaudo'
                    )])
                    valor_validado = (
                            line.valor_anterior + compras + line.rendimiento_causado - recaudos - line.administracion
                    )
                    validation = line.valor_actual != valor_validado
                    if validation:
                        self.message_product_validation += 'Validación de totales para gestor FCP producto Statum I no es correcta. Actual={0} Validado={1} \n'.format(line.valor_actual,valor_validado )
                if line.name == 'Statum II':
                    compras = sum( [recurso.value for recurso in self.recursos_fcp.filtered(
                        lambda x: x.investment_type.name == 'Statum II' and x.movement_type.name == 'Compra'
                    )])
                    recaudos = sum( [recurso.value for recurso in self.recursos_fcp.filtered(
                        lambda x: x.investment_type.name == 'Statum II' and x.movement_type.name == 'Aplicación de recaudo'
                    )])
                    valor_validado = (
                            line.valor_anterior + compras + line.rendimiento_causado - recaudos - line.administracion
                    )
                    validation = line.valor_actual != valor_validado
                    if validation:
                        self.message_product_validation += 'Validación de totales para gestor FCP producto Statum II no es correcta. Actual={0} Validado={1} \n'.format(line.valor_actual,valor_validado )


        if len(self.message_product_validation) > 0:
            self.show_alert_product_validation = True



    def validacion_informes_clientes(self):
        #Tomando último informe clientes creado
        informe_clientes = self.env['ctm.validacion'].search([('year','=',self.year),('month','=',self.month)], order='day desc', limit=1)
        #Tomando linea de detalle del informe clientes
        informe_clientes_detalle = informe_clientes.detalle_validacion_ids.filtered(
                lambda x: x.cliente == self.cliente
        )
        #VALORES DE INFORME CLIENTES
        informe_factoring_csf = int(informe_clientes_detalle.factoring_csf)
        informe_libranzas_csf = int(informe_clientes_detalle.libranzas_csf)
        informe_sentencias_csf = int(informe_clientes_detalle.sentencias_csf)
        informe_rpr_csf = int(informe_clientes_detalle.rpr_csf)
        # FCL
        informe_libranzas_fcl = int(informe_clientes_detalle.libranzas_fcl)
        informe_rpr_fcl = int(informe_clientes_detalle.rpr_fcl)
        # FCP
        informe_sentencias_fcp = int(informe_clientes_detalle.sentencias_fcp)
        informe_rpr_fcp = int(informe_clientes_detalle.rpr_fcp)

        informe_total = int(informe_clientes_detalle.total)

        resultados_informe = [
            informe_factoring_csf, informe_libranzas_csf, informe_sentencias_csf,informe_rpr_csf,
            informe_libranzas_fcl, informe_rpr_fcl, informe_sentencias_fcp, informe_rpr_fcp, informe_total

        ]

        #VALORES DE RESUMEN DE MOVIMIENTOS
        resumen_factoring_csf = 0
        resumen_libranzas_csf = 0
        resumen_sentencias_csf = 0
        resumen_rpr_csf = 0
        # FCL
        resumen_libranzas_fcl = 0
        resumen_rpr_fcl = 0
        # FCP
        resumen_sentencias_fcp = 0
        resumen_rpr_fcp = 0

        resumen_total = 0
        actual_type = 'CSF'
        for line in self.resumen_inversion_ids:
            if line.name == 'Factoring':
                resumen_factoring_csf = int(line.valor_actual)
            if line.name == 'Libranzas' and actual_type == 'CSF':
                resumen_libranzas_csf = int(line.valor_actual)
            if line.name == 'Sentencias' and actual_type == 'CSF':
                resumen_sentencias_csf = int(line.valor_actual)
            if line.name == 'RPR CSF':
                resumen_rpr_csf = int(line.valor_actual)
                actual_type = 'FCL'

            if line.name == 'Libranzas' and actual_type == 'FCL':
                resumen_libranzas_fcl = int(line.valor_actual)
            if line.name == 'RPR FCL':
                resumen_rpr_fcl = int(line.valor_actual)
                actual_type = 'FCP'

            if line.name == 'Sentencias' and actual_type == 'FCP':
                resumen_sentencias_fcp = int(line.valor_actual)
            if line.name == 'RPR STATUM':
                resumen_rpr_fcp = int(line.valor_actual)

        resumen_total = int(self.resumen_inversion_ids[-1].valor_actual)

        resultados_extracto = [
            resumen_factoring_csf, resumen_libranzas_csf, resumen_sentencias_csf, resumen_rpr_csf,
            resumen_libranzas_fcl, resumen_rpr_fcl, resumen_sentencias_fcp, resumen_rpr_fcp, resumen_total
        ]

        self.show_alert_validation = resultados_extracto != resultados_informe


    def set_borrador_extracto(self):
        for rec in self:
            future_extractos = self.search([
                ('cliente', '=', rec.cliente.id),
                ('year', '=', rec.year),
                ('month', '>', rec.month),
                ('state', '!=', 'draft'),
            ])
            future_year_extractos = self.search([
                ('cliente', '=', rec.cliente.id),
                ('year', '>', rec.year),
                ('state', '!=', 'draft'),
            ])
            if future_extractos or future_year_extractos:
                raise ValidationError(
                    'No se puede cambiar de estado porque existen extractos futuros que no están en borrador')

            if self.env.user.id in [8,2,10, 108]:
                rec.state = 'draft'
            else:
                raise ValidationError('Usted no tiene permisos para realizar esta acción')


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
            'partner_ids': self.cliente.id,
            'notify_followers': True,
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

class Tir(models.Model):
    _name = 'ati.tir'
    _order = 'date asc'

    extracto_id = fields.Many2one('ati.extracto','Extracto')
    valor = fields.Float('Valor del Portafolio')
    date = fields.Date('Día')
    move = fields.Float('Movimiento')


class TirGestor(models.Model):
    _name = 'ati.tir.gestor'
    _description = 'TIR por Gestor'
    _order = 'gestor_id asc, tipo_id asc, date asc, valor desc'

    extracto_id = fields.Many2one('ati.extracto', 'Extracto')
    valor = fields.Float('Valor del Portafolio')
    date = fields.Date('Día')
    move = fields.Float('Movimiento')
    gestor_id = fields.Many2one('ati.gestor', 'Gestor')
    tipo_id = fields.Many2one('ati.investment.type', 'Tipo')

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

    @api.depends("titulo")
    def _compute_paid_value(self):
        for rec in self:
            if len(rec.titulo) > 0:
                if len(rec.titulo.tit_historico_ids) > 0:
                    for line in rec.titulo.tit_historico_ids:
                        if line.periodo[:2] == rec.extracto_id.month and line.periodo[3:7] == rec.extracto_id.year:
                            rec.paid_value += line.recaudo
                else:
                    rec.paid_value = 0
            else:
                rec.paid_value = 0

    extracto_id = fields.Many2one('ati.extracto','Extracto')
    titulo = fields.Many2one('ati.titulo','Titulo')
    investment_type = fields.Many2one('ati.investment.type','Tipo')
    issuing = fields.Many2one('res.partner','Emisor',required=1)
    payer = fields.Many2one('res.partner','Pagador',required=1)
    sale_value = fields.Float('Valor de Compra')
    value = fields.Float('Valor de portafolio')
    fee = fields.Float('Tasa')
    bonding_date = fields.Date('Fecha de Negociación')
    redemption_date = fields.Date('Fecha de vencimiento')
    #Por ahora el recaudo, cuando se carguen más titulos en el mes se debe hacer cóidog de suma
    paid_value = fields.Float('Valor pagado')
    state_titulo = fields.Many2one('ati.state.titulo', 'Estado')



class RecursoRecompraCSF(models.Model):
    _name = 'ati.extracto.recompra.csf'

    name = fields.Char('Nombre')
    date = fields.Date('Fecha')
    value = fields.Float('Valores')
    investment_type = fields.Many2one('ati.investment.type','Producto')
    movement_type = fields.Many2one('ati.movement.type','Movimiento')
    buyer = fields.Many2one('res.partner','Comprador',required=1)
    extracto_id = fields.Many2one('ati.extracto', 'Extracto')

class RecursoRecompraFCL(models.Model):
    _name = 'ati.extracto.recompra.fcl'

    name = fields.Char('Nombre')
    date = fields.Date('Fecha')
    value = fields.Float('Valores')
    investment_type = fields.Many2one('ati.investment.type','Producto')
    movement_type = fields.Many2one('ati.movement.type','Movimiento')
    buyer = fields.Many2one('res.partner','Comprador',required=1)
    extracto_id = fields.Many2one('ati.extracto', 'Extracto')

class RecursoRecompraFCP(models.Model):
    _name = 'ati.extracto.recompra.fcp'

    name = fields.Char('Nombre')
    date = fields.Date('Fecha')
    value = fields.Float('Valores')
    investment_type = fields.Many2one('ati.investment.type','Producto')
    movement_type = fields.Many2one('ati.movement.type','Movimiento')
    buyer = fields.Many2one('res.partner','Comprador',required=1)
    extracto_id = fields.Many2one('ati.extracto', 'Extracto')