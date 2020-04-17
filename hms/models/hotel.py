from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError
from odoo.modules import get_module_resource
#from odoo.tools import image_colorize, image_resize_image_big
from odoo.tools import *
import base64

AVAILABLE_STARS = [
    ('0', 'Low'),
    ('1', 'One Star'),
    ('2', 'Two Star'),
    ('3', 'Three Star'),
    ('4', 'Four Star'),
    ('5', 'Five Star'),
]

class HotelGroup(models.Model):
    _name = "hotel.group"
    _description = "Hotel Group"

    name = fields.Char(string='Hotel Group Name', required=True)

class Property(models.Model):
    _name = "property.property"
    _description = "Property"

    hotelgroup_id = fields.Many2one('hotel.group',
                                    string='Hotel Group',
                                    required=True)
    name = fields.Char(required=True, string='Hotel Name', index=True)
    code = fields.Char(string='Property ID', required=True)
    address1 = fields.Char(string='Address 1')
    address2 = fields.Char(string='Address 2')
    address3 = fields.Char(string='Address 3')
    city_id = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    zip = fields.Char(change_default=True)
    country_id = fields.Many2one('res.country', string='Country')
    phone = fields.Char(string='Phone')
    fax = fields.Char(string='Fax')
    email = fields.Char(string='Email')
    website = fields.Char(string='Website')
    sociallink = fields.Char(string='Social Link')
    roomqty = fields.Integer(string='Total Rooms', compute='_compute_room_no_count')
    property_license = fields.Char(string='Property License')
    rating = fields.Selection(AVAILABLE_STARS, string='Rating', index=True, default=AVAILABLE_STARS[0][0])
    logo = fields.Binary(string='Logo', attachment=True, store=True)
    image = fields.Binary(string='Image', attachment=True, store=True)
    contact_ids = fields.Many2many('contact.contact')
    bankinfo_ids = fields.One2many('bank.info','property_id', string="Bank Info")
    comments = fields.Text(string='Notes')
    roomtype_ids = fields.Many2many('room.type')
    building_ids = fields.Many2many('building.building')
    propertyroom_ids = fields.One2many('property.room','property_id', string="Property Room")
    building_count = fields.Integer("Building", compute='_compute_building_count')
    room_count = fields.Integer("Room", compute='_compute_room_count')
    roomtype_count = fields.Integer("Room Type", compute='_compute_roomtype_count')
    package_ids = fields.One2many('package.package', 'property_id', string="Package")
    transgroup_ids = fields.One2many('transaction.group', 'property_id', string="Transaction Group")
    transaction_ids = fields.One2many('transaction.transaction', 'property_id', string="Transaction")

    def action_building_count(self):
        buildings = self.mapped('building_ids')
        action = self.env.ref('hms.building_action_window').read()[0]
        if len(buildings) > 1:
            action['domain'] = [('id', 'in', buildings.ids)]
        elif len(buildings) == 1:
            form_view = [(self.env.ref('hms.building_view_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = buildings.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_type': 'out_building',
        }
        return action
    
    def _compute_room_no_count(self):
        self.roomqty = len(self.propertyroom_ids)

    def _compute_building_count(self):
        self.building_count = len(self.building_ids)
    
    # Room Count
    def action_room_count(self):
        rooms = self.mapped('propertyroom_ids')
        action = self.env.ref('hms.property_room_action_window').read()[0]
        if len(rooms) > 1:
            action['domain'] = [('id', 'in', rooms.ids)]
        elif len(rooms) == 1:
            form_view = [(self.env.ref('hms.property_room_view_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = rooms.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_type': 'out_room',
        }
        return action
    
    def _compute_room_count(self):
        self.room_count = len(self.propertyroom_ids)

    # Room Type Count
    def action_room_type_count(self):
        room_types = self.mapped('roomtype_ids')
        action = self.env.ref('hms.room_type_action_window').read()[0]
        if len(room_types) > 1:
            action['domain'] = [('id', 'in', room_types.ids)]
        elif len(room_types) == 1:
            form_view = [(self.env.ref('hms.room_type_view_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = room_types.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_type': 'out_room_type',
        }
        return action
    
    def _compute_roomtype_count(self):
        self.roomtype_count = len(self.roomtype_ids)
    
    # @api.depends('id')    
    # def _property_pc(self):
    #     for rec in self:
    #         # if(rec.id.propertyroom_ids):
    #         for roomno in rec.id.propertyroom_ids:
    #             roomno.property_id = int(roomno.property_id)

    # @api.onchange('property_id')
    # def onchange_property_id(self):
    #     roomtype_list =[]
    #     domain={}
    #     for rec in self:
    #         if(rec.property_id.roomtype_ids):
    #             for roomtype in rec.property_id.building_ids:
    #                 roomtype_list.append(roomtype.id)
    #             domain = {'roomtype_id':[('id','=', roomtype_list)]}
    #             return{'domain': domain}

class Contact(models.Model):
    _name = "contact.contact"
    _description = "Contact"

    name = fields.Char(string='Contact Person', required=True)
    email = fields.Char(string='Email')
    title = fields.Many2one('res.partner.title')
    phone = fields.Char(string='Phone')
    position = fields.Char(string='Job Position')
    image = fields.Binary(string='Image', attachment=True, store=True)

    @api.model
    def _get_default_image(self, colorize=False):
        image = image_colorize(
            open(
                odoo.modules.get_module_resource('base', 'static/src/img',
                                                 'avatar_grey/png')).read())
        return image_resize_image_big(image.encode('base64'))

class BankInfo(models.Model):
    _name = "bank.info"
    _description = "Bank Information"

    property_id = fields.Many2one('property.property', string="Property", required=True, readonly=True)
    bank_name = fields.Char(string="Bank Name", required=True)
    bank_branch = fields.Char(string="Branch Name", required=True)
    bank_account = fields.Char(string="Bank Account", required=True)
    bank_logo = fields.Binary(string="Bank Logo")
    bank_desc = fields.Text(string="Description")

class Building(models.Model):
    _name = "building.building"
    _description = "Building"
    _rec_name ='building_name'

    building_name = fields.Char(string='Building Name', required=True)
    building_type = fields.Many2one('building.type',
                                    string='Building Type',
                                    required=True)
    building_location = fields.Char(string='Location')
    building_img = fields.Binary(string='Building Image',
                                 attachment=True,
                                 store=True)
    building_desc = fields.Text(string='Description')
    building_capacity = fields.Integer(string='Capacity', required=True)
    location_ids = fields.Many2many('room.location', string="Room Location", required=True)
    # location_number = fields.Integer("Location Number", compute="_room_location_count", readonly=True)

    # def get_name(self,cr, uid, ids, context=None):
    #     if context is None:
    #         context = {}
    #     if isinstance(ids, (int, long)):
    #         ids = [ids]

    #     res = []
    #     for record in self.browse(cr, uid, ids, context=context):
    #         name = record.building_name
    #         res.append(record.id, name)
    #     return res

    # @api.model
    # def name_get(self):
    #     result = []
    #     for record in self:
    #         result.append((record.id, "{}".format(record.building_name)))
    #     return result

    
    # @api.depends('building_capacity','location_ids')
    # def _room_location_count(self):
       
    #         return len(locations)

    # @api.model
    # def create(self, values):
    #     locations = values['location_ids']
    #     building_capacity = values['building_capacity']
    #     if values['location_ids'][0][2]:
    #         if len(values['location_ids'][0][2]) > building_capacity:
    #             raise UserError(_("Location number must less than building capacity."))
    #     return super(Building, self).create(values)

    @api.constrains('location_ids')
    def check_capacity(self):
        for record in self:
            if len(record.location_ids) > record.building_capacity:
                raise UserError(_("Location number must not larger than building capacity."))
    
class BuildingType(models.Model):
    _name = "building.type"
    _description = "Building Type"

    building_type = fields.Char(string='Building Type', required=True)
    buildingtype_desc = fields.Char(string='Description', required=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.buildingtype_desc, record.building_type)))
        return result

class RoomLocation(models.Model):
    _name = "room.location"
    _description = "Room Location"

    location_code = fields.Char(string='Code', size=3, required=True)
    location_name = fields.Char(string='Name', required=True)

    @api.model
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.location_code,
                                                       record.location_name)))
        return result

class RoomType(models.Model):
    _name = "room.type"
    _description = "Room Type"

    code = fields.Char(string='Code', size=3, required=True)
    name = fields.Char(string='Room Type', required=True)
    ratecode_id = fields.Char(string='Rate Code')
    totalroom = fields.Integer(string='Total Rooms')
    image = fields.Binary(string='Image', attachment=True, store=True)
    roomtype_desc = fields.Text(string='Description')

class RoomView(models.Model):
    _name = "room.view"
    _description = "Room View"

    name = fields.Char(string='Room View', required=True)
    roomview_desc = fields.Text(string='Description')

class RoomFacility(models.Model):
    _name = "room.facility"
    _description = "Room Facility"
    _order = 'facilitytype_id'

    name = fields.Char(string="Room Facility", required=True)
    facilitytype_id =  fields.Many2one('room.facility.type', string='Facility Type', required=True)
    facility_desc= fields.Text(string="Description")

class RoomFacilityType(models.Model):
    _name = "room.facility.type"
    _description = "Room Facility Type"

    facility_type = fields.Char(string="Room Facility Type ", size=3, required=True)
    facilitytype_desc = fields.Char(string="Description", required=True)
    
    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, "{} ({})".format(record.facilitytype_desc, record.facility_type)))
        return res

class PropertyRoom(models.Model):
    _name = "property.room"
    _description = "Property Room"
    _group = 'roomlocation_id'

                #   for roomtype in rec.property_id.roomtype_ids:
                #     roomtype_list.append(roomtype.id)
                #     domain = {'roomtype_id': [('id', '=', roomtype_list)]}
                #     return {'domain': domain} 

    # def _default_property_id(self):
    #     rec = self.env['property.property'].browse(self._context.get('active_id'))
    #     return rec
    
    # def _default_roomtype_id(self):
    #     roomtype_list =[]
    #     domain = {}
    #     for rec in self:
    #         if(rec.property_id.roomtype_ids):
    #             for roomtype in rec.property_id.roomtype_ids:
    #                 roomtype_list.append(roomtype.id)
    #                 domain = {'roomtype_id': [('id', '=', roomtype_list)]}
    #         return {'domain': domain} 

    def _default_roomtype_id(self):
        rec = self.env['property.property'].browse(self._context.get('default_property_id'))
        if(rec.roomtype_ids):
            return rec.roomtype_ids
        return False
    
    room_no = fields.Char(string="Room No", required=True)
    property_id = fields.Many2one('property.property', string="Property", required=True)
    roomtype_id = fields.Many2one('room.type', string="Room Type", default=_default_roomtype_id, required=True)
    # roomtype_id = fields.Many2one('room.type', string="Room Type", related='property_id.roomtype_ids', required=True)
    roomview_ids = fields.Many2many('room.view', string="Room View Code")
    building_id = fields.Many2one('building.building', string="Room Building", required=True)
    roomlocation_id = fields.Many2one('room.location', string="Location", required=True)
    facility_ids = fields.Many2many('room.facility', string="Room Facility", required=True)
    ratecode_id = fields.Char(string="Ratecode")
    room_bedqty = fields.Integer(string="Number of Beds", required=True)
    room_size = fields.Char(string="Room Size")
    room_extension = fields.Char(string="Room Extension")
    room_img = fields.Binary(string="Image", attachment=True, store=True)
    room_desc = fields.Text(string="Description")
    room_connect = fields.Char(string="Connecting Room")
    room_fostatus = fields.Char(string="FO Room Status", size=2, default='VC', invisible=True)
    room_hkstatus = fields.Char(string="HK Room Status", size=2, default='VC', invisible=True)
    room_status = fields.Char(string="Room Status",size=2, default='CL', invisible=True) 
    

    # Building Link with Property 
    # @api.onchange('property_id')
    # def onchange_bulding(self):
    #     building_list = []
    #     domain = {}
    #     for rec in self:
    #         if (rec.property_id.building_ids):
    #             for building in rec.property_id.building_ids:
    #                 building_list.append(building.id)
    #             domain = {'building_id': [('id', '=', building_list)]}
    #             return {'domain': domain}

    # Room location link with Building
    @api.onchange('building_id')
    def onchange_room_location_id(self):
        location_list = []
        domain = {}
        for rec in self:
            if (rec.building_id.location_ids):
                for location in rec.building_id.location_ids:
                    location_list.append(location.id)
                domain = {'roomlocation_id': [('id', '=', location_list)]}
                return {'domain': domain}

    # Room Type Link with Property 12.4.20
    # @api.depends('property_id')
    # def _compute_roomtype_id(self):
    #     roomtype_list =[]
    #     domain = {}
    #     for rec in self:
    #         if(rec.property_id.roomtype_ids):
    #             for roomtype in rec.property_id.roomtype_ids:
    #                 roomtype_list.append(roomtype.id)
    #                 domain = {'roomtype_id': [('id', '=', roomtype_list)]}
    #         rec.roomtype_id =domain

    # @api.depends('property_id')
    # def onchange_roomtype_id(self):
    #     roomtype_list = []
    #     domain = {}
    #     for rec in self:
    #         if (rec.property_id.roomtype_ids):
    #             for roomtype in rec.property_id.roomtype_ids:
    #                 roomtype_list.append(roomtype.id)
    #             domain = {'roomtype_id': [('id', '=', roomtype_list)]}
    #             return {'domain': domain}  

    # @api.model
    # def default_get_roomtype_id(self,fields):
    #     res = super(PropertyRoom, self).default_get(fields)
    #     roomtype_list= []
    #     for rec in self:
    #         if('property_id' in fields):
    #             if (rec.property_id.roomtype_ids):
    #                 for roomtype in rec.property_id.roomtype_ids:
    #                     roomtype_list.append(roomtype.id)
    #                 domain = {'roomtype_id': [('id', '=', roomtype_list)]}
    #                 return {'domain': domain}
    
class MarketSegment(models.Model):
    _name="market.segment"
    _description="Maret Segment"
    _order='group_id'

    market_code = fields.Char(string="Market Code", size=3, required=True)
    market_name = fields.Char(string="Market Name", required=True)
    group_id = fields.Many2one('market.group', string="Group Code", required=True)
    options = fields.Selection([
        ('W', 'Walk In'),
        ('H', 'House Use'),
        ('C', 'Complimentary'),
        ('O', 'Others'),], string="Options")

class MarketGroup(models.Model):
    _name = "market.group" 
    _description = "Market Group"

    group_code = fields.Char(string="Group Code", size=3, required=True)
    group_name = fields.Char(string="Group Name", required=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.group_name, record.group_code)))
        return result

class MarketSource(models.Model):
    _name = "market.source"
    _description = "Market Source"

    source_code = fields.Char(string="Source Code", size=3, required=True)
    source_desc = fields.Char(string="Description")

class SpecialDay(models.Model):
    _name = "special.day"
    _description = "Special Day"

    special_date_from = fields.Date(string="Special Date From", required=True)
    special_date_to = fields.Date(string="Special Date To", required=True)
    special_desc = fields.Char(string="Description")

class Weekend(models.Model):
    _name = "weekend.weekend"
    _description = "Weekend"

    monday = fields.Boolean(string="Monday")
    tuesday = fields.Boolean(string="Tuesday")
    wednesday = fields.Boolean(string="Wednesday")
    thursday = fields.Boolean(string="Thursday")
    friday = fields.Boolean(string="Friday")
    saturday = fields.Boolean(string="Saturday")
    sunday = fields.Boolean(string="Sunday")

class Package(models.Model):
    _name = "package.package"
    _description = "Package"

    property_id = fields.Many2one('property.property', string="Property", required=True)
    package_code = fields.Char(string="Package Code", size=3, required=True)
    package_name = fields.Char(string="Package Name", required=True)

class TransactionGroup(models.Model):
    _name = "transaction.group"
    _description = "Transaction Group"    

    property_id = fields.Many2one('property.property', string="Property", required=True, readonly=True)
    group_name = fields.Char(string="Group Name", size=3, required=True)
    group_desc = fields.Char(string="Description")


    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.group_name,
                                                        record.group_desc)))
        return result

class Transaction(models.Model):
    _name = "transaction.transaction"
    _description = "Transaction"

    property_id = fields.Many2one('property.property',
                                  string="Property",
                                  required=True, readonly=True)
    trans_revtype = fields.Selection([
        ('R', 'Revenue'),
        ('F', 'F&B Revenue'),
        ('M', 'Miscellaneous'),
        ('N', 'Non Revenue'),
        ('P', 'Payment'),
    ],
                                     string="Revenue Type",
                                     required=True)
    trans_code = fields.Char(string="Transaction Code", size=4, required=True)
    trans_name = fields.Char(string="Transaction Name", required=True)
    transgroup_id = fields.Many2one('transaction.group',
                                    string="Transaction Group",
                                    required=True)
    trans_unitprice = fields.Float(string="Unit Price", required=True)
    trans_utilities = fields.Selection([
        ('Y', 'Yes'),
        ('N', 'No'),
    ],
                                       string="Utilities",
                                       required=True)
    trans_svc = fields.Boolean(string="Service Charge")
    trans_tax = fields.Boolean(string="Tax")
    trans_internal = fields.Boolean(string="Internal Use")
    trans_minus = fields.Boolean(string="Minus Nature")
    trans_type = fields.Selection([
        ('R', 'Revenue'),
        ('S', 'Service'),
        ('V', 'Tax'),
    ],
                                  string="Transaction Type")