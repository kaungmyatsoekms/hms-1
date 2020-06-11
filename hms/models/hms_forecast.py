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
    avail_arrival = fields.Integer('Arrival Room')
    arrival_dep = fields.Integer('Departure Room')
    avail_occupancy = fields.Integer('Occupancy Room')
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
    avail_unconfirm = fields.Integer('Unconfirm Reservation')
    avail_rmrev = fields.Integer('Forecast Room Revenue')
    total_room = fields.Integer('Total Room',related="property_id.room_count")
    avail_totalroom = fields.Integer('Available Total Room')
    revpar = fields.Integer('REVPAR')
    adr = fields.Integer('ADR')
    avail_roomtype_ids = fields.One2many('roomtype.available','availability_id',"Available Room Type")

    _sql_constraints = [(
        'package_code_unique', 'UNIQUE(property_id, avail_date)',
        'Date already exists with this Property! Date must be unique!'
    )]

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
    ravail_occupancy = fields.Integer('Occupancy')
    ravail_block = fields.Integer('Block')
    ravail_waitlist = fields.Integer('Wait List')
    ravail_allotment = fields.Integer('Allotment')
    ravail_unconfirm = fields.Integer('Unconfirm')
    total_room = fields.Integer('Total Room', compute='compute_totalroom')
    ravail_totalroom = fields.Integer('Room Type Available Total Room')

    def compute_totalroom(self):
        for rec in self:
            property_id = rec.property_id
            if property_id:
                property_obj = self.env['property.property'].search([('id','=',property_id.id)])
                _logger.info('#################################')
                _logger.info(property_obj)
                room_objs_per_type = property_obj.propertyroom_ids.filtered(lambda x: x.roomtype_id.id==rec.ravail_rmty.id)
                room_count = len(room_objs_per_type)
                _logger.info(room_count)
            else:
                room_count = 0
            rec.total_room = room_count