from odoo import models, fields, api
from odoo.exceptions import UserError


class PropertyReportWizard(models.TransientModel):
    _name = 'hms.property_report_wizard'

    property_id = fields.Many2one('hms.property',
                                  string="Property",
                                  required=True)

    def get_report(self):
        data = {
            'ids': self.ids,
            'model': 'hms.property',
            'form': self.read(['property_id'])[0]
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('hms.property_report').report_action(self,
                                                                 data=data)
