from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules import get_module_resource
from odoo.tools import *
import base64
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)


#Availability
class Availability(models.Model):
    _name = "hms.availability"
    _description = "Availability"

    active = fields.Boolean('Active', default=True, help='Active')
    color = fields.Integer(string='Color Index', help="Colour Index")
    property_id = fields.Many2one('hms.property', String="Property")
    avail_date = fields.Date(string="Date", help="Date")
    avail_booking = fields.Integer('Booking', default=0, help="Booking")
    avail_arrival = fields.Integer('Arr', store=True, default=0, help="Arr")
    avail_dep = fields.Integer('Dep', store=True, default=0, help="Dep")
    avail_occupancy = fields.Integer('Occ', store=True, default=0, help="Occ")
    avail_block = fields.Integer('Block', default=0, help="Block")
    avail_ooo = fields.Integer('OOO', default=0, help="OOO")
    avail_waitlist = fields.Integer('Wait', default=0, help="Wait")
    avail_allotment = fields.Integer('Allt', default=0, help="Allt")
    avail_arrguest = fields.Integer('Arr Guests', default=0, help="Arr Guests")
    avail_depguest = fields.Integer('Dep Guests', default=0, help="Dep Guests")
    avail_occguest = fields.Integer('Occ Guests', default=0, help="Occ Guests")
    avail_grp = fields.Integer('GRP Rooms', default=0, help='GRP Rooms')
    avail_fit = fields.Integer('FIT Rooms', default=0, help="FIT Rooms")
    avail_grpguest = fields.Integer('GRP Guests', default=0, help="GRP Guests")
    avail_fitguest = fields.Integer('FIT Guests', default=0, help="FIT Guests")
    avail_unconfirm = fields.Integer('Uncfm', store=True, default=0, help="Uncfm")
    avail_rmrev = fields.Integer('Room Revenue', default=0, help="Room Revenue")
    total_room = fields.Integer('Total Room', help="Total Room")
    avail_tl_room = fields.Integer('Avail',
                                   compute='_compute_avail_room',
                                   store=True, help="Avail")
    revpar = fields.Integer('REVPAR', default=0, help="REVPAR")
    adr = fields.Integer('ADR', default=0, help="ADR")
    avail_roomtype_ids = fields.One2many('hms.roomtype.available',
                                         'availability_id',
                                         "Available Room Type", help="Available Room Type")
    # reservation_line_ids = fields.One2many(
    #     'hms.reservation.line',
    #     'property_id',
    #     related='property_id.reservation_line_ids',
    #     string="Reservation lines")

    _sql_constraints = [
        ('package_code_unique', 'UNIQUE(property_id, avail_date)',
         'Date already exists with this Property! Date must be unique!')
    ]

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} (Total Available Rooms - {})".format(
                record.avail_date, record.avail_tl_room)))
        return result

    # Compute Total Available Room (Use)
    @api.depends('total_room', 'avail_occupancy', 'avail_block', 'avail_ooo')
    def _compute_avail_room(self):
        for record in self:
            unavail_room = record.avail_occupancy + record.avail_block + record.avail_ooo
            record.avail_tl_room = record.total_room - unavail_room

    #Compute Unconfirm Rooms (No Use)
    # @api.depends('reservation_line_ids')
    # def _compute_unconfirm_room(self):
    #     for record in self:
    #         no_of_unconfirm_day = 0
    #         unconfirm_days = self.env['hms.reservation.line'].search([
    #             ('property_id', '=', record.property_id.id),
    #             ('state', '=', 'reservation'),
    #             ('arrival', '<=', record.avail_date),
    #             ('departure', '>', record.avail_date)
    #         ])
    #         for rec in unconfirm_days:
    #             no_of_unconfirm_day += rec.rooms
    #         record.avail_unconfirm = no_of_unconfirm_day

    # Compute Arrival Rooms (No Use)
    # @api.depends('reservation_line_ids')
    # def _compute_arrival_room(self):
    #     for record in self:
    #         no_of_arrival_days = 0
    #         arrival_days = self.env['hms.reservation.line'].search([
    #             ('property_id', '=', record.property_id.id),
    #             ('arrival', '=', record.avail_date), ('state', '=', 'confirm')
    #         ])
    #         for rec in arrival_days:
    #             no_of_arrival_days += rec.rooms
    #         record.avail_arrival = no_of_arrival_days

    #Compute Departure Rooms (No Use)
    # @api.depends('reservation_line_ids')
    # def _compute_departure_room(self):
    #     for record in self:
    #         no_of_dep_days = 0
    #         dep_days = self.env['hms.reservation.line'].search([
    #             ('property_id', '=', record.property_id.id),
    #             ('departure', '=', record.avail_date),
    #             ('state', '=', 'confirm')
    #         ])
    #         for rec in dep_days:
    #             no_of_dep_days += rec.rooms
    #         record.avail_dep = no_of_dep_days

    #Compute Occupy Rooms (No Use)
    # @api.depends('reservation_line_ids')
    # def _compute_occupy_room(self):
    #     for record in self:
    #         no_of_occ_days = 0
    #         occ_days = self.env['hms.reservation.line'].search([
    #             ('property_id', '=', record.property_id.id),
    #             ('arrival', '<=', record.avail_date),
    #             ('departure', '>', record.avail_date),
    #             ('state', '=', 'confirm')
    #         ])
    #         for rec in occ_days:
    #             no_of_occ_days += rec.rooms
    #         record.avail_occupancy = no_of_occ_days


# Room Type Available
class RoomTypeAvailable(models.Model):
    _name = "hms.roomtype.available"
    _description = "Room Type Available"

    active = fields.Boolean('Active', default=True, help="Active")
    color = fields.Integer(string='Color Index', help="Colour Index")
    availability_id = fields.Many2one('hms.availability', help="Availability")
    property_id = fields.Many2one('hms.property',
                                  string="Property", help="Property")
    ravail_date = fields.Date('Date', required=True, help="Date")
    roomtype_ids = fields.Many2many('hms.roomtype',
                                    related="property_id.roomtype_ids")
    ravail_rmty = fields.Many2one(
        'hms.roomtype',
        string="Room Type",
        domain="[('id', '=?', roomtype_ids)]",
        required=True, help="Room Type")  #, domain="[('id', '=?', roomtype_ids)]", required=True
    ravail_ooo = fields.Integer('Out Of Order', default=0, help="Out of Order")
    ravail_booking = fields.Integer('Booking', default=0, help="Booking")
    ravail_occupancy = fields.Integer('Occupancy', default=0, help="Occupancy")
    ravail_block = fields.Integer('Block', default=0, help="Block")
    ravail_waitlist = fields.Integer('Wait List', default=0, help="Wait List")
    ravail_allotment = fields.Integer('Allotment', default=0, help="Allotment")
    ravail_unconfirm = fields.Integer(
        'Unconfirm', default=0, help="Unconfirm")  #,compute ='_compute_unconfirm_room')
    total_room = fields.Integer('Total Room', store=True, help="Total Room")
    ravail_totalroom = fields.Integer('Available',
                                      compute='_compute_avail_room',
                                      store=True, help="Available")
    overbook_ids = fields.One2many('hms.overbooking', 'rt_avail_id',
                                   "Overbookings", help="Overbooking")

    def name_get(self):
        result = []
        for record in self:
            result.append(
                (record.id, "{}-{}".format(record.ravail_rmty.code,
                                                record.ravail_totalroom)))
        return result

    # Compute Total Available Room (Use)
    @api.depends('total_room', 'ravail_occupancy', 'ravail_block',
                 'ravail_ooo')
    def _compute_avail_room(self):
        for record in self:
            unavail_room = record.ravail_occupancy + record.ravail_block + record.ravail_ooo
            record.ravail_totalroom = record.total_room - unavail_room