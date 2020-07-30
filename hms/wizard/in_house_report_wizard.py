from odoo import models, fields, api, _
import tempfile
from odoo.tools.misc import xlwt
import io
import base64
from odoo.tools import date_utils


class InHouseReportWizard(models.TransientModel):
    _name = 'hms.inhouse_report_wizard'

    property_id = fields.Many2one('hms.property',
                                  string="Property",
                                  required=True)
    system_date = fields.Date(string="System Date",
                              related="property_id.system_date",
                              store=True)
    property_name = fields.Char(string="Property Name", store=True)
    with_rate = fields.Boolean(default=False)
    rate_attr = fields.Selection(string='Rate',
                                 selection=[('with', 'With Rate'),
                                            ('without', 'Without Rate')],
                                 compute='_compute_rate_attr',
                                 inverse='_write_rate_attr')
    sorting_method = fields.Selection(
        string="Sort By",
        selection=[('gname', 'Guest Name'), ('gpname', 'Group Name'),
                   ('cname', 'Company Name'), ('room', 'Room No'),
                   ('arr', 'Arrival Date'), ('dep', 'Departure Date')],
    )

    @api.onchange('property_id')
    def onchange_property_name(self):
        for rec in self:
            rec.property_name = rec.property_id.name

    # Radio Button for Rate Attr
    @api.depends('with_rate')
    def _compute_rate_attr(self):
        for rec in self:
            if rec.with_rate or self._context.get(
                    'default_rate_attr') == 'with':
                rec.rate_attr = 'with'
                rec.with_rate = True
            else:
                rec.rate_attr = 'without'

    def _write_rate_attr(self):
        for rec in self:
            rec.with_rate = rec.rate_attr == 'with'

    @api.onchange('rate_attr')
    def onchange_rate_attr(self):
        self.with_rate = (self.rate_attr == 'with')

    def get_report(self):
        data = {
            'ids':
            self.ids,
            'model':
            'hms.reservation.line',
            'form':
            self.read([
                'property_id', 'property_name', 'system_date', 'rate_attr',
                'with_rate', 'sorting_method'
            ])[0]
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('hms.inhouse_report').report_action(self,
                                                                data=data)
