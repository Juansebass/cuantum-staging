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

    # Se verifica si los productos de la oferta son distintos, de ser asi se avisa que solo se puede tener un solo tipo y se cancela la accion
    @api.onchange('order_line')
    def on_change_order_line_restriccion_producto(self):
        for rec in self:
            if len(rec.order_line) > 0:
                for ol in rec.order_line:
                    if ol.product_id.id != rec.order_line[0].product_id.id:
                        raise ValidationError('Solo puedes ofrecer productos del mismo tipo en una Oferta')

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    emisor_line = fields.Many2one('res.partner','Emisor')
    pagador_line = fields.Many2one('res.partner','Pagador')
    plazo_pago = fields.Date('Plazo Estimado')
    taza_retorno = fields.Float('Tasa Estimada')
    gestor_line = fields.Many2one('ati.gestor','Gestor')
    n_titulo = fields.Char('Nº Titulo')
    reserva = fields.Float('Reserva')