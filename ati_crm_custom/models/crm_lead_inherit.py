# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

class CrmLead(models.Model):
    _inherit = "crm.lead"

    @api.depends('stage_id')
    def compute_stage_name(self):
        for rec in self:
            rec.stage_name = rec.stage_id.name
        pass

    user_id = fields.Many2one(
        'res.users', string='Salesperson', default= False,
        domain="['&', ('share', '=', False), ('company_ids', 'in', user_company_ids)]",
        check_company=True, index=True, tracking=True)

    #Variable utilizada para dominios en busquedas
    stage_name = fields.Char(compute=compute_stage_name, store=True)

    recursos_girados = fields.Boolean('Se giraron recursos',default=False)
    acepto_oferta = fields.Boolean('Se acepto oferta',default=False)

    #Enviar a riesgos
    def enviar_riesgos(self):
        for rec in self:
            if len(rec.partner_id) < 1:
                raise ValidationError("Debes seleccionar un cliente en la oportunidad para que se envíe el cliente y la oportunidad al análisis de riesgo")
            elif rec.partner_id.vinculado == True:
                raise ValidationError("El cliente ya tiene verificada su vinculación a Cuantum en su formulario, si crees que esta información es incorrecta, revísalo y verifícalo con un supervisor")
            rec.partner_id.doc_enviada = True
            _stage = self.env['crm.stage'].search([('name','=','Riesgos')])
            rec.stage_id = _stage
        return

    def write(self, values):
        #Verifico por medio de la etapa si es valido a la nueva etapa que se esta pasando, para esto usamos el campo stages_available_ids
        # que es donde se guardan las etapa a la que puede pasar cada una.
        if 'stage_id' in values:
            _cambio_valido = False
            _logger.warning('***** values: {0}'.format(values))
            _logger.warning('***** self.stage_id.stages_available_ids: {0}'.format(self.stage_id.id))
            for s in self.stage_id.stages_available_ids:
                if s.stage.id == values['stage_id']:
                    _cambio_valido = True

            if not _cambio_valido:
                raise ValidationError('No es una nueva estapa valida para la oportunidad ' + self.name)

        # Verificamos si se giraron recursos y si se acepto oferta, de ser asi damos por ganada la oportunidad
        if 'recursos_girados' in values or 'acepto_oferta' in values:
            etapa_ganadora = self.env['crm.stage'].search([('is_won','=',True)])
            if 'recursos_girados' in values:
                if values['recursos_girados'] == True and self.acepto_oferta:
                    values['stage_id'] = etapa_ganadora.id
            elif 'acepto_oferta' in values:
                if values['acepto_oferta'] == True and self.recursos_girados:
                    values['stage_id'] = etapa_ganadora.id

        return super(CrmLead, self).write(values)

    # Verificamos si el cliente tine vinculacion entonces se crea la oportunidad directamente sobre el estado Oferta
    @api.model
    def create(self,vals):
        if vals['partner_id']:
            partner_tmp = self.env['res.partner'].browse(vals['partner_id'])
            stage_tmp = self.env['crm.stage'].search([('name','=','Oferta')])
            if partner_tmp.vinculado:
                vals['stage_id'] = stage_tmp.id
        return super(CrmLead, self).create(vals)
        
        #TODO revisar si se puede enviar notificacion
        #  {
        #   'type': 'ir.actions.client',
        #   'tag': 'display_notification',
        #   'params': {
        #       'message': 'Hola',
        #       'type': 'success',
        #       'sticky': False,
        #   }
        #}