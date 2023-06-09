from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime
import base64
import csv
from datetime import date as dt
import logging
_logger = logging.getLogger(__name__)



class ImportRendimientosAdministracion(models.Model):
    _name = 'import.rendimientos.administracion'
    _order = "fch_procesado desc"
    _description = 'Rendimientos y Administracion'

    def btn_process(self):

        #date_string = '2022-12-01'
        #date_string_stop = '2022-12-31'
        #datetime_star = datetime.strptime(date_string, '%Y-%m-%d')
        #datetime_stop = datetime.strptime(date_string_stop, '%Y-%m-%d')
        #fcl = self.env['ati.recurso.recompra.fcl'].search([('date','>=',datetime_star),('date','<=',datetime_stop)])
        #fcp = self.env['ati.recurso.recompra.fcp'].search([('date','>=',datetime_star),('date','<=',datetime_stop)])
        #csf = self.env['ati.recurso.recompra.csf'].search([('date','>=',datetime_star),('date','<=',datetime_stop)])
#
        #for f in fcl:
        #    f.unlink()
        #for c in fcp:
        #    c.unlink()
        #for s in csf:
        #    s.unlink()
#
        #return



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
            if len(lista) > 7:
                fecha = lista[0]
                valores = lista[1]
                movimiento = lista[2]
                comprador = lista[3]
                documento = lista[4]
                tip_documento = lista[5]
                linea_neogcio = lista[6]
                gestor = lista[7]

                vals.clear()

                client = self.env['res.partner'].search([(self.client_match,'=',documento)])
                if len(client) > 0:
                    if len(client) > 1:
                        raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, se encuentran dos o mas clientes con el mismo documento: {1}, contenido de linea: {2}".format(i,documento, line))
                    # Carga vals

                    vals['buyer'] = client.id
                    
                    if fecha != '':
                        fecha_recurso = datetime.strptime(fecha, '%d/%m/%Y')
                        vals['date'] = fecha_recurso
                    else:
                        raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, la primera columna que refiere al la fecha esta vacia, contenido de linea: {1}".format(i, line))
                    
                    if valores != '':
                        valores = valores.replace('$','').replace(' ', '').replace('.', '').replace(',', '.')
                        vals['value'] = valores
                    else:
                        raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, la segunda columna que refiere al valor esta vacia, contenido de linea: {1}".format(i, line))
                    
                    if movimiento != '':
                        if movimiento not in ['RENDIMIENTO','ADMINISTRACION']:
                            raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, no se encuentra movimiento con codigo {1}, contenido de linea: {2}".format(i, movimiento, line))
                        
                        vals['movement_type'] = movimiento
                    else:
                        raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, la segunda columna que refiere al valor esta vacia, contenido de linea: {1}".format(i, line))

                    if linea_neogcio != '':
                        inves_type = self.env['ati.investment.type'].search([('code', '=', linea_neogcio)])
                        if len(inves_type) < 1:
                            raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, no se encuentra una linea de negocio con codigo {1}, contenido de linea: {2}".format(i, linea_neogcio, line))
                        
                        vals['investment_type'] = inves_type.id
                    else:
                        raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, la septima columna que refiere a la linea de negocio esta vacia, contenido de linea: {1}".format(i, line))

                    if gestor != '':
                        manager = self.env['ati.gestor'].search([('code', '=', gestor)])
                        if len(manager) < 1:
                            raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, no se encuentra un Gestor con codigo {1}, contenido de linea: {2}".format(i, gestor, line))
                        
                        vals['manager'] = manager.id
                    else:
                        raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, la octava columna que refiere al gestor esta vacia, contenido de linea: {1}".format(i, line))

                    #Creamos recurso en proceso de recompra

                    self.env['ati.rendimientos.administracion'].sudo().create(vals)


                    _procesados += "{} \n".format(documento)
                else:
                    _noprocesados += "{} \n".format(documento)
                    raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, contenido de linea: {1}. El cliente no existe".format(i, line))
            elif len(lista) == 1:
                continue
            else:
                _logger.warning("***** lista: {0}".format(len(lista)))
                raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, contenido de linea: {1}. Se necesitan al menos 8 columnas".format(i, line))
        self.ren_adm_cargados = _procesados
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
    ren_adm_cargados = fields.Text('Recursos Cargados')
    skip_first_line = fields.Boolean('Saltear primera linea',default=True)
    client_match = fields.Selection(selection=[('vat','Vat')],string='Buscar clientes por...',default='vat')