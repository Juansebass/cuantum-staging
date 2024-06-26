 # -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class SaleOrderInherit(models.Model):
    _inherit = "sale.order"

    @api.model
    def create(self, vals):
        
        res = super(SaleOrderInherit, self).create(vals)
        
        #Agregamos al cliente como seguidor
        add_user_as_follower = self.env['mail.followers'].sudo().create({
                'partner_id': res.partner_id.id,
                'res_model': 'sale.order',
                'res_id': res.id,
                'subtype_ids': [1, 3, 18, 19]
            })
        #Agregamos al Representante Legal como seguidor
        if res.partner_id.rep_legal:
            add_user_as_follower = self.env['mail.followers'].sudo().create({
                'partner_id': res.partner_id.rep_legal.id,
                'res_model': 'sale.order',
                'res_id': res.id,
                'subtype_ids': [1, 3, 18, 19]
            })
        #Agregamos al Contacto en cuantum como seguidor
        if res.partner_id.cuantum_contact:
            add_user_as_follower = self.env['mail.followers'].sudo().create({
                'partner_id': res.partner_id.cuantum_contact.id,
                'res_model': 'sale.order',
                'res_id': res.id,
                'subtype_ids': [1, 3, 18, 19]
            })
            
        
        return res

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        duplicated = super().copy(default)
        duplicated.env['mail.followers'].sudo().search([
            ('partner_id', '=', self.partner_id.id),
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', duplicated.id)
        ]).unlink()
        return super().copy(default)
