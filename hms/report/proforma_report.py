from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from dateutil.relativedelta import relativedelta
from dateutil import parser
from odoo import api, fields, models


# class ProformaReport(models.AbstractModel):
#     """
#         Abstract Model specially for report template.
#         _name = Use prefix `report.` along with `module_name.report_name`
#     """
#     _name = 'report.hms.report_hms_pro_forma'
#     _description = 'Proforma Report'

#     # def get_reservation_list(self, property_id, date_start, date_end):
#     #     reservation_line_obj = self.env['hms.reservation.line'].search([
#     #         ('property_id', '=', property_id[0]),
#     #         ('arrival', '>=', date_start), ('departure', '<=', date_end)
#     #     ])
#     #     return reservation_line_obj

#     @api.model
#     def _get_report_values(self, docids, data=None):
#         self.model = self.env.context.get('active_model')
#         if data is None:
#             data = {}
#         if not docids:
#             docids = data.get('ids', data.get('active_ids'))

#         rsvn_line_id = data['form']['rsvn_line_id']

#         trans_lines = self.env['hms.room.transaction.charge.line'].search([('reservation_line_id', '=', rsvn_line_id[0])])
#         return {
#             'doc_ids': docids,
#             'doc_model': 'hms.reservation.line',
#             # 'data': data['form'],
#             # 'date_start': date_start,
#             # 'date_end': date_end,
#             # 'property_id': property_id[1],
#             'docs': trans_lines,
#             # 'time': time,
#             # 'get_reservation_list': get_reservation_list,
#         }


class ProformaReport(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.hms.report_hms_pro_forma'
    _description = 'Proforma Report'

    def get_rsvn_line(self, rsvn_line_id):
        rsvn_line_obj = self.env['hms.reservation.line'].search([('id', '=',
                                                         rsvn_line_id[0])])
        return rsvn_line_obj

    @api.model
    def _get_report_values(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        if data is None:
            data = {}
        if not docids:
            docids = data.get('ids', data.get('active_ids'))

        rsvn_line_id = data['form']['rsvn_line_id']
        # folio_profile = self.env['hms.property'].search([('id', '=',
        #                                                   rsvn_line_id[0])])
        rsvn_line = self.env['hms.reservation.line'].search([('id', '=', rsvn_line_id[0])])
        trans_lines = self.env['hms.room.transaction.charge.line'].search([('reservation_line_id', '=', rsvn_line_id[0])])
        rm_act = self.with_context(data['form'].get('used_context', {}))
        get_rsvn_line = rm_act.get_rsvn_line(rsvn_line_id)

        return {
            'doc_ids': docids,
            'doc_model': 'hms.reservation.line',
            # 'data': data['form'],
            'rsvn_line_id': rsvn_line_id[1],
            'docs': rsvn_line,
            'get_rsvn_line': get_rsvn_line,
        }
          