# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.depends('recursos_recompra_fcl_ids')
    def _compute_totales_fcl(self):
        for rec in self:
            rec.compra_fcl = sum(ladicion['value'] for ladicion in rec.recursos_recompra_fcl_ids.filtered(lambda x: x.movement_type.code == 'COMPRA'))
            rec.retiro_fcl = sum(ladicion['value'] for ladicion in rec.recursos_recompra_fcl_ids.filtered(lambda x: x.movement_type.code == 'RETIRO'))
            rec.adicion_fcl = sum(ladicion['value'] for ladicion in rec.recursos_recompra_fcl_ids.filtered(lambda x: x.movement_type.code == 'APORTE'))
            rec.aplicacion_recaudo_fcl = sum(ladicion['value'] for ladicion in rec.recursos_recompra_fcl_ids.filtered(lambda x: x.movement_type.code == 'APLICACION'))
            rec.total_fcl = sum([rec.adicion_fcl,rec.aplicacion_recaudo_fcl]) - sum([rec.compra_fcl,rec.retiro_fcl])
    
    @api.depends('recursos_recompra_csf_ids')
    def _compute_totales_csf(self):
        for rec in self:
            rec.compra_csf = sum(ladicion['value'] for ladicion in rec.recursos_recompra_csf_ids.filtered(lambda x: x.movement_type.code == 'COMPRA'))
            rec.retiro_csf = sum(ladicion['value'] for ladicion in rec.recursos_recompra_csf_ids.filtered(lambda x: x.movement_type.code == 'RETIRO'))
            rec.adicion_csf = sum(ladicion['value'] for ladicion in rec.recursos_recompra_csf_ids.filtered(lambda x: x.movement_type.code == 'APORTE'))
            rec.aplicacion_recaudo_csf = sum(ladicion['value'] for ladicion in rec.recursos_recompra_csf_ids.filtered(lambda x: x.movement_type.code == 'APLICACION'))
            rec.total_csf = sum([rec.adicion_csf,rec.aplicacion_recaudo_csf]) - sum([rec.compra_csf,rec.retiro_csf])

    #Campos informativos
    rep_legal = fields.Many2one('res.partner','Representante Legal')
    cuantum_contact = fields.Many2one('res.partner','Contacto')
    freelance = fields.Many2one('res.partner','Freelance')

    #Emisor / Pagador
    emisor = fields.Boolean('Emisor',default=False)
    pagador = fields.Boolean('Pagador',default=False)

    #Variable utilizada para confirmar la vinculacion por el departamento de legales
    vinculado = fields.Boolean('Vinculado',default=False)
    #Variable utilizada para verificacion si el cliente esta activo o inactivo
    act_in = fields.Selection([ ('activo', 'Activo'),('inactivo', 'Inactivo'),],'Estado',default='inactivo')

    #RIESGOS
    #Variable para confirmar que la documentacion para una posible vinculacion con el cliente fue enviada
    doc_enviada = fields.Boolean('Documentacion enviada', default=False)
    documentacion_completa = fields.Boolean('Documentacion completa', default=False)
    busqueda_lista = fields.Boolean('Busqueda en listas', default=False)
    nota_riesgos = fields.Text('Notas extras')

    #Recursos de recompra
    recursos_recompra_fcl_ids = fields.One2many('ati.recurso.recompra.fcl','buyer','Recuros de recompra FCL')
    recursos_recompra_csf_ids = fields.One2many('ati.recurso.recompra.csf','buyer','Recuros de recompra CSF')
    #TOTALE FCL
    compra_fcl = fields.Float('Total Compra', compute=_compute_totales_fcl)
    retiro_fcl = fields.Float('Total Retiro', compute=_compute_totales_fcl)
    adicion_fcl = fields.Float('Total Adicion', compute=_compute_totales_fcl)
    aplicacion_recaudo_fcl = fields.Float('Total A. de Recuado', compute=_compute_totales_fcl)
    total_fcl = fields.Float('Total FCL', compute=_compute_totales_fcl)
    #TOTALE CSF
    compra_csf = fields.Float('Total Compra', compute=_compute_totales_csf)
    retiro_csf = fields.Float('Total Retiro', compute=_compute_totales_csf)
    adicion_csf = fields.Float('Total Adicion', compute=_compute_totales_csf)
    aplicacion_recaudo_csf = fields.Float('Total A. de Recuado', compute=_compute_totales_csf)
    total_csf = fields.Float('Total CSF', compute=_compute_totales_csf)

    def enviar_calificado_crm(self):
        for rec in self:
            if rec.doc_enviada and rec.documentacion_completa and rec.busqueda_lista and rec.vinculado:
                _leads = self.env['crm.lead'].search([('partner_id','=',rec.id),('stage_id.name','=','Riesgos')])
                _stage = self.env['crm.stage'].search([('name','=','Calificado')],limit=1)
                for lead in _leads:
                    lead.stage_id = _stage
            else:
                raise ValidationError("No puede aprobar oportunidades si los siguientes campos no fueron validados: Vinculado, Documentacion enviada, Documentacion completa, Busqueda en listas")
