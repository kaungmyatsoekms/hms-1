
import time
from odoo import api, fields, models, _


class ReportPMSLeaseAgreementReport(models.AbstractModel):

    _name = 'report.pms.lease.agreement.report'
    _description = 'Lease Agreement Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        # if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
        #     raise UserError(_("Form content is missing, this report cannot be printed."))

        # total = []
        # model = self.env.context.get('active_model')
        # docs = self.env[model].browse(self.env.context.get('active_id'))

        # target_move = data['form'].get('target_move', 'all')
        # date_from = fields.Date.from_string(data['form'].get('date_from')) or fields.Date.today()

        # if data['form']['result_selection'] == 'customer':
        #     account_type = ['receivable']
        # elif data['form']['result_selection'] == 'supplier':
        #     account_type = ['payable']
        # else:
        #     account_type = ['payable', 'receivable']

        # movelines, total, dummy = self._get_partner_move_lines(account_type, date_from, target_move, data['form']['period_length'])
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_partner_lines': movelines,
            'get_direction': total,
            'company_id': self.env['res.company'].browse(
                data['form']['company_id'][0]),
        }
