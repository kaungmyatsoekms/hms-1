import datetime
from odoo import api, fields, models, tools, _


class PMSLeaseReportlWizard(models.TransientModel):
    _name = "pms.lease.report.wizard"
    _description = "Lease Report Wizard"

    property_id = fields.Many2one("pms.properties", "Property")
    lease_no = fields.Char("Lease No")
    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")

    @api.multi
    def print_report(self):
        """
            Print report either by warehouse or product-category
        """
        assert len(
            self
        ) == 1, 'This option should only be used for a single id at a time.'
        datas = {
            'form': {
                'property_id':
                property_id.id,
                'lease_no':
                self.lease_no,
                'from_date':
                self.from_date,
                'to_date':
                self.to_date,
            }
        }
        return self.env.ref(
            'property_management_system.action_inventory_report_by_warehouse'
        ).with_context(landscape=True).report_action(self, data=datas)
