import base64
import datetime
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules import get_module_resource
from odoo.tools import *

# Availability
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
    avail_occguest = fields.Integer('Occupid Guest')
    avail_grp = fields.Integer('Group Room')
    avail_fit = fields.Integer('Fit Room')
    avail_grpguest = fields.Integer('Group Guest')
    avail_fitguest = fields.Integer('Fit Guest')
    avail_unconfirm = fields.Integer('Unconfirm Reservation')
    avail_rmrev = fields.Integer('Forecast Room Revenue')
    total_room = fields.Integer('Total Room')
    avail_totalroom = fields.Integer('Available Total Room')
    revpar = fields.Integer('REVPAR')
    adr = fields.Integer('ADR')

# Room Type Available
class RoomTypeAvailable(models.Model):
    _name = "roomtype.available"
    _description = "Room Type Available"

    property_id = fields.Many2one('property.property',string="Property")
    ravail_date = fields.Date('Date')
    ravail_rmty = fields.Integer('Room Type')
    ravail_ooo = fields.Integer('Out Of Order')
    ravail_occupancy = fields.Integer('Occupancy')
    ravail_block = fields.Integer('Block')
    ravail_waitlist = fields.Integer('Wait List')
    ravail_allotment = fields.Integer('Allotment')
    ravail_unconfirm = fields.Integer('Unconfirm')
    total_room = fields.Integer('Total Room')
    ravail_totalroom = fields.Integer('Room Type Available Total Room')


