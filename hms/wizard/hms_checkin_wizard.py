import datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class HMSRsvnCheckinLineWizard(models.TransientModel):
    _name = "hms.rsvn_checkin_line_wizard"
    _description = "Check-In Wizard"

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
    guest_name = fields.Many2one("res.partner",
                                 string="Guest Name",
                                 domain="[('is_guest','=',True)]")
    group_name = fields.Many2one("res.partner",
                                 string="Group Name",
                                 domain="[('is_group','=',True)]")
    pax = fields.Integer(string="Pax")
    child = fields.Integer(string="Child")
    room_no = fields.Many2one("hms.property.room", string="Room No")

    # ratehead_id = fields.Many2one(
    #     'hms.ratecode.header',
    #     domain=
    #     "[('property_id', '=', reservation_line_id.property_id.id), ('start_date', '<=', reservation_line_id.arrival), ('end_date', '>=', reservation_line_id.departure)]"
    # )

    def action_checkin_line_wiz(self):
        reservation_lines = self.env['hms.reservation.line'].browse(
            self._context.get('active_id'))
        for d in reservation_lines:
            d.write({
                'state': 'checkin',
                'guest_id': self.guest_name,
                'group_id': self.group_name,
                'pax': self.pax,
                'child': self.child,
                'room_no': self.room_no,
            })
