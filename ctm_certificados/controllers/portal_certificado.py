from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request
from odoo import http
from odoo.exceptions import AccessError, MissingError


class CertificadoCustomperPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'count_certificado' in counters:
            partner = request.env.user.partner_id
            values['count_certificado'] = request.env['ctm.certificado'].search_count(
                self._get_certificado_domain()
            )
        return values

    def _get_certificado_domain(self):
        """ Checking domain"""
        return [('cliente', '=', request.env.user.partner_id.id), ('state', '=', 'processed')]

    @http.route(['/my/certificates'], type='http', auth="user", website=True)
    def portal_my_certificates(self):
        """Displays a list of certificates for the current user in the user's
        portal."""
        domain = self._get_certificado_domain()
        certificates = request.env['ctm.certificado'].search(domain)
        values = {
            'default_url': "/my/certificates",
            'certificates': certificates,
            'page_name': 'certificate',
        }
        return request.render("ctm_certificados.portal_my_certificates",
                              values)

    @http.route(['/my/certificate/<int:certificate_id>'], type='http', auth="public", website=True)
    def portal_certificate_page(self, certificate_id, report_type=None, access_token=None, message=False, download=False,
                             **kw):
        try:
            order_sudo = self._document_check_access('ctm.certificado', certificate_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=order_sudo, report_type=report_type,
                                     report_ref='ctm_certificados.report_comprador', download=download)
