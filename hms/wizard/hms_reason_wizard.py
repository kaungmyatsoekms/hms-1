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
<<<<<<< HEAD
        reservations.write({
            'reason_id': self.reason_id,
        })
=======
>>>>>>> 813ce8ba9d8720bff9380cda22d30976a425e869
        reservations.reservation_line_ids.write({
            'reason_id': self.reason_id,
        })
        reservations.cancel_status()
<<<<<<< HEAD
        reservations.copy_cancel_record()
=======
>>>>>>> 813ce8ba9d8720bff9380cda22d30976a425e869
        reservations.write({
            'state': 'cancel',
        })
        reservations.reservation_line_ids.write({
            'state': 'cancel',
        })
<<<<<<< HEAD
        # return reservations.send_mail()


class HMSCancelReasonLineWizard(models.TransientModel):
    _name = "hms.cancel_reason_line_wizard"
    _description = "Cancel Reason Wizard"

    def get_reservation_line_id(self):
        reservation_line = self.env['hms.reservation.line'].browse(
            self._context.get('active_id', []))
        if reservation_line:
            return reservation_line

    reservation_line_id = fields.Many2one("hms.reservation.line",
                                          default=get_reservation_line_id,
                                          store=True)
    reservation_no = fields.Char("Reservation",
                                 related="reservation_line_id.confirm_no",
                                 store=True)
    reason_id = fields.Many2one('hms.reason', string="Reason")

    def action_reason_line_wiz(self):
        reservation_lines = self.env['hms.reservation.line'].browse(
            self._context.get('active_id', []))

        for d in reservation_lines:
            d.write({
                'reason_id': self.reason_id,
            })
        reservation_lines.write({
            'reason_id': self.reason_id,
        })
        reservation_lines.cancel_status()
        reservation_lines.copy_cancel_record()
        reservation_lines.write({
            'state': 'cancel',
        })
=======
>>>>>>> 813ce8ba9d8720bff9380cda22d30976a425e869
        # return reservations.send_mail()