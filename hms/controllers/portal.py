# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from odoo.http import request


class PortalAccount(CustomerPortal):

    def _invoice_get_page_view_values(self, invoice, access_token, **kwargs):
        values = {
            'page_name': 'proforma',
            'reservations': invoice,
        }
        return self._get_page_view_values(invoice, access_token, values, 'my_invoices_history', False, **kwargs)

    @http.route(['/my/reservations/<int:line_id>'], type='http', auth="public", website=True)
    def portal_my_invoice_detail(self, line_id, access_token=None, report_type=None, download=False, **kw):
        try:
            rsvn_line_sudo = self._document_check_access('hms.reservation.line', line_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=rsvn_line_sudo, report_type=report_type, report_ref='hms.action_report_proforma', download=download)

        values = self._invoice_get_page_view_values(rsvn_line_sudo, access_token, **kw)
        acquirers = values.get('acquirers')
        if acquirers:
            country_id = values.get('partner_id') and values.get('partner_id')[0].country_id.id
            values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(rsvn_line_sudo.amount_residual, rsvn_line_sudo.currency_id, country_id)

        return request.render("hms.portal_proforma_page", values)