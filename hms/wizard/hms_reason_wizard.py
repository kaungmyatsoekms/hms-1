import datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class HMSCancelReasonWizard(models.TransientModel):
    _name = "hms.cancel_reason_wizard"
    _description = "Cancel Reason Wizard"

    def get_reservation_id(self):
        reservation = self.env['hms.reservation'].browse(
            self._context.get('active_id', []))
        if reservation:
            return reservation

    reservation_id = fields.Many2one("hms.reservation",
                                     default=get_reservation_id,
                                     store=True)
    reservation_no = fields.Char("Reservation",
                                 related="reservation_id.confirm_no",
                                 store=True)
    reason_id = fields.Many2one('hms.reason', string="Reason")

    def action_reason_wiz(self):
        reservations = self.env['hms.reservation'].browse(
            self._context.get('active_id', []))

        for d in reservations.reservation_line_ids:
            d.write({
                'reason_id': self.reason_id,
            })
        reservations.reservation_line_ids.write({
            'reason_id': self.reason_id,
        })
        reservations.cancel_status()
        reservations.write({
            'state': 'cancel',
        })
        reservations.reservation_line_ids.write({
            'state': 'cancel',
        })
        # return reservations.send_mail()