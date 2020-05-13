import datetime
from odoo import api, fields, models, tools, _


class PMSLeaseCancelWizard(models.TransientModel):
    _name = "pms.lease_cancel_wizard"
    _description = "Cancel Wizard"

    @api.multi
    def action_cancel_wiz(self):
        lease_ids = self.env['pms.lease_agreement'].browse(
            self._context.get('active_id', []))
        lease_ids.write({'state': 'CANCELLED'})
        return True
