# -*- coding: utf-8 -*-

from odoo import models
import logging
_logger = logging.getLogger(__name__)


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    #Al enviar la oferta el cliente si esta oferta tiene relacion con un lead este lead cambiara de etapa de 'Calificado' a 'Oferta'
    def _action_send_mail(self, auto_commit=False):
        if self.model == 'sale.order':
            self = self.with_context(mailing_document_based=True)
            if self.env.context.get('mark_so_as_sent'):
                so = self.env['sale.order'].search([('id','=',self.res_id)])
                lead = so.opportunity_id
                if len(lead) > 0:
                    if lead.stage_id.name == 'Calificado':
                        _stage = self.env['crm.stage'].search([('name','=','Oferta')])
                        if len(_stage) > 0:
                            lead.stage_id = _stage
                self = self.with_context(mail_notify_author=self.env.user.partner_id in self.partner_ids)
        return super(MailComposeMessage, self)._action_send_mail(auto_commit=auto_commit)