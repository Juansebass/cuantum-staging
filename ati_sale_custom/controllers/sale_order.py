# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class SaleOrderFunctions(http.Controller):
    @http.route('/aceptar-oferta/<int:_id>/<string:rating>', type='http', auth='none')
    def approve_offer(self, _id, rating, **kwargs):
        assert rating in ('True', 'False'), "Aprobación de Oferta Erronea"
        sale_id = request.env['sale.order'].sudo().search([('id', '=', _id), ], limit=1)
        if not sale_id:
            return request.not_found()

        if rating == 'True':
            rating_system = 'aceptada'
            sale_id.write({'estado_oferta_fcl': rating_system})
        elif rating == 'False':
            rating_system = 'rechazada'
            sale_id.write({'estado_oferta_fcl': rating_system})
        else:
            return request.render('ati_sale_custom.offer_rating_refuse', {
                'rating': 'Valide el valor de aprobacion enviado',
                'sale': _id,
                'id': _id,
            })

        return request.render('ati_sale_custom.approve_offer_messages', {
            'rating': rating_system,
            'sale': sale_id,
        })


