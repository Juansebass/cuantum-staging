# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = "res.partner"
    tasa_rendimiento_fcl = fields.Float('Tasa Rendimiento')
    tasa_rendimiento_csf = fields.Float('Tasa Rendimiento')

    # Sobreescribimos esta funcion para que no se envie el vat a los contactos hijos de una empresa, esta funcion es del core de odoo en /odoo/addons/base/models/res_partner.py
    def _commercial_sync_from_company(self):
        """ Handle sync of commercial fields when a new parent commercial entity is set,
        as if they were related fields """
        commercial_partner = self.commercial_partner_id
        if commercial_partner != self:
            sync_vals = commercial_partner._update_fields_values(self._commercial_fields())
            _logger.warning('*********** Eliminamos vat de los parametros a enviar al contacto hijo ')
            sync_vals.pop('vat')
            self.write(sync_vals)

    @api.depends('recursos_recompra_fcp_ids')
    def _compute_totales_fcp(self):
        for rec in self:
            rec.compra_fcp = sum(ladicion['value'] for ladicion in rec.recursos_recompra_fcp_ids.filtered(lambda x: x.movement_type.code == 'COMPRA'))
            rec.retiro_fcp = sum(ladicion['value'] for ladicion in rec.recursos_recompra_fcp_ids.filtered(lambda x: x.movement_type.code == 'RETIRO'))
            rec.adicion_fcp = sum(ladicion['value'] for ladicion in rec.recursos_recompra_fcp_ids.filtered(lambda x: x.movement_type.code == 'APORTE'))
            rec.rendimiento_fcp = sum(ladicion['value'] for ladicion in rec.recursos_recompra_fcp_ids.filtered(lambda x: x.movement_type.code == 'RENDIMIENTO'))
            rec.aplicacion_recaudo_fcp = sum(ladicion['value'] for ladicion in rec.recursos_recompra_fcp_ids.filtered(lambda x: x.movement_type.code == 'APLICACION'))
            rec.total_fcp = sum([rec.adicion_fcp,rec.aplicacion_recaudo_fcp,rec.rendimiento_fcp]) - sum([rec.compra_fcp,rec.retiro_fcp])

    @api.depends('recursos_recompra_fcl_ids')
    def _compute_totales_fcl(self):
        for rec in self:
            rec.compra_fcl = sum(ladicion['value'] for ladicion in rec.recursos_recompra_fcl_ids.filtered(lambda x: x.movement_type.code == 'COMPRA'))
            rec.retiro_fcl = sum(ladicion['value'] for ladicion in rec.recursos_recompra_fcl_ids.filtered(lambda x: x.movement_type.code == 'RETIRO'))
            rec.adicion_fcl = sum(ladicion['value'] for ladicion in rec.recursos_recompra_fcl_ids.filtered(lambda x: x.movement_type.code == 'APORTE'))
            rec.aplicacion_recaudo_fcl = sum(ladicion['value'] for ladicion in rec.recursos_recompra_fcl_ids.filtered(lambda x: x.movement_type.code == 'APLICACION'))
            rec.rendimiento_fcl = sum(ladicion['value'] for ladicion in rec.recursos_recompra_fcl_ids.filtered(lambda x: x.movement_type.code == 'RENDIMIENTO'))
            rec.total_fcl = sum([rec.adicion_fcl,rec.aplicacion_recaudo_fcl,rec.rendimiento_fcl]) - sum([rec.compra_fcl,rec.retiro_fcl])
    
    @api.depends('recursos_recompra_csf_ids')
    def _compute_totales_csf(self):
        for rec in self:
            #Factoring
            rec.compra_fac_csf = sum(ladicion['value'] for ladicion in rec.recursos_recompra_csf_ids.filtered(lambda x: x.movement_type.code == 'COMPRA' and x.investment_type.code == 'FAC'))
            rec.aplicacion_fac_recaudo_csf = sum(ladicion['value'] for ladicion in rec.recursos_recompra_csf_ids.filtered(lambda x: x.movement_type.code == 'APLICACION' and x.investment_type.code == 'FAC'))
            rec.total_fac_csf = sum([rec.aplicacion_fac_recaudo_csf]) - sum([rec.compra_fac_csf])
            #Libraznas
            rec.compra_lib_csf = sum(ladicion['value'] for ladicion in rec.recursos_recompra_csf_ids.filtered(lambda x: x.movement_type.code == 'COMPRA' and x.investment_type.code == 'LIB'))
            rec.aplicacion_lib_recaudo_csf = sum(ladicion['value'] for ladicion in rec.recursos_recompra_csf_ids.filtered(lambda x: x.movement_type.code == 'APLICACION' and x.investment_type.code == 'LIB'))
            rec.total_lib_csf = sum([rec.aplicacion_lib_recaudo_csf]) - sum([rec.compra_lib_csf])
            #Sentencias
            rec.compra_sen_csf = sum(ladicion['value'] for ladicion in rec.recursos_recompra_csf_ids.filtered(lambda x: x.movement_type.code == 'COMPRA' and x.investment_type.code == 'SEN'))
            rec.aplicacion_sen_recaudo_csf = sum(ladicion['value'] for ladicion in rec.recursos_recompra_csf_ids.filtered(lambda x: x.movement_type.code == 'APLICACION' and x.investment_type.code == 'SEN'))
            rec.total_sen_csf = sum([rec.aplicacion_sen_recaudo_csf]) - sum([rec.compra_sen_csf])
            #Mutuos
            rec.compra_mut_csf = sum(ladicion['value'] for ladicion in rec.recursos_recompra_csf_ids.filtered(lambda x: x.movement_type.code == 'COMPRA' and x.investment_type.code == 'MUT'))
            rec.aplicacion_mut_recaudo_csf = sum(ladicion['value'] for ladicion in rec.recursos_recompra_csf_ids.filtered(lambda x: x.movement_type.code == 'APLICACION' and x.investment_type.code == 'MUT'))
            rec.total_mut_csf = sum([rec.aplicacion_mut_recaudo_csf]) - sum([rec.compra_mut_csf])

            #TOTALES
            rec.retiro_total_csf = sum(ladicion['value'] for ladicion in rec.recursos_recompra_csf_ids.filtered(lambda x: x.movement_type.code == 'RETIRO'))
            rec.adicion_total_csf = sum(ladicion['value'] for ladicion in rec.recursos_recompra_csf_ids.filtered(lambda x: x.movement_type.code == 'APORTE'))
            rec.rendimiento_total_csf = sum(ladicion['value'] for ladicion in rec.recursos_recompra_csf_ids.filtered(lambda x: x.movement_type.code == 'RENDIMIENTO'))
            rec.total_csf = sum([rec.total_mut_csf,rec.total_sen_csf,rec.total_lib_csf,rec.total_fac_csf, rec.adicion_total_csf, rec.rendimiento_total_csf]) - rec.retiro_total_csf

    #Campos informativos
    rep_legal = fields.Many2one('res.partner','Representante Legal')
    cuantum_contact = fields.Many2one('res.partner','Contacto')
    freelance = fields.Many2one('res.partner','Freelance')
    num_encargo = fields.Char('Nº de encargo')

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
    recursos_recompra_fcp_ids = fields.One2many('ati.recurso.recompra.fcp','buyer','Recuros de recompra FCP')
    recursos_recompra_csf_ids = fields.One2many('ati.recurso.recompra.csf','buyer','Recuros de recompra CSF')
    #TOTALES FCP
    compra_fcp = fields.Float('Total Compra', compute=_compute_totales_fcp)
    retiro_fcp = fields.Float('Total Retiro', compute=_compute_totales_fcp)
    adicion_fcp = fields.Float('Total Adicion', compute=_compute_totales_fcp)
    aplicacion_recaudo_fcp = fields.Float('Total A. de Recuado', compute=_compute_totales_fcp)
    rendimiento_fcp = fields.Float('Total Rendimiento', compute=_compute_totales_fcp)
    total_fcp = fields.Float('Total FCL', compute=_compute_totales_fcp)
    #TOTALES FCL
    compra_fcl = fields.Float('Total Compra', compute=_compute_totales_fcl)
    retiro_fcl = fields.Float('Total Retiro', compute=_compute_totales_fcl)
    adicion_fcl = fields.Float('Total Adicion', compute=_compute_totales_fcl)
    aplicacion_recaudo_fcl = fields.Float('Total A. de Recuado', compute=_compute_totales_fcl)
    rendimiento_fcl = fields.Float('Total Rendimiento', compute=_compute_totales_fcl)
    total_fcl = fields.Float('Total FCL', compute=_compute_totales_fcl)
    #TOTALES CSF
    total_csf = fields.Float('Total CSF', compute=_compute_totales_csf)
    adicion_total_csf = fields.Float('Total Adicion CSF', compute=_compute_totales_csf)
    retiro_total_csf = fields.Float('Total Retiro CSF', compute=_compute_totales_csf)
    rendimiento_total_csf = fields.Float('Total Rendimiento CSF', compute=_compute_totales_csf)
    #-Factoring CSF
    compra_fac_csf = fields.Float('Total Compra', compute=_compute_totales_csf)
    aplicacion_fac_recaudo_csf = fields.Float('Total A. de Recuado', compute=_compute_totales_csf)
    total_fac_csf = fields.Float('Total Factoring CSF', compute=_compute_totales_csf)
    #-Libranzas CSF
    compra_lib_csf = fields.Float('Total Compra', compute=_compute_totales_csf)
    aplicacion_lib_recaudo_csf = fields.Float('Total A. de Recuado', compute=_compute_totales_csf)
    total_lib_csf = fields.Float('Total Libranzas CSF', compute=_compute_totales_csf)
    #-Sentencias CSF
    compra_sen_csf = fields.Float('Total Compra', compute=_compute_totales_csf)
    aplicacion_sen_recaudo_csf = fields.Float('Total A. de Recuado', compute=_compute_totales_csf)
    total_sen_csf = fields.Float('Total Sentencias CSF', compute=_compute_totales_csf)
    #-Mutuos CSF
    compra_mut_csf = fields.Float('Total Compra', compute=_compute_totales_csf)
    aplicacion_mut_recaudo_csf = fields.Float('Total A. de Recuado', compute=_compute_totales_csf)
    total_mut_csf = fields.Float('Total Mutuos CSF', compute=_compute_totales_csf)

    def enviar_calificado_crm(self):
        for rec in self:
            if rec.doc_enviada and rec.documentacion_completa and rec.busqueda_lista and rec.vinculado:
                _leads = self.env['crm.lead'].search([('partner_id','=',rec.id),('stage_id.name','=','Riesgos')])
                _stage = self.env['crm.stage'].search([('name','=','Calificado')],limit=1)
                for lead in _leads:
                    lead.sudo().stage_id = _stage
            else:
                raise ValidationError("No puede aprobar oportunidades si los siguientes campos no fueron validados: Vinculado, Documentacion enviada, Documentacion completa, Busqueda en listas")
