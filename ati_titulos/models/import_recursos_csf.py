# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime
import base64
import csv
from datetime import date as dt
import logging
_logger = logging.getLogger(__name__)



class ImportRecursosCSF(models.Model):
    _name = 'import.recursos.csf'
    _order = "fch_procesado desc"
    _description = 'Modelo para importacion de recursos de recompra CSF'

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
            if len(lista) > 6:
                fecha = lista[0]
                valores = lista[1]
                movimiento = lista[2]
                comprador = lista[3]
                documento = lista[4]
                tip_documento = lista[5]
                linea_neogcio = lista[6]

                vals.clear()

                client = self.env['res.partner'].search([(self.client_match,'=',documento)])
                if len(client) > 1:
                    raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, tienes mas de un cliente con el mismo documento, contenido de linea: {1}".format(i, line))
                if len(client) > 0:
                    
                    # Carga vals

                    vals['buyer'] = client.id
                    
                    if fecha != '':
                        fecha_recurso = datetime.strptime(fecha, '%d/%m/%Y')
                        vals['date'] = fecha_recurso
                    else:
                        raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, la primera columna que refiere al la fecha esta vacia, contenido de linea: {1}".format(i, line))
                    
                    if valores != '':
                        valores = valores.replace('$','').replace(' ', '').replace('.', '').replace(',', '.').replace('-','')
                        vals['value'] = valores
                    else:
                        raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, la segunda columna que refiere al valor esta vacia, contenido de linea: {1}".format(i, line))
                    
                    if movimiento != '':
                        mov_tmp = self.env['ati.movement.type'].search([('code','=',movimiento)])
                        if len(mov_tmp) < 1:
                            raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, no se encuentra movimiento con codigo {1}, contenido de linea: {2}".format(i, mov_tmp, line))
                        
                        vals['movement_type'] = mov_tmp.id
                    else:
                        raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, la tercera columna que refiere al movimiento esta vacia, contenido de linea: {1}".format(i, line))

                    if linea_neogcio != '':
                        inves_type = self.env['ati.investment.type'].search([('code', '=', linea_neogcio)])
                        if len(inves_type) < 1:
                            raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, no se encuentra una linea de negocio con codigo {1}, contenido de linea: {2}".format(i, linea_neogcio, line))
                        
                        vals['investment_type'] = inves_type.id
                    elif movimiento == 'COMPRA' or movimiento == 'APLICACION':
                        raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, la séptima columna que refiere a la linea de negocio esta vacia, contenido de linea: {1}".format(i, line))

                    #Creamos recurso en proceso de recompra

                    self.env['ati.recurso.recompra.csf'].sudo().create(vals)


                    _procesados += "{} \n".format(documento)
                else:
                    _noprocesados += "{} \n".format(documento)
                    raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, contenido de linea: {1}. El cliente no existe".format(i, line))
            elif len(lista) == 1:
                continue
            else:
                _logger.warning("***** lista: {0}".format(len(lista)))
                raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, contenido de linea: {1}. Se necesitan al menos 6 columnas".format(i, line))
        self.recursos_cargados = _procesados
        self.not_processed_content = _noprocesados
        self.responsable = self.env.user.partner_id
        self.fch_procesado = datetime.today()
        self.state = 'processed'

    name = fields.Char('Nombre')
    month = fields.Char('Mes de Periodo')
    year = fields.Char('Año de Periodo')
    client_file = fields.Binary('Archivo')
    delimiter = fields.Char('Delimitador',default=";")
    fch_procesado = fields.Datetime('Fecha procesado')
    responsable = fields.Many2one('res.partner','Responsable de proceso')
    state = fields.Selection(selection=[('draft','Borrador'),('processed','Procesado')],string='Estado',default='draft')
    file_content = fields.Text('Texto archivo')
    not_processed_content = fields.Text('Texto no procesado')
    recursos_cargados = fields.Text('Recursos Cargados')
    skip_first_line = fields.Boolean('Saltear primera linea',default=True)
    client_match = fields.Selection(selection=[('vat','Vat')],string='Buscar clientes por...',default='vat')