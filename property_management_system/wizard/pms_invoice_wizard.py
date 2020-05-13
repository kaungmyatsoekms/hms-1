import calendar
from datetime import datetime
from odoo import api, fields, models, tools, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class PMSInvoicewizard(models.TransientModel):
    _name = "pms.invoice_wizard"
    _description = "Invoice Wizard"

    @api.model
    def default_month(self):
        timesheet_date = datetime.strptime(str(
            datetime.now()), '%Y-%m-%d %H:%M:%S.%f').strftime(
                tools.misc.DEFAULT_SERVER_DATETIME_FORMAT)
        months = datetime.strptime(timesheet_date, '%Y-%m-%d %H:%M:%S')
        name = months.month
        return name

    @api.model
    def default_year(self):
        timesheet_date = datetime.strptime(str(
            datetime.now()), '%Y-%m-%d %H:%M:%S.%f').strftime(
                tools.misc.DEFAULT_SERVER_DATETIME_FORMAT)
        years = datetime.strptime(timesheet_date, '%Y-%m-%d %H:%M:%S')
        return years.year

    inv_create_type = fields.Selection([('MONTHLY', "MONTHLY"),
                                        ('QUORTERLY', "QUORTERLY")],
                                       string="Create Type",
                                       default="MONTHLY")

    inv_month = fields.Selection([
        (1, 'January'),
        (2, 'February'),
        (3, 'March'),
        (4, 'April'),
        (5, 'May'),
        (6, 'June'),
        (7, 'July'),
        (8, 'August'),
        (9, 'September'),
        (10, 'October'),
        (11, 'November'),
        (12, 'December'),
    ],
                                 string='Month',
                                 default=default_month)
    inv_year = fields.Selection(
        [(num, str(num)) for num in range(1900, (datetime.now().year) + 1)],
        string='Year',
        default=default_year)
    inv_quorter = fields.Selection([('1ST-QUORTER', '1ST-QUORTER'),
                                    ('2ND-QUORTER', '2ND-QUORTER'),
                                    ('3RD-QUORTER', '3RD-QUORTER'),
                                    ('4TH-QUORTER', '4TH-QUORTER')],
                                   string="Quorter",
                                   default='1ST-QUORTER')

    @api.multi
    def create_lease_invoice(self):
        lease_invoices = self.env['pms.lease_agreement.line'].browse(
            self._context.get('active_id', []))
        vals = []
        vals.append([self.inv_month, self.inv_year, self.inv_quorter])
        invoices = lease_invoices.action_invoice(self.inv_create_type, vals)
        if invoices:
            action = self.env.ref('account.action_invoice_tree1').read()[0]
            if len(invoices) > 1:
                action['domain'] = [('id', 'in', invoices.ids)]
            elif len(invoices) == 1:
                action['views'] = [(self.env.ref('account.invoice_form').id,
                                    'form')]
                action['res_id'] = invoices.ids[0]
            else:
                action = {'type': 'ir.actions.act_window_close'}
            return action
        return {'type': 'ir.actions.act_window_close'}
