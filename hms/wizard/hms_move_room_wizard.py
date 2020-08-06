from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import datetime,date, timedelta
from dateutil.relativedelta import relativedelta

class MoveRoomWizard(models.TransientModel):
    _name = "hms.move_room_wizard"
    _description = "Move Room"

    def get_inhouse_rsvn_line_id(self):
        inhouse_rsvn_line_id = self.env['hms.reservation.line'].browse(
            self._context.get('active_id',[])
        )
        if inhouse_rsvn_line_id:
            return inhouse_rsvn_line_id

    def get_avail_rooms(self):
        line_id = self.env['hms.reservation.line'].browse(
            self._context.get('active_id',[])
        )
        total_rooms = self.env['hms.property.room'].search([
            ('property_id', '=', line_id.property_id.id)
        ])

        total_rooms = total_rooms.filtered(lambda x: x.roomtype_id.code[0] != 'H').ids

        occ_rooms = self.env['hms.reservation.line'].search([
            ('property_id', '=', line_id.property_id.id),
            '|',('state', '=', 'confirm'),
            ('state', '=', 'checkin'),
        ])

        occ_rooms = occ_rooms.filtered(lambda x: x.room_type.code[0] != 'H').room_no.ids

        avail_rooms = list(set(total_rooms) - set(occ_rooms))

        if line_id:
            return avail_rooms

    inhouse_rsvn_line_id = fields.Many2one('hms.reservation.line', default=get_inhouse_rsvn_line_id)
    property_id = fields.Many2one('hms.property', related="inhouse_rsvn_line_id.property_id")
    avail_rooms = fields.Many2many('hms.property.room', default=get_avail_rooms)
    room_no = fields.Many2one('hms.property.room', domain="[('id', '=?', avail_rooms)]", required=True)

    def action_move_room_wiz(self):

        inhouse_rsvn_line_id = self.env['hms.reservation.line'].browse(
            self._context.get('active_id'))

        if self.room_no.bedtype_id:
            inhouse_rsvn_line_id.update({
                'room_no': self.room_no.id,
                'room_type': self.room_no.roomtype_id.id,
                'bedtype_id': self.room_no.bedtype_id.id,
            })


        else:
            inhouse_rsvn_line_id.update({
                'room_no': self.room_no.id,
                'room_type': self.room_no.roomtype_id.id,
            })




