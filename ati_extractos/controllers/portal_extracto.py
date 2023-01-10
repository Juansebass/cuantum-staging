from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.exceptions import AccessError, MissingError
import logging

_logger = logging.getLogger(__name__)

class ExtractoCustomperPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'count_extracto' in counters:
            partner = request.env.user.partner_id
            values['count_extracto'] = request.env['ati.extracto'].search_count([ ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['send'])])
        return values

    def _prepare_extracto_domain(self, partner):
        return [
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['send'])
        ]

    @http.route(['/my/extracto', '/my/extracto/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_extracto(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Extracto = request.env['ati.extracto']

        domain = self._prepare_extracto_domain(partner)

        #searchbar_sortings = self._get_sale_searchbar_sortings()

        # default sortby order
        #if not sortby:
        #    sortby = 'date'
        #sort_order = searchbar_sortings[sortby]['order']
#
        #if date_begin and date_end:
        #    domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        extracto_count = Extracto.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/extracto",
            #url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=extracto_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        extractos = Extracto.search(domain, limit=self._items_per_page, offset=pager['offset'])
        _logger.warning('***** extractos: {0}'.format(extractos))
        request.session['my_extractos_history'] = extractos.ids[:100]

        values.update({
            'date': date_begin,
            'extractos': extractos.sudo(),
            'page_name': 'extracto',
            'pager': pager,
            'default_url': '/my/extracto',
            #'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("ati_extractos.portal_my_extracto", values)

    @http.route(['/my/extracto/<int:extracto_id>'], type='http', auth="public", website=True)
    def portal_extracto_page(self, extracto_id, report_type=None, access_token=None, message=False, download=False, **kw):
        try:
            order_sudo = self._document_check_access('ati.extracto', extracto_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=order_sudo, report_type=report_type, report_ref='ati_extractos.report_ati_extracto', download=download)

        