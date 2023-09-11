from odoo import api, models, fields


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    notify_followers = fields.Boolean('Destinatarios', default=True)