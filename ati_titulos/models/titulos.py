 # -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
import base64

logger = logging.getLogger(__name__)

class Titulo(models.Model):
    _name = 'ati.titulo'
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char('Nombre')
    investment_type = fields.Many2one('ati.investment.type','Tipo de inversion', required=1)
    client = fields.Many2one('res.partner','Cliente',required=1)
    manager = fields.Many2one('ati.gestor','Gestor',required=1)
    issuing = fields.Many2one('res.partner','Emisor',required=1)
    payer = fields.Many2one('res.partner','Pagador',required=1)
    title = fields.Char('Titulo',required=1)
    last_periodo = fields.Char('Ultimo periodo cargado')
    date = fields.Date('Fecha ultima carga')
    sale_value = fields.Float('Valor de Compra')
    value = fields.Float('Valor')
    recaudo_total = fields.Float('Recaudo Total')
    fee = fields.Float('Tasa')
    bonding_date = fields.Date('Fecha de validacion')
    redemption_date = fields.Date('Fecha de redencion')
    state_titulo = fields.Many2one('ati.state.titulo','Estado de titulo')
    state = fields.Selection(
        string='Status',
        store=True,
        selection=[
            ('draft', 'Borrador'),
            ('cancel', 'Cancelado'),
            ('confirmed', 'Confirmado')
        ],
    )
    tit_historico_ids = fields.One2many('ati.titulo.historico','titulo_id','Titulo Historico')

    #Variables de padre/hijo
    is_parent = fields.Boolean('Es padre')
    is_son = fields.Boolean(related='parent_id.is_parent', string='Es Hijo')
    son_ids = fields.One2many('ati.titulo.son','parent_id','Titulos hijo')
    parent_id = fields.Many2one('ati.titulo', 'Padre')

    @api.model
    def create(self, var):

        res = super(Titulo, self).create(var)
        res.name = res.title

        return res
    
    def write(self, values):
        res = super(Titulo, self).write(values)
        for son in self.son_ids:
                son.name.parent_id = self.id

        return res

    def unlink(self):
        if self.env.user.id != 8:
            raise ValidationError('No tienes permisos para borrar titulos')
        else:
            return super(Titulo, self).unlink()

class TitulosHistorico(models.Model):
    _name = 'ati.titulo.historico'

    name = fields.Char('Nombre')
    titulo_id = fields.Many2one('ati.titulo','Titulo', ondelete='cascade')
    investment_type = fields.Many2one('ati.investment.type','Tipo de inversion', required=1)
    client = fields.Many2one('res.partner','Cliente',required=1)
    manager = fields.Many2one('ati.gestor','Gestor',required=1)
    issuing = fields.Many2one('res.partner','Emisor',required=1)
    payer = fields.Many2one('res.partner','Pagador',required=1)
    title = fields.Char('Titulo',required=1)
    periodo = fields.Char('Periodo')
    date_create = fields.Date('Fecha Carga')
    movement_type = fields.Many2one('ati.movement.type','Tipo de movimiento')
    sale_value = fields.Float('Valor de Compra')
    value = fields.Float('Valor')
    recaudo = fields.Float('Recaudo')
    fee = fields.Float('Tasa')
    bonding_date = fields.Date('Fecha de Negociación')
    redemption_date = fields.Date('Fecha de redencion')
    state_titulo = fields.Many2one('ati.state.titulo','Estado de titulo')
    responsable = fields.Many2one('res.partner','Responsable de proceso')
    state = fields.Selection(
        string='Status',
        store=True,
        selection=[
            ('draft', 'Borrador'),
            ('cancel', 'Cancelado'),
            ('confirmed', 'Confirmado')
        ],
    )

class TitulosHijos(models.Model):
    _name = 'ati.titulo.son'

    name = fields.Many2one('ati.titulo', 'Hijos')
    parent_id = fields.Many2one('ati.titulo', 'Padre')

class EliminarHistoricos(models.Model):
    _name = 'eliminar.historicos'

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
    manager = fields.Many2one('ati.gestor', 'Gestor', required=True)
    eliminados = fields.Text('Eliminados')

    def btn_delete(self):
        _eliminados = ""
        self.ensure_one()
        if not self.delimiter:
            raise ValidationError('Debe ingresar el delimitador')
        if not self.client_file:
            raise ValidationError('Debe seleccionar el archivo')
        if self.state != 'sin_eliminar':
            raise ValidationError('Archivo procesado!')
        if not self.month and not self.year:
            raise ValidationError('Debe introducir un mes y año de periodo para este cargue')
        if not self.manager:
            raise ValidationError('Debe introducir un gestor para este cargue')

        self.file_content = base64.decodebytes(self.client_file)
        lines = self.file_content.split('\r')

        for i,line in enumerate(lines):
            new_record = None
            if self.skip_first_line and i == 0:
                continue
            raise ValidationError('Error: {0}'.format(line))
            lista = line.split(self.delimiter)

            try:
                titulo_name = lista[0]
                cliente = lista[1]
                nit = lista[2]
                titulo_id = lista[3]
                titulo_historico = self.env['ati.titulo.historico'].search(
                    [('id', '=', titulo_id)], limit=1)
                titulo_historico.unlink()
                _eliminados += "{0};{1};{2};{3}\n".format(titulo_name, cliente, nit, titulo_id)


            except Exception as e:
                raise ValidationError('Error: {0}, Línea: {1}'.format(e, lista))

        self.eliminados = _eliminados
        self.state = 'eliminados'
        self.responsible = self.env.user.partner_id
