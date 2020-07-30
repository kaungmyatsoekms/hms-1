import datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class HMSCheckinMessageWizard(models.TransientModel):
    _name = "hms.checkin_message_wizard"
    _description = "Required Info Message Box to Check-In"

    text = fields.Text()


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
                                 required=True,
                                 domain="[('is_guest','=',True)]")
    group_name = fields.Many2one("res.partner",
                                 string="Group Name",
                                 domain="[('is_group','=',True)]")
    pax = fields.Integer(string="Pax", required=True)
    child = fields.Integer(string="Child")
    nationality_id = fields.Many2one('hms.nationality',
                                     string="Nationality",
                                     required=True)
    extrabed = fields.Integer("Extra Bed", help="No. of Extra Bed")
    child_bfpax = fields.Integer("Child BF-Pax", help="Child BF Pax")

    @api.onchange('guest_name')
    def onchange_guest_nationality(self):
        for rec in self:
            if rec.guest_name:
                if rec.guest_name.nationality_id:
                    rec.nationality_id = rec.guest_name.nationality_id
                else:
                    rec.nationality_id = False

    def action_checkin_line_wiz(self):
        reservation_lines = self.env['hms.reservation.line'].browse(
            self._context.get('active_id'))

        for d in reservation_lines:
            citime = datetime.strptime(str(datetime.now()),
                                       "%Y-%m-%d %H:%M:%S.%f")
            d.write({
                'state': 'checkin',
                'guest_id': self.guest_name,
                'group_id': self.group_name,
                'pax': self.pax,
                'child': self.child,
                'nationality_id': self.nationality_id,
                'citime': citime,
            })
        # Update Guest Nationality in Guest Profile
        reservation_lines.guest_id.write({
            'nationality_id': self.nationality_id,
        })
        # Update 'checkin' state to main reservation
        count = 0
        for d in reservation_lines.reservation_id.reservation_line_ids:
            if d.state == 'checkin':
                if d.room_type.code[0] != 'H':
                    count += 1

        if count > 0:
            reservation_lines.reservation_id.write({
                'state': 'checkin',
            })
            hfo_reservation = self.env['hms.reservation.line'].search([
                ('reservation_id', '=', reservation_lines.reservation_id.id),
                ('room_type', '=ilike', 'H%')
            ])
            if hfo_reservation:
                hfo_reservation.write({'state': 'checkin'})