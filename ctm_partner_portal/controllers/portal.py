from odoo import http  # type: ignore
from odoo.addons.portal.controllers.portal import CustomerPortal  # type: ignore


class CustomCustomerPortal(CustomerPortal):

    @http.route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        self.OPTIONAL_BILLING_FIELDS += [
            'ingresos_mensuales',
            'gastos_mensuales',
            'document_file',
        ]
        response = super(CustomCustomerPortal, self).account(redirect=redirect, **post)
        return response
