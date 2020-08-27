from odoo import models, fields, api
from odoo.exceptions import UserError


class ProformaReportWizard(models.TransientModel):
    _name = 'hms.proforma_report_wizard'

    rsvn_line_id = fields.Many2one('hms.reservation.line',
                                  string="Reservation Line",
                                  required=True)

    def get_report(self):
        data = {
            'ids': self.ids,
            'model': 'hms.reservation.line',
            'form': self.read(['rsvn_line_id'])[0]
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('hms.proforma_report').report_action(self,
                                                                 data=data)