import datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class HMSRsvnConfirmWizard(models.TransientModel):
    _name = "hms.rsvn_confirm_wizard"
    _description = "Confirm Wizard"

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
    reservation_type = fields.Many2one('rsvn.type',
                                       "Reservation Type",
                                       readonly=True,
                                       default=1)
    reservation_status = fields.Many2one('rsvn.status', "Reservation Status")

    def action_confirm_wiz(self):
        reservations = self.env['hms.reservation'].browse(
            self._context.get('active_id', []))

        for d in reservations.reservation_line_ids:
            d.write({
                'reservation_type': self.reservation_type,
                'reservation_status': self.reservation_status
            })
        reservations.write({
            'reservation_type': self.reservation_type,
            'reservation_status': self.reservation_status
        })
        reservations.confirm_status()
        reservations.write({
            'state': 'confirm',
        })
        # return reservations.send_mail()


class HMSRsvnConfirmLineWizard(models.TransientModel):
    _name = "hms.rsvn_confirm_line_wizard"
    _description = "Confirm Wizard"

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
    reservation_type = fields.Many2one('rsvn.type',
                                       "Reservation Type",
                                       readonly=True,
                                       default=1)
    reservation_status = fields.Many2one('rsvn.status', "Reservation Status")

    def action_confirm_line_wiz(self):
        reservation_lines = self.env['hms.reservation.line'].browse(
            self._context.get('active_id'))

        for d in reservation_lines:
            d.write({
                'reservation_type': self.reservation_type,
                'reservation_status': self.reservation_status
            })
        reservation_lines.write({
            'reservation_type': self.reservation_type,
            'reservation_status': self.reservation_status
        })
        reservation_lines.confirm_status()
        reservation_lines.write({
            'state': 'confirm',
        })
        # return reservations.send_mail()