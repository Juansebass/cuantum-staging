 # -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
import base64



class EliminarHistoricos(models.Model):
    _name = 'eliminar.rpr'

    responsible = fields.Many2one('res.partner', 'Responsable')
    month = fields.Char('Mes de Periodo', required=1)
    year = fields.Char('Año de Periodo', required=1)
    state = fields.Selection([('sin_eliminar', 'Sin Eliminar'), ('eliminados', 'Eliminados')], default='sin_eliminar',
                              string='Estado')
    name = fields.Char('Nombre')
    client_file = fields.Binary('Archivo')
    file_content = fields.Text('Texto archivo')
    delimiter = fields.Char('Delimitador', default=";")
    skip_first_line = fields.Boolean('Saltear primera linea', default=True)
    # manager = fields.Many2one('ati.gestor', 'Gestor', required=True)
    # eliminados = fields.Text('Eliminados')
    #
    # def btn_delete(self):
    #     _eliminados = ""
    #     self.ensure_one()
    #     if not self.delimiter:
    #         raise ValidationError('Debe ingresar el delimitador')
    #     if not self.client_file:
    #         raise ValidationError('Debe seleccionar el archivo')
    #     if self.state != 'sin_eliminar':
    #         raise ValidationError('Archivo procesado!')
    #     if not self.month and not self.year:
    #         raise ValidationError('Debe introducir un mes y año de periodo para este cargue')
    #     if not self.manager:
    #         raise ValidationError('Debe introducir un gestor para este cargue')
    #
    #     self.file_content = base64.decodebytes(self.client_file)
    #     lines = self.file_content.split('\r')
    #
    #     for i,line in enumerate(lines):
    #         new_record = None
    #         if self.skip_first_line and i == 0:
    #             continue
    #         lista = line.split(self.delimiter)
    #
    #         if len(lista) > 3:
    #
    #             try:
    #                 titulo_name = lista[0]
    #                 cliente = lista[1]
    #                 nit = lista[2]
    #                 titulo_id = lista[3].split('\n')[0]
    #                 titulo_historico = self.env['ati.titulo.historico'].search(
    #                     [('id', '=', titulo_id)], limit=1)
    #                 titulo_historico.unlink()
    #                 _eliminados += "{0};{1};{2};{3}\n".format(titulo_name, cliente, nit, titulo_id)
    #
    #
    #             except Exception as e:
    #
    #                 raise ValidationError('Error: {0}, Línea: {1}'.format(e, lista))
    #
    #     self.eliminados = _eliminados
    #     self.state = 'eliminados'
    #     self.responsible = self.env.user.partner_id