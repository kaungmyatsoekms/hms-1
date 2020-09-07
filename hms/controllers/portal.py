# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from odoo.http import request


class PortalAccount(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(PortalAccount, self)._prepare_portal_layout_values()
        invoice_count = request.env['hms.reservation.line'].search_count([
            ('state', 'in', ('booking', 'reservation', 'confirm', 'cancel', 'checkin')),
        ])
        values['invoice_count'] = invoice_count
        return values

    def _invoice_get_page_view_values(self, invoice, access_token, **kwargs):
        values = {
            'page_name': 'proforma',
            'reservations': invoice,
        }
        return self._get_page_view_values(invoice, access_token, values, 'my_proforma_history', False, **kwargs)

    @http.route(['/my/reservations', '/my/reservations/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_proforma_invoices(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        ProformaInvoice = request.env['hms.reservation.line']

        domain = [('state', 'in', ('booking', 'reservation', 'confirm', 'checkin', 'cancel'))]

        searchbar_sortings = {
            'date': {'label': _('Invoice Date'), 'order': 'system_date desc'},
            'duedate': {'label': _('Due Date'), 'order': 'system_date desc'},
            'name': {'label': _('Reference'), 'order': 'confirm_no desc'},
            'state': {'label': _('Status'), 'order': 'state'},
        }
        # default sort by order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups('hms.reservation.line', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        invoice_count = ProformaInvoice.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/reservations",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=invoice_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        invoices = ProformaInvoice.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_proforma_history'] = invoices.ids[:100]

        values.update({
            'date': date_begin,
            'invoices': invoices,
            'page_name': 'proforma',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/reservations',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("hms.portal_my_invoices", values)

    @http.route(['/my/reservations/<int:line_id>'], type='http', auth="public", website=True)
    def portal_my_invoice_detail(self, line_id, access_token=None, report_type=None, download=False, **kw):
        try:
            rsvn_line_sudo = self._document_check_access('hms.reservation.line', line_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=rsvn_line_sudo, report_type=report_type, report_ref='hms.proforma_report_id', download=download)

        values = self._invoice_get_page_view_values(rsvn_line_sudo, access_token, **kw)
        acquirers = values.get('acquirers')
        if acquirers:
            country_id = values.get('partner_id') and values.get('partner_id')[0].country_id.id
            values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(rsvn_line_sudo.amount_residual, rsvn_line_sudo.currency_id, country_id)

        return request.render("hms.portal_proforma_page", values)

    def _invoice_get_page_values(self, invoice, access_token, **kwargs):
        values = {
            'page_name': 'group_proforma',
            'reservation': invoice,
        }
        return self._get_page_view_values(invoice, access_token, values, 'my_proforma_history', False, **kwargs)

    @http.route(['/my/reservation/<int:line_id>'], type='http', auth="public", website=True)
    def portal_my_proforma_invoice_detail(self, line_id, access_token=None, report_type=None, download=False, **kw):
        try:
            rsvn_line_sudo = self._document_check_access('hms.reservation', line_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=rsvn_line_sudo, report_type=report_type, report_ref='hms.group_proforma_report_id', download=download)

        values = self._invoice_get_page_values(rsvn_line_sudo, access_token, **kw)
        acquirers = values.get('acquirers')
        if acquirers:
            country_id = values.get('partner_id') and values.get('partner_id')[0].country_id.id
            values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(rsvn_line_sudo.amount_residual, rsvn_line_sudo.currency_id, country_id)

        return request.render("hms.portal_group_proforma_page", values)