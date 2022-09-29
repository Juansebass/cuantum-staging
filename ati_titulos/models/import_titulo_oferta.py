# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime
import base64
import csv
from datetime import date as dt
import logging
_logger = logging.getLogger(__name__)



class ImportOfertaTitulos(models.Model):
    _name = 'ati.import.oferta.titulos'
    _order = "fch_procesado desc"
    _description = 'Oferta Titulos'

    def btn_process(self):
        _procesados = ""
        vals={}    
        self.ensure_one()
        if not self.delimiter:
            raise ValidationError('Debe ingresar el delimitador')
        if not self.client_file:
            raise ValidationError('Debe seleccionar el archivo')
        if self.state != 'draft':
            raise ValidationError('Archivo procesado!')
        

        self.file_content = base64.decodebytes(self.client_file)
        lines = self.file_content.split('\n')
        for i,line in enumerate(lines):
            if self.skip_first_line and i == 0:
                continue
            lista = line.split(self.delimiter)
            if len(lista) > 6:
                titulo = lista[0]
                emisor = lista[1]
                pagador = lista[2]
                fch_negociacion = lista[3]
                fch_vencimiento = lista[4]
                tasa_desc = lista[5]
                vpn_des = lista[6]

                vals.clear()
                
                partner_emisor = self.env['res.partner']
                if emisor != '':
                    partner_emisor = self.env['res.partner'].search([('name','=',emisor)], limit=1)
                    if len(partner_emisor) > 0:
                        vals['issuing'] = partner_emisor.id
                    else:
                        raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, el emisor {1}, contenido de linea: {2}".format(i, emisor, line))
                else:
                    raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, no contiene emisor, contenido de linea: {1}".format(i, line))

                if len(partner_emisor) > 0:

                    # Carga vals
                    if titulo != '':
                        vals['name'] = titulo.replace(' ', '')
                    else:
                        raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, la primera columna que refiere al titulo esta vacia, contenido de linea: {1}".format(i, line))
                    
                    if pagador != '':
                        partner_pagador = self.env['res.partner'].search([('name','=',pagador)], limit=1)
                        if len(partner_pagador) > 0:
                            vals['payer'] = partner_pagador.id
                        else:
                            raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, el pagador {1}, contenido de linea: {2}, NO EXISTE".format(i, pagador, line))
                    else:
                        raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, no contiene pagador, contenido de linea: {1}".format(i, line))
                    if fch_negociacion != '':
                        fecha_negociacion = datetime.strptime(fch_negociacion, '%d/%m/%y')
                        vals['bonding_date'] = fecha_negociacion
                    if fch_vencimiento != '':
                        fecha_vencimiento = datetime.strptime(fch_vencimiento, '%d/%m/%y')
                        vals['redemption_date'] = fecha_vencimiento
                    if tasa_desc != '':
                        vals['fee'] = float(tasa_desc.replace(',','.').replace('%',''))

                    vals['investment_type'] = self.investment_type.id
                    vals['manager'] = self.manager.id
                    vpn_des = vpn_des.replace('$','').replace(' ', '').replace('.', '').replace(',', '.')
                    vals['value'] = vpn_des

                    # Buscamos si el titulo ya existe
                    titulo_existente = self.env['ati.titulo.oferta'].search([('name','=',titulo)],limit=1)
                    if len(titulo_existente) > 0:
                        raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, el titulo: {1} ya existe como un titulo para ofertar".format(i, titulo))
                    
                    titulo_creado = self.env['ati.titulo.oferta'].sudo().create(vals)

                    _procesados += "{} \n".format(titulo_creado.name)
                else:
                    raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, contenido de linea: {1}. El cliente no existe".format(i, line))
            elif len(lista) == 1:
                continue
            else:
                _logger.warning("***** lista: {0}".format(len(lista)))
                raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, contenido de linea: {1}. Se necesitan al menos 7 columnas".format(i, line))
        self.ofertas_creadas = _procesados
        self.responsable = self.env.user.partner_id
        self.fch_procesado = datetime.today()
        self.state = 'processed'

    name = fields.Char('Nombre')
    client_file = fields.Binary('Archivo')
    manager = fields.Many2one('ati.gestor', 'Gestor', required=True)
    investment_type = fields.Many2one('ati.investment.type', 'Tipo', required=True)
    delimiter = fields.Char('Delimitador',default=";")
    fch_procesado = fields.Datetime('Fecha procesado')
    responsable = fields.Many2one('res.partner','Responsable de proceso')
    state = fields.Selection(selection=[('draft','Borrador'),('processed','Procesado')],string='Estado',default='draft')
    file_content = fields.Text('Texto archivo')
    ofertas_creadas = fields.Text('Creados')
    skip_first_line = fields.Boolean('Saltear primera linea',default=True)