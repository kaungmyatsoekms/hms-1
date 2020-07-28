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
                                 domain="[('is_guest','=',True)]")
    group_name = fields.Many2one("res.partner",
                                 string="Group Name",
                                 domain="[('is_group','=',True)]")
    pax = fields.Integer(string="Pax")
    child = fields.Integer(string="Child")
    nationality_id = fields.Many2one('hms.nationality', string="Nationality")

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
            d.write({
                'state': 'checkin',
                'guest_id': self.guest_name,
                'group_id': self.group_name,
                'pax': self.pax,
                'child': self.child,
                'nationality_id': self.nationality_id,
            })
        reservation_lines.reservation_id.write({
            'state': 'checkin',
        })
