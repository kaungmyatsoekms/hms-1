import datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class HMSRsvnUnconfirmWizard(models.TransientModel):
    _name = "hms.rsvn_unconfirm_wizard"
    _description = "Unconfirm Wizard"

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
                                       default=2)
    reservation_status = fields.Many2one('rsvn.status', "Reservation Status")

    def action_unconfirm_wiz(self):
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
        reservations.unconfirm_status()
        reservations.write({
            'state': 'reservation',
        })
        # return reservations.send_mail()
