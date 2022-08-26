# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

class CrmStage(models.Model):
    _inherit = "crm.stage"

    #Campo utilizado para determinar a que otras etapas en crm puede pasar
    stages_available_ids = fields.One2many('crm.stage.stages.available','stage_id',string="Siguientes etapas disponibles")

class StageAvailable(models.Model):
    _name = "crm.stage.stages.available"

    stage = fields.Many2one('crm.stage','Etapa')
    stage_id = fields.Many2one('crm.stage','Etapa')