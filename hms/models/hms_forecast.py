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
    _name = "availability.availability"
    _description = "Availability"

    property_id = fields.Many2one('property.property', String="Property")
    avail_date = fields.Date(string="Date")
    avail_arrival = fields.Integer('Arrival Room') #, compute='_compute_arrival_room'
    avail_dep = fields.Integer('Departure Room')#, compute='_compute_departure_room')
    avail_occupancy = fields.Integer('Occupancy Room')#, compute ='_compute_occupy_room')
    avail_block = fields.Integer('Block Room')
    avail_ooo = fields.Integer('Out Of Order')
    avail_waitlist = fields.Integer('Wait List')
    avail_allotment = fields.Integer('Allotment')
    avail_arrguest = fields.Integer('Arrival Guest')
    avail_depguest = fields.Integer('Departure Guest')
    avail_occguest = fields.Integer('Occupied Guest')
    avail_grp = fields.Integer('Group Room')
    avail_fit = fields.Integer('Fit Room')
    avail_grpguest = fields.Integer('Group Guest')
    avail_fitguest = fields.Integer('Fit Guest')
    avail_unconfirm = fields.Integer('Unconfirm Reservation') #, compute='_compute_unconfirm_room'
    avail_rmrev = fields.Integer('Forecast Room Revenue')
    total_room = fields.Integer('Total Room',related="property_id.room_count")
    avail_totalroom = fields.Integer('Available Total Room', compute='_compute_avail_room')
    revpar = fields.Integer('REVPAR')
    adr = fields.Integer('ADR')
    avail_roomtype_ids = fields.One2many('roomtype.available','availability_id',"Available Room Type")

    _sql_constraints = [(
        'package_code_unique', 'UNIQUE(property_id, avail_date)',
        'Date already exists with this Property! Date must be unique!'
    )]

    # Compute Total Available Room
    @api.depends('total_room','avail_occupancy','avail_block','avail_ooo')
    def _compute_avail_room(self):
        for record in self:
            unavail_room = record.avail_occupancy + record.avail_block + record.avail_ooo
            record.avail_totalroom = record.total_room-unavail_room

    #Compute Unconfirm Rooms
    def _compute_unconfirm_room(self):
        for record in self:
            no_of_unconfirm_day = 0
            unconfirm_days = self.env['hms.reservation.line'].search([('property_id','=',record.property_id.id),('state','=','reservation'),('arrival','<=', record.avail_date),('departure','>',record.avail_date)])
            for rec in unconfirm_days:
                no_of_unconfirm_day += rec.rooms
            record.avail_unconfirm = no_of_unconfirm_day

    # Compute Arrival Rooms
    def _compute_arrival_room(self):
        for record in self:
            no_of_arrival_days = 0
            arrival_days =self.env['hms.reservation.line'].search([('property_id','=',record.property_id.id),('arrival','=', record.avail_date),('state','=','confirm')])
            for rec in arrival_days:
                no_of_arrival_days += rec.rooms
            record.avail_arrival = no_of_arrival_days

    #Compute Departure Rooms
    def _compute_departure_room(self):
        for record in self:
            no_of_dep_days = 0
            dep_days =self.env['hms.reservation.line'].search([('property_id','=',record.property_id.id),('departure','=', record.avail_date),('state','=','confirm')])
            for rec in dep_days:
                no_of_dep_days += rec.rooms
            record.avail_dep = no_of_dep_days

    #Compute Occupy Rooms
    def _compute_occupy_room(self):
        for record in self:
            no_of_occ_days = 0
            occ_days = self.env['hms.reservation.line'].search([('property_id','=',record.property_id.id),('arrival','<=', record.avail_date),('departure','>',record.avail_date),('state','=','confirm')])
            for rec in occ_days:
                no_of_occ_days += rec.rooms
            record.avail_occupancy = no_of_occ_days

# Room Type Available
class RoomTypeAvailable(models.Model):
    _name = "roomtype.available"
    _description = "Room Type Available"

    availability_id = fields.Many2one('availability.availability')
    property_id = fields.Many2one('property.property',string="Property")
    ravail_date = fields.Date('Date')
    roomtype_ids = fields.Many2many('room.type', related="property_id.roomtype_ids")
    ravail_rmty = fields.Many2one('room.type', string="Room Type", domain="[('id', '=?', roomtype_ids)]", required=True)#, domain="[('id', '=?', roomtype_ids)]", required=True
    ravail_ooo = fields.Integer('Out Of Order')
    ravail_occupancy = fields.Integer('Occupancy', compute='_compute_occupy_room')
    ravail_block = fields.Integer('Block')
    ravail_waitlist = fields.Integer('Wait List')
    ravail_allotment = fields.Integer('Allotment')
    ravail_unconfirm = fields.Integer('Unconfirm')#,compute ='_compute_unconfirm_room')
    total_room = fields.Integer('Total Room')#, compute='compute_totalroom')
    ravail_totalroom = fields.Integer('Room Type Available Total Room', compute='_compute_avail_room')

    def compute_totalroom(self):
        for rec in self:
            property_id = rec.property_id
            if property_id:
                property_obj = self.env['property.property'].search([('id','=',property_id.id)])
                room_objs_per_type = property_obj.propertyroom_ids.filtered(lambda x: x.roomtype_id.id==rec.ravail_rmty.id)
                room_count = len(room_objs_per_type)
                _logger.info(room_count)
            else:
                room_count = 0
            rec.total_room = room_count

    #Compute Unconfirm Rooms
    def _compute_unconfirm_room(self):

        for record in self:
            no_of_unconfirm_day = 0
            unconfirm_days = self.env['hms.reservation.line'].search([('property_id','=',record.property_id.id),('state','=','reservation'),('arrival','<=', record.ravail_date),('departure','>',record.ravail_date),('room_type','=',record.ravail_rmty.id)])
            for rec in unconfirm_days:
                no_of_unconfirm_day += rec.rooms
            record.ravail_unconfirm = no_of_unconfirm_day

    #Compute Occupy Rooms
    def _compute_occupy_room(self):
        
        for record in self:
            no_of_occ_days = 0
            occ_days = self.env['hms.reservation.line'].search([('property_id','=',record.property_id.id),('arrival','<=', record.ravail_date),('departure','>',record.ravail_date),('room_type','=',record.ravail_rmty.id),('state','=','confirm')])
            for rec in occ_days:
                no_of_occ_days += rec.rooms
            record.ravail_occupancy = no_of_occ_days

    # Compute Total Available Room
    def _compute_avail_room(self):
        for record in self:
            unavail_room = record.ravail_occupancy + record.ravail_block + record.ravail_ooo
            record.ravail_totalroom = record.total_room - unavail_room