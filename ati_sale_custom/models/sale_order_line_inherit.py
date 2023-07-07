# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    offer_type = fields.Selection(
        string='Tipo de Oferta',
        selection=[
            ('comprador', 'Comprador'),
            ('activo', 'Activo')
        ],
        default='comprador',
        required=True
    )

    #Variable utilizadas para cargar ofertas de titulos segun gestor y tipo de inversion
    gestor_ofertar = fields.Many2one('ati.gestor','Gestor de titulos')
    tipo_producto_ofertar = fields.Many2one('ati.investment.type','Tipo de producto')
    fecha_celebracion = fields.Datetime(string='Fecha de Celebración', index=True,
                                        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                        copy=False, default=fields.Datetime.now)
    emisor_ofertar = fields.Many2one('res.partner', 'Emisor')
    pagador_ofertar = fields.Many2one('res.partner', 'Pagador')

    def action_cargar_titulos_oferta(self):
        for rec in self:
            if len(rec.gestor_ofertar) < 1:
                raise ValidationError('Debe seleccionar un Gestor para poder cargar ofertas')
            elif len(rec.tipo_producto_ofertar) < 1:
                raise ValidationError('Debe seleccionar un Tipo de producto para poder cargar ofertas')
            elif rec.gestor_ofertar.code != 'FCL' and rec.tipo_producto_ofertar.code == 'LIB':
                raise ValidationError('Solo se puede ofrecer Libranzas con gestor FCL')

            ofertas = []
            if not rec.emisor_ofertar and not rec.pagador_ofertar:
                ofertas = self.env['ati.titulo.oferta'].search([
                    ('investment_type', '=', rec.tipo_producto_ofertar.id),
                    ('manager', '=', rec.gestor_ofertar.id),
                    ('odquirido', '=', False)
                ])
            elif not rec.emisor_ofertar and rec.pagador_ofertar:
                ofertas = self.env['ati.titulo.oferta'].search([
                    ('investment_type', '=', rec.tipo_producto_ofertar.id),
                    ('manager', '=', rec.gestor_ofertar.id),
                    ('payer', '=', rec.pagador_ofertar.id),
                    ('odquirido', '=', False)
                ])
            elif rec.emisor_ofertar and not rec.pagador_ofertar:
                ofertas = self.env['ati.titulo.oferta'].search([
                    ('investment_type', '=', rec.tipo_producto_ofertar.id),
                    ('manager', '=', rec.gestor_ofertar.id),
                    ('issuing', '=', rec.emisor_ofertar.id),
                    ('odquirido', '=', False)
                ])
            else:
                ofertas = self.env['ati.titulo.oferta'].search([
                    ('investment_type', '=', rec.tipo_producto_ofertar.id),
                    ('manager', '=', rec.gestor_ofertar.id),
                    ('issuing', '=', rec.emisor_ofertar.id),
                    ('payer', '=', rec.pagador_ofertar.id),
                    ('odquirido', '=', False)
                ])
            # Verificamos que existan ofertas, en el caso de existir las agregamos a las lineas
            if len(ofertas) == 0:
                raise ValidationError('El gestor {0} no tiene disponible Titulos de tipo {1}'.format(rec.gestor_ofertar.name, rec.tipo_producto_ofertar.name))
            
            producto = self.env['product.product']
            if rec.tipo_producto_ofertar.code == 'FAC':
                producto = self.env['product.product'].search([('name','=','Factoring')])
            elif rec.tipo_producto_ofertar.code == 'LIB':
                producto = self.env['product.product'].search([('name','=','Libranza')])
            elif rec.tipo_producto_ofertar.code == 'SEN':
                producto = self.env['product.product'].search([('name','=','Sentencias')])
            elif rec.tipo_producto_ofertar.code == 'MUT':
                producto = self.env['product.product'].search([('name','=','Mutuos')])
            
            for o in ofertas:
                rec.order_line = [(0,0,{
                    'emisor_line' : o.issuing.id,
                    'pagador_line' : o.payer.id,
                    'plazo_pago' : o.redemption_date,
                    'taza_retorno' : o.fee,
                    'gestor_line' : o.manager.id,
                    'n_titulo' : o.name,
                    'name' : o.name,
                    'titulo_oferta' : o.id,
                    'price_unit' : o.value,
                    'product_id' : producto.id
                })]
            
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for rec in self:
            
            #Recorremos todas las lineas para verificar si hay alguna linea asociada a un titulo de oferta (ati.titulo.oferta) y si las hay consultamos que ya no esten adquiridas
            for ol in rec.order_line:
                if len(ol.titulo_oferta) > 0:
                    if ol.titulo_oferta.odquirido:
                        raise ValidationError('El titulo {0} esta en estado de adquirido en Titulos de Oferta, no puedes validar un titulo que ya fue adquirido por alguien'.format(ol.titulo_oferta.name))
                    else:
                        ol.titulo_oferta.odquirido = True
                        ol.titulo_oferta.cliente = rec.partner_id.id
                # Agregando fecha de celebración a la orden
                self.date_order = self.fecha_celebracion
        return res

    # Se verifica si los productos de la oferta son distintos, de ser asi se avisa que solo se puede tener un solo tipo y se cancela la accion
    @api.onchange('order_line')
    def on_change_order_line_restriccion_producto(self):
        for rec in self:
            if len(rec.order_line) > 0:
                for ol in rec.order_line:
                    if ol.product_id.id != rec.order_line[0].product_id.id:
                        raise ValidationError('Solo puedes ofrecer productos del mismo tipo en una Oferta')


    def get_group_results_fcl(self):
        for rec in self:
            results = []
            ofertas = rec.order_line.filtered(
            lambda x: x.gestor_line.code == 'FCL').sorted(key=lambda x: int(x.emisor_line))

            dic_actual = {
                'originador': 'origi',
                'nit': 'nit',
                'cuenta': 'cuenta',
                'tipo': 'tipo',
                'banco': 'banco',
                'valor': 1000.13
            }
            results.append(dic_actual)
        return results

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    emisor_line = fields.Many2one('res.partner','Emisor')
    pagador_line = fields.Many2one('res.partner','Pagador')
    plazo_pago = fields.Date('Plazo Estimado')
    taza_retorno = fields.Float('Tasa Estimada')
    gestor_line = fields.Many2one('ati.gestor','Gestor')
    n_titulo = fields.Char('Nº Titulo')
    reserva = fields.Float('Reserva')
    titulo_oferta = fields.Many2one('ati.titulo.oferta','Titulo oferta')