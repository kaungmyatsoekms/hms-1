import datetime
from odoo import api, fields, models, tools, _


class PMSLeaseActivateWizard(models.TransientModel):
    _name = "pms.lease.activate.wizard"
    _description = "Activate Wizard"

    @api.multi
    def action_activate_wiz(self):
        lease_ids = self.env['pms.lease_agreement'].browse(
            self._context.get('active_id', []))
        lease_ids.action_activate()
        return lease_ids.send_mail()
