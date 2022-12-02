 # -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class AtiExtractoInherit(models.Model):
    _inherit = "ati.extracto"

    @api.model
    def create(self, vals):
        
        res = super(AtiExtractoInherit, self).create(vals)
        
        #Agregamos al cliente como seguidor
        add_user_as_follower = self.env['mail.followers'].sudo().create({
                'partner_id': res.cliente.id,
                'res_model': 'ati.extracto',
                'res_id': res.id,
                'subtype_ids': [1, 3, 18, 19]
            })
        #Agregamos al Representante Legal como seguidor
        if res.cliente.rep_legal:
            add_user_as_follower = self.env['mail.followers'].sudo().create({
                'partner_id': res.cliente.rep_legal.id,
                'res_model': 'ati.extracto',
                'res_id': res.id,
                'subtype_ids': [1, 3, 18, 19]
            })
        #Agregamos al Contacto en cuantum como seguidor
        if res.cliente.cuantum_contact:
            add_user_as_follower = self.env['mail.followers'].sudo().create({
                'partner_id': res.cliente.cuantum_contact.id,
                'res_model': 'ati.extracto',
                'res_id': res.id,
                'subtype_ids': [1, 3, 18, 19]
            })
            
        
        return res