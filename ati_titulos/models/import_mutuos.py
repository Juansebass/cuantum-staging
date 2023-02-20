# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime
import base64
import csv
from datetime import date as dt
import logging
_logger = logging.getLogger(__name__)



class ImportMutuo(models.Model):
    _name = 'import.mutuo'
    _order = "fch_procesado desc"
    _description = 'Mutuo'

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
        
        # Se valida si existe el periodo al cual se decea hacer un cargue de extractos, en el caso de existir se verifica que el 
        # estado del mismo se encuentre en estado abierto de cargue
        if self.month and self.year:
            periodo = self.env['ati.state.periodo'].search([('year','=',self.year),('month','=',self.month)])
            if len(periodo) > 0:
                if periodo.state_cargue == 'close':
                    raise ValidationError('El estado de cargue para este periodo se encuentra cerrado')
            else:
                raise ValidationError('No existe un periodo creado para el mes y año seleccionado')
        else:
            raise ValidationError('Debe introducir un mes y año de periodo para este cargue')

        self.file_content = base64.decodebytes(self.client_file)
        lines = self.file_content.split('\n')
        for i,line in enumerate(lines):
            if self.skip_first_line and i == 0:
                continue
            lista = line.split(self.delimiter)
            if len(lista) > 11:
                titulo = lista[0]
                emisor = lista[1]
                pagador = lista[2]
                comprador_corresp = lista[3]
                tipo_doc = lista[4]
                ident_comprador = lista[5]
                fch_negociacion = lista[6]
                fch_vencimiento = lista[7]
                tasa_desc = lista[8]
                vpn_des = lista[9]
                concepto = lista[10].replace(' ','')
                recaudo = lista[11]

                vals.clear()

                client = self.env['res.partner'].search([(self.client_match,'=',ident_comprador),('vinculado','=',True)])
                if len(client) > 1:
                    raise ValidationError("El CSV no se procesara por cliente con nit repetido en sistema. El nit {0} lo tienen dos o mas clientes".format(ident_comprador))
                if client:

                    # Carga vals
                    if titulo != '':
                        #comprobamos que el titulo no contenga separaciones
                        if titulo.find(' ') != -1:
                            raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, la primera columna que refiere al titulo esta contiene caracter de separacion, contenido de linea: {1}".format(i, line))
                        vals['title'] = titulo
                    else:
                        raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, la primera columna que refiere al titulo esta vacia, contenido de linea: {1}".format(i, line))
                    if emisor != '':
                        partner_emisor = self.env['res.partner'].search([('name','=',emisor)], limit=1)
                        if len(partner_emisor) > 0:
                            vals['issuing'] = partner_emisor.id
                        else:
                            raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, el emisor {1} no existe, contenido de linea: {2}".format(i, emisor, line))
                    else:
                        raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, no contiene emisor, contenido de linea: {1}".format(i, line))
                    if pagador != '':
                        partner_pagador = self.env['res.partner'].search([('name','=',pagador)], limit=1)
                        if len(partner_pagador) > 0:
                            vals['payer'] = partner_pagador.id
                        else:
                            raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, el pagador {1}, contenido de linea: {2}, NO EXISTE".format(i, pagador, line))
                    else:
                        raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, no contiene pagador, contenido de linea: {1}".format(i, line))
                    if fch_negociacion != '':
                        fecha_negociacion = datetime.strptime(fch_negociacion, '%d/%m/%Y')
                        vals['bonding_date'] = fecha_negociacion
                    if fch_vencimiento != '':
                        fecha_vencimiento = datetime.strptime(fch_vencimiento, '%d/%m/%Y')
                        vals['redemption_date'] = fecha_vencimiento
                    if tasa_desc != '':
                        vals['fee'] = float(tasa_desc.replace(',','.').replace('%',''))

                    inves_type = self.env['ati.investment.type'].search([('code', '=', 'MUT')])
                    vals['investment_type'] = inves_type.id
                    vals['client'] = client.id
                    vals['manager'] = self.manager.id
                    vpn_des = vpn_des.replace('$','').replace(' ', '').replace('.', '').replace(',', '.').replace('-','')
                    vals['value'] = vpn_des
                    recaudo = recaudo.replace('$','').replace(' ', '').replace('.', '').replace(',', '.').replace('-','')
                    try:
                        float(recaudo)
                    except:
                        recaudo = '0.00'

                    # Concepto o estado de titulo
                    if concepto != '':
                        _concepto_tmp = self.env['ati.state.titulo'].search([('code','=',concepto)], limit=1)
                        if len(_concepto_tmp) == 0:
                            _concepto_tmp = self.env['ati.state.titulo'].search([('code','ilike',concepto)], limit=1)
                        if len(_concepto_tmp) > 0:
                            vals['state_titulo'] = _concepto_tmp.id
                        else:  
                            raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, el concepto ingresado no corresponde a ninguno que este en el sistema, contenido de linea: {1}".format(i, line))
                    else:
                        raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, no contiene concepto, contenido de linea: {1}".format(i, line))
                    

                    #Comprobamos si un titulo es hijo
                    _parent = self.env['ati.titulo']
                    _is_parent = titulo.find('-')
                    if _is_parent != -1:
                        _parent = self.env['ati.titulo'].search([('title','=',titulo[:_is_parent]),('issuing','=',partner_emisor.id)],limit=1)
                        if len(_parent) != 1:
                            raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, el titulo padre indicado no existe, contenido de linea: {1}".format(i, line))
                        
                        vals['parent_id'] = _parent.id
                    _logger.warning('***** En el titulo {0}, el padre es {1}'.format(titulo, _parent))
                    
                    # Buscamos si el titulo ya existe
                    titulo_existente = self.env['ati.titulo'].search([('title','=',titulo),('issuing','=',partner_emisor.id)],limit=1)
                    
                    titulo_creado = self.env['ati.titulo']
                    # Si el titulo ya existe lo modificamos y agregamos en su historico, de lo contrario lo creamos y 
                    # agregamos en el historico del nuevo titulo
                    if len(titulo_existente) > 0:
                        recaudo_total = float(recaudo) + titulo_existente.recaudo_total
                        vals['recaudo_total'] = recaudo_total
                        vals['date'] = datetime.today()
                        vals['last_periodo'] = self.month + '/' + self.year
                        titulo_existente.sudo().write(vals)
                    
                        # Elimino recaudo_total de vals ya que no existe en ati.titulo.historico
                        del vals['recaudo_total']
                        del vals['date']
                        del vals['last_periodo']
                        if "is_parent" in vals:
                            del vals['is_parent']
                        if "parent_id" in vals:
                            del vals['parent_id']

                        # Agrego recaudo, date_create, titulo_id para ati.titulo.historico
                        vals['date_create'] = datetime.today()
                        vals['periodo'] = self.month + '/' + self.year
                        vals['recaudo'] = recaudo
                        vals['titulo_id'] = titulo_existente.id
                        vals['responsable'] = self.env.user.partner_id.id
                        self.env['ati.titulo.historico'].sudo().create(vals)
                    else:
                        _logger.warning('***** Creando titulo: {0}'.format(vals['title']))
                        vals['recaudo_total'] = recaudo
                        vals['date'] = datetime.today()
                        vals['last_periodo'] = self.month + '/' + self.year
                        titulo_creado = self.env['ati.titulo'].sudo().create(vals)

                        # Elimino recaudo_total de vals ya que no existe en ati.titulo.historico
                        del vals['recaudo_total']
                        del vals['date']
                        del vals['last_periodo']
                        if "is_parent" in vals:
                            del vals['is_parent']
                        if "parent_id" in vals:
                            del vals['parent_id']

                        # Agrego recaudo, date_create, titulo_id para ati.titulo.historico
                        vals['date_create'] = datetime.today()
                        vals['periodo'] = self.month + '/' + self.year
                        vals['recaudo'] = recaudo
                        vals['titulo_id'] = titulo_creado.id
                        vals['responsable'] = self.env.user.partner_id.id
                        self.env['ati.titulo.historico'].sudo().create(vals)

                    #Si el titulo es hijo comprobamos que exista la relacion con el padre, si no existe la creamos
                    if len(_parent) > 0 and len(titulo_creado) > 0:
                        _existe = False
                        for son in _parent.son_ids:
                            if titulo == son.name.name:
                                _existe = True
                        _logger.warning('**** consulta por parent en el titulo: {0}'.format(titulo))
                        if _parent.is_parent == False:
                            _logger.warning('**** confirma como padre al titulo: {0}'.format(titulo))
                            _parent.write({'is_parent':True})
                        if not _existe:
                            _parent.write({'son_ids': [(0,0,{'name':titulo_creado.id})]})


                    _procesados += "{} \n".format(ident_comprador)
                else:
                    _noprocesados += "{} \n".format(ident_comprador)
                    raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, contenido de linea: {1}. El cliente no existe".format(i, line))
            elif len(lista) == 1:
                continue
            else:
                _logger.warning("***** lista: {0}".format(len(lista)))
                raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, contenido de linea: {1}. Se necesitan al menos 18 columnas".format(i, line))
        self.clientes_creados = _procesados
        self.not_processed_content = _noprocesados
        self.responsable = self.env.user.partner_id
        self.fch_procesado = datetime.today()
        self.state = 'processed'

    name = fields.Char('Nombre')
    month = fields.Char('Mes de Periodo')
    year = fields.Char('Año de Periodo')
    client_file = fields.Binary('Archivo')
    manager = fields.Many2one('ati.gestor', 'Gestor', required=True)
    delimiter = fields.Char('Delimitador',default=";")
    fch_procesado = fields.Datetime('Fecha procesado')
    responsable = fields.Many2one('res.partner','Responsable de proceso')
    state = fields.Selection(selection=[('draft','Borrador'),('processed','Procesado')],string='Estado',default='draft')
    file_content = fields.Text('Texto archivo')
    not_processed_content = fields.Text('Texto no procesado')
    clientes_creados = fields.Text('Creados')
    skip_first_line = fields.Boolean('Saltear primera linea',default=True)
    client_match = fields.Selection(selection=[('vat','Vat')],string='Buscar clientes por...',default='vat')