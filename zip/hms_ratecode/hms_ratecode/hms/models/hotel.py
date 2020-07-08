from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules import get_module_resource
#from odoo.tools import image_colorize, image_resize_image_big
from odoo.tools import *
import base64
import datetime

AVAILABLE_STARS = [
    ('0', 'Low'),
    ('1', 'One Star'),
    ('2', 'Two Star'),
    ('3', 'Three Star'),
    ('4', 'Four Star'),
    ('5', 'Five Star'),
]

AVAILABLE_REV = [
    ('R', 'Room Revenue'),
    ('F', 'F&B Revenue'),
    ('M', 'Miscellaneous'),
    ('N', 'Non Revenue'),
    ('P', 'Payment'),
]

AVAILABLE_PAY = [
    ('CA', 'Cash'),
    ('CL', 'City Ledger'),
    ('AX', 'Amex Card'),
    ('DC', 'Diners Club'),
    ('MC', 'Master Card'),
    ('VS', 'Visa Card'),
    ('LC', 'Local Card'),
    ('CU', 'Union Pay'),
    ('OT', 'Others'),
]



class HotelGroup(models.Model):
    _name = "hotel.group"
    _description = "Hotel Group"

    name = fields.Char(string='Hotel Group Name', required=True)

class Property(models.Model):
    _name = "property.property"
    _description = "Property"

    is_property = fields.Boolean(string ='Is Property', compute='_compute_is_property')
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
    market_ids = fields.Many2many('market.segment', string="Market Segment")
    propertyroom_ids = fields.One2many('property.room','property_id', string="Property Room")
    building_count = fields.Integer("Building", compute='_compute_building_count')
    room_count = fields.Integer("Room", compute='_compute_room_count')
    roomtype_count = fields.Integer("Room Type", compute='_compute_roomtype_count')
    package_ids = fields.One2many('package.package', 'property_id', string="Package")
    subgroup_ids = fields.One2many('sub.group','property_id',string="Sub Group")
    transgroup_ids = fields.One2many('transaction.group','property_id', string="Transaction Group")
    transaction_ids = fields.One2many('transaction.transaction', 'property_id', string="Transaction")
    creditlimit_ids = fields.One2many('credit.limit', 'property_id', string="Credit Limit")
    weekend_id = fields.One2many('weekend.weekend', 'property_id', string="Weekends")
    ratecode_ids = fields.One2many('rate.code','property_id', string="Rate Code")

    _sql_constraints = [('code_unique', 'UNIQUE(code)',
                         'Hotel ID already exists! Hotel ID must be unique!')]

    def _compute_is_property(self):
        self.is_property=True

    def action_weekend(self):
        weekend= self.mapped('weekend_id')
        action = self.env.ref('hms.weekend_action_window').read()[0]
        if(len(weekend)) == 1:
            # action['domain'] = [('id', '=', weekend.id)]
            form_view = [(self.env.ref('hms.weekend_view_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] 
                        if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = weekend.id
        elif len(weekend) == 0:
            form_view = [(self.env.ref('hms.weekend_view_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] 
                        if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = weekend.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        context = {
            'default_type': 'out_weekend',
        }
        return action

    def action_package(self):
        packages = self.mapped('package_ids')
        action = self.env.ref('hms.package_action_window').read()[0]
        if len(packages) >= 1:
            action['domain'] = [('id', 'in', packages.ids)]
        elif len(packages) == 0:
            form_view = [(self.env.ref('hms.package_view_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = packages.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        context = {
            'default_type': 'out_package',
        }
        return action

    def action_transaction(self):
        transactions = self.mapped('transaction_ids')
        action = self.env.ref('hms.transaction_action_window').read()[0]
        if len(transactions) >= 1:
            action['domain'] = [('id', 'in', transactions.ids)]
        elif len(transactions) == 0:
            form_view = [(self.env.ref('hms.transaction_view_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = transactions.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        context = {
            'default_type': 'out_transaction',
        }
        return action

    def action_ratecode(self):
        rate_code = self.mapped('ratecode_ids')
        action = self.env.ref('hms.rate_code_action_window').read()[0]
        if len(rate_code) >= 1:
            action['domain'] = [('id', 'in', rate_code.ids)]
        elif len(rate_code) == 0:
            form_view = [(self.env.ref('hms.rate_code_view_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = rate_code.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        context = {
            'default_type': 'out_ratecode',
        }
        return action

    def action_creditlimit(self):
        credit_limit = self.mapped('creditlimit_ids')
        action = self.env.ref('hms.credit_limit_action_window').read()[0]
        if len(credit_limit) >= 1:
            action['domain'] = [('id', 'in', credit_limit.ids)]
        elif len(credit_limit) == 0:
            form_view = [(self.env.ref('hms.credit_limit_view_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = credit_limit.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        context = {
            'default_type': 'out_creditlimit',
        }
        return action

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
    building_capacity = fields.Integer(string='Capacity', default=1, required=True)
    location_ids = fields.Many2many('room.location', string="Room Location", required=True)
    # location_number = fields.Integer("Location Number", compute="_room_location_count", readonly=True)

    _sql_constraints = [
        ('building_name_unique', 'UNIQUE(building_name)',
         'Building name already exists! Building name must be unique!')
    ]

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
    def _check_capacity(self):
        for record in self:
            if len(record.location_ids) > record.building_capacity:
                raise UserError(_("Location number must not larger than building capacity."))
    
class BuildingType(models.Model):
    _name = "building.type"
    _description = "Building Type"

    building_type = fields.Char(string='Building Type', required=True)
    buildingtype_desc = fields.Char(string='Description', required=True)

    _sql_constraints = [(
        'building_type_unique', 'UNIQUE(building_type)',
        'Building type already exists with this name! Building type name must be unique!'
    )]

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

    _sql_constraints = [(
        'location_code_unique', 'UNIQUE(location_code)',
        'Location code already exists with this name! Location code must be unique!'
    )]

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
    ratecode_id = fields.Many2one('rate.code',string='Rate Code')
    totalroom = fields.Integer(string='Total Rooms')
    image = fields.Binary(string='Image', attachment=True, store=True)
    roomtype_desc = fields.Text(string='Description')

    # propertyroom_ids = fields.One2many('property.room',
    #                                    'roomtype_id',
    #                                    string="Property Room")
    # count_roomtype = fields.Integer(
    #     string="Total Room",
    #     compute='count_room_no',
    #     store=True,
    #     help='Contains number of room that belong to this room type')

    _sql_constraints = [(
        'code_unique', 'UNIQUE(code)',
        'Room code already exists with this name! Room code name must be unique!'
    )]

    # @api.depends('propertyroom_ids')
    # def count_room_no(self):
    #     for roomtype in self:
    #         roomtype.count_roomtype = len(roomtype.propertyroom_ids)

class RoomView(models.Model):
    _name = "room.view"
    _description = "Room View"

    name = fields.Char(string='Room View', required=True)
    roomview_desc = fields.Text(string='Description')

    _sql_constraints = [(
        'name_unique', 'UNIQUE(name)',
        'Room view already exists with this name! Room view name must be unique!'
    )]

class RoomFacility(models.Model):
    _name = "room.facility"
    _description = "Room Facility"
    _order = 'facilitytype_id'

    amenity_ids = fields.Many2many('room.amenity',string="Room Facility", required=True)
    facilitytype_id =  fields.Many2one('room.facility.type', string='Facility Type', required=True)
    facility_desc= fields.Text(string="Description")

class RoomAmenitiy(models.Model):
    _name = "room.amenity"
    _description = "Room Amenity"

    name = fields.Char(string="Amenity Name", required=True)
    amenity_desc = fields.Text(string="Descripton")

class RoomFacilityType(models.Model):
    _name = "room.facility.type"
    _description = "Room Facility Type"

    facility_type = fields.Char(string="Room Facility Type ", help='Eg. EQP.....', size=3, required=True)
    facilitytype_desc = fields.Char(string="Description", help='Eg.Room Equipment.....', required=True)
    
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


    # @api.model
    # def _default_roomtype_id(self):
    #     roomtype_list =[]
    #     domain = {}
    #     property_id = self.env['property.property'].browse(self._context.get('default_property_id'))
    #     if  property_id.roomtype_ids:
    #         for roomtype in property_id.roomtype_ids:
    #             roomtype_list.append(roomtype.id)
    #         domain = {'roomtype_id':  [('id', 'in', roomtype_list)]} 
    #         return {'domain': domain}

    # def _default_property_id(self):
    #     rec = self.env['property.property'].browse(self._context.get('active_id'))
    #     return rec

    # def _default_roomtype_id(self):
    #     rec = self.env['property.property'].browse(self._context.get('default_property_id'))
    #     if(rec.roomtype_ids):
    #         return rec.roomtype_ids
    #     return False
    
    room_no = fields.Char(string="Room No", required=True)
    property_id = fields.Many2one('property.property', string="Property", required=True, readonly=True)
    roomtype_ids = fields.Many2many("room.type", related="property_id.roomtype_ids")
    roomtype_id = fields.Many2one('room.type', string="Room Type", domain="[('id', '=?', roomtype_ids)]", required=True)
    roomview_ids = fields.Many2many('room.view', string="Room View Code")
    building_ids = fields.Many2many("building.building", related="property_id.building_ids")
    building_id = fields.Many2one('building.building', string="Room Building", domain="[('id', '=?', building_ids)]", required=True)
    roomlocation_id = fields.Many2one('room.location', string="Location", required=True)
    facility_ids = fields.Many2many('room.facility', string="Room Facility", required=True)
    ratecode_id = fields.Many2one('rate.code',string="Ratecode")
    room_bedqty = fields.Integer(string="Number of Beds", required=True, default=1, size=2)
    room_size = fields.Char(string="Room Size")
    room_extension = fields.Char(string="Room Extension")
    room_img = fields.Binary(string="Image", attachment=True, store=True)
    room_desc = fields.Text(string="Description")
    room_connect = fields.Char(string="Connecting Room")
    room_fostatus = fields.Char(string="FO Room Status", size=2, default='VC', invisible=True)
    room_hkstatus = fields.Char(string="HK Room Status", size=2, default='VC', invisible=True)
    room_status = fields.Char(string="Room Status",size=2, default='CL', invisible=True) 

    _sql_constraints = [
        ('room_no_unique', 'UNIQUE(property_id, room_no)',
         'Room number already exists! Room number must be unique!')
    ]

    # Room location link with Building
    @api.onchange('building_id')
    def onchange_room_location_id(self):
        location_list = []
        domain = {}
        for rec in self:
            if (rec.building_id.location_ids):
                for location in rec.building_id.location_ids:
                    location_list.append(location.id)
                domain = {'roomlocation_id': [('id', 'in', location_list)]}
                return {'domain': domain}
                
    
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
    
    _sql_constraints = [(
        'market_code_unique', 'UNIQUE(market_code)',
        'Market code already exists with this name! Market code must be unique!'
    )]

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.market_name, record.market_code)))
        return result

class MarketGroup(models.Model):
    _name = "market.group" 
    _description = "Market Group"

    group_code = fields.Char(string="Group Code", help='Eg. COR.....', size=3, required=True)
    group_name = fields.Char(string="Group Name", help='Eg. Corporate.....', required=True)

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

    _sql_constraints = [(
        'source_code_unique', 'UNIQUE(source_code)',
        'Source code already exists with this name! Source code must be unique!'
    )]

class SpecialDay(models.Model):
    _name = "special.day"
    _description = "Special Day"
    _rec_name = 'special_date'

    property_id = fields.Many2one('property.property',
                                  string="Property",
                                  required=True)
    special_date = fields.Date(string="Special Date", required=True)
    special_desc = fields.Char(string="Description")

class Weekend(models.Model):
    _name = "weekend.weekend"
    _description = "Weekend"

    property_id = fields.Many2one('property.property',
                                  string="Property",
                                  required=True)
    monday = fields.Boolean(string="Monday")
    tuesday = fields.Boolean(string="Tuesday")
    wednesday = fields.Boolean(string="Wednesday")
    thursday = fields.Boolean(string="Thursday")
    friday = fields.Boolean(string="Friday", default=True)
    saturday = fields.Boolean(string="Saturday", default=True)
    sunday = fields.Boolean(string="Sunday")

class Package(models.Model):

    _name = "package.package"
    _description = "Package"

    property_id = fields.Many2one('property.property', string="Property", readonly=True, required=True)
    package_code = fields.Char(string="Package Code", size=4, required=True)
    package_name = fields.Char(string="Package Name", required=True)

    _sql_constraints = [(
        'package_code_unique', 'UNIQUE(property_id, package_code)',
        'Package code already exists with this name! Package code must be unique!'
    )]


class RevenueType(models.Model):
    _name = "revenue.type"
    _description = "Revenue Type"    

    rev_code = fields.Char(string="Group Code", size=1, required=True)
    rev_type = fields.Selection(AVAILABLE_REV, string="Revenue Type", required=True)
    revtype_name = fields.Char(string="Revenue")
    rev_subgroup = fields.Boolean(string="Sub Group")
    subgroup_ids = fields.One2many('sub.group','revtype_id',string="Sub Group")
    transaction_id = fields.Many2one('transaction.transaction','trans_revtype')

    _sql_constraints = [(
        'rev_code_unique', 'UNIQUE(rev_code)',
        'This code already exists with this name! This Group code must be unique!'
    )]

    # def _compute_revtype_name(self):
    #     # self.revtype_name = dict(AVAILABLE_REV)[self.rev_type]
    #     # self.revtype_name = dict(self._fields['rev_type']._description_selection(self.env))
    #     self.revtype_name = dict(self.fields_get(allfields=['rev_type'])['rev_type']['selection'])['1']

    # dict(self._fields['rev_type']._description_selection(self.env)) --> get description
    # @api.onchange('rev_type')
    # def onchange_revtype_name(self):
    #     for record in self:
    #         for item in VALUES:
    #             if item[0] == self.rev_type:
    #             record.revtype_name = item[1]
        # self.revtype_name= dict(AVAILABLE_REV)[self.rev_type]


    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "({} {}) {}".format(record.rev_code, record.rev_type,record.revtype_name)))
        return result

    @api.onchange('rev_type')
    def onchange_rev_code(self):
        for record in self:
            rev_type = record.rev_type
            record.revtype_name = dict(AVAILABLE_REV)[record.rev_type]
            if rev_type == 'P':
                 record.rev_code = '9'
            elif rev_type =='N':
                record.rev_code = '8'
            else:
                record.rev_code = ''


    @api.constrains('rev_code','rev_type')
    def _check_rev_code(self):
        for record in self:
            rev_code = record.rev_code
            rev_type = record.rev_type
            if rev_code and not str(rev_code).isdigit():
                raise UserError(_("Transaction code must be digit"))
            else:
                if rev_code == '0':
                    raise UserError(_("This code not start with '0'"))
                else:
                    if rev_type == 'P':
                        if int(rev_code) != 9:
                            raise UserError(_("Payment code must be 9 "))
                    elif rev_type =='N':
                        if int(rev_code) != 8:
                            raise UserError(_("Non Revenue code must be 8"))
                    elif rev_type !='P' and rev_type !='N':
                        if int(rev_code) == 8 or int(rev_code) == 9:
                            raise UserError(_("Revenue code must be 1 ~ 7 "))                    

# Revenue Sub Group
class SubGroup(models.Model):
    _name = "sub.group"
    _description = "Revenue Sub Group"    

    property_id = fields.Many2one('property.property', string="Property", required=True)
    revtype_id = fields.Many2one('revenue.type', string="Revenue Type", domain="[('rev_subgroup', '=?', True)]", required=True)
    revtype_name = fields.Char(string="Revenue")
    sub_group = fields.Char(string="Sub Group Code", size=1, required=True)
    sub_desc = fields.Char(string="Description", required=True)
    transsub_id = fields.Many2one('transaction.transaction','subgroup_id')


    _sql_constraints = [(
        'sub_group_unique', 'UNIQUE(property_id, revtype_id, sub_group)',
        'This Sub Group code already exists with this name! This code must be unique!'
    )]

    # @api.onchange('revtype_id')
    # def onchange_revtype_name(self):
    #     for record in self:
    #         revtype_id = self.revtype_id
    #         record.revtype_name = dict(self._fields['revtype_id']._description_selection(self.env))

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "({}) {}".format(record.sub_group, record.sub_desc)))
        return result

    @api.constrains('sub_group')
    def _check_sub_group(self):
        for record in self:
            sub_code = record.sub_group
            if sub_code and not str(sub_code).isdigit():
                raise UserError(_("Transaction code must be digit"))

# Transaction Group
class TransactionGroup(models.Model):
    _name = "transaction.group"
    _description = "Transaction Group"    

    property_id = fields.Many2one('property.property', string="Property", required=True)
    group_name = fields.Char(string="Sub Group Code", size=1, required=True)
    group_desc = fields.Char(string="Description", required=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "({}) {}".format(record.group_name, record.group_desc)))
        return result

    # def name_get(self):
    #     result = []
    #     for record in self:
    #         if record.group_desc:
    #             name="{} ({})".format(record.group_desc,
    #             record.group_name)
    #         else:
    #             name="{}".format(record.group_name)
    #     result.append((record.id,name))
    #     return result

class Transaction(models.Model):
    _name = "transaction.transaction"
    _description = "Transaction"

    property_id = fields.Many2one('property.property',
                                  string="Property",
                                  required=True, readonly=True)
    # trans_revtypeids = fields.One2many("sub.group", 'property_id', related="property_id.revtype_id")
    revtype_id = fields.Many2one('revenue.type', string="Revenue Type", required=True)
    revtype_name = fields.Char(String="Revenue Type")
    trans_ptype = fields.Selection(AVAILABLE_PAY,string="Pay Type")
    subgroup_id = fields.Many2one('sub.group', string="Sub Group")
    subgroup_name = fields.Char(string="Sub Group Name")
    # trans_revtype = rev_type = fields.Selection(AVAILABLE_REV, string="Revenue Type", required=True)
    trans_code = fields.Char(string="Transaction Code", size=4, required=True, index=True)
    trans_name = fields.Char(string="Transaction Name", required=True)
    # transgroup_ids = fields.One2many("transaction.group", 'property_id', related="property_id.transgroup_ids")
    # transgroup_id = fields.Many2one("transaction.group", string="Transaction Group", domain="[('id', '=?', transgroup_ids)]", required=True)
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
    root_id = fields.Many2one('transaction.root', compute='_compute_transaction_root', store=True)

    _sql_constraints = [(
        'trans_code_unique', 'UNIQUE(property_id, trans_code)',
        'Transaction code already exists with this name! Transaction code must be unique!'
    )]


    @api.onchange('subgroup_id')
    def onchange_sub_name(self):
        for record in self:
            subgroup_id = record.subgroup_id
            record.subgroup_name=subgroup_id.sub_desc

    @api.onchange('revtype_id')
    def onchange_revtype_name(self):
        for record in self:
            revtype_id = record.revtype_id
            record.revtype_name  =revtype_id.revtype_name

    # def _compute_get_sub_name(self):
    #     self.subgroup_name=self.subgroup_id.sub_desc

    # @api.constrains('trans_code','trans_revtype')
    # def _check_trans_code(self):
    #     for record in self:
    #         trans_revtype=record.trans_revtype
    #         trans_code=record.trans_code
    #         if trans_revtype == 'P':
    #             if trans_code and not str(trans_code).isdigit():
    #                 raise UserError(_("Transaction code must be digit"))
    #             else:
    #                 if int(record.trans_code) < 9000:
    #                     raise UserError(_("Payment Code must be greather than 9000 "))
                   
    #         elif record.trans_revtype != 'P':
    #             if trans_code and not str(trans_code).isdigit():
    #                 raise UserError(_("Transaction code must be digit"))
    #             else:
    #                 if int (record.trans_code) > 9000:
    #                     raise UserError(_("Revenue code must be less than 9000 "))

    @api.depends('trans_code')
    def _compute_transaction_root(self):
        # this computes the first 2 digits of the transaction.
        # This field should have been a char, but the aim is to use it in a side panel view with hierarchy, and it's only supported by many2one fields so far.
        # So instead, we make it a many2one to a psql view with what we need as records.
        for record in self:
            record.root_id = record.trans_code and (ord(record.trans_code[0]) * 1000 + ord(record.trans_code[1])) or False

# class Transaction(models.Model):
#     _name = "transaction.transaction"
#     _description = "Transaction"

#     property_id = fields.Many2one('property.property',
#                                   string="Property",
#                                   required=True, readonly=True)
#     trans_revtype = fields.Selection([
#         ('R', 'Room Revenue'),
#         ('F', 'F&B Revenue'),
#         ('M', 'Miscellaneous'),
#         ('N', 'Non Revenue'),
#         ('P', 'Payment'),
#     ],
#                                      string="Revenue Type",
#                                      required=True)
#     trans_code = fields.Char(string="Transaction Code", size=4, required=True, index=True)
#     trans_name = fields.Char(string="Transaction Name", required=True)
#     transgroup_ids = fields.One2many("transaction.group", 'property_id', related="property_id.transgroup_ids")
#     transgroup_id = fields.Many2one("transaction.group", string="Transaction Group", domain="[('id', '=?', transgroup_ids)]", required=True)
#     trans_unitprice = fields.Float(string="Unit Price", required=True)
#     trans_utilities = fields.Selection([
#         ('Y', 'Yes'),
#         ('N', 'No'),
#     ],
#                                        string="Utilities",
#                                        required=True)
#     trans_svc = fields.Boolean(string="Service Charge")
#     trans_tax = fields.Boolean(string="Tax")
#     trans_internal = fields.Boolean(string="Internal Use")
#     trans_minus = fields.Boolean(string="Minus Nature")
#     trans_type = fields.Selection([
#         ('R', 'Revenue'),
#         ('S', 'Service'),
#         ('V', 'Tax'),
#     ],
#                                   string="Transaction Type")
#     root_id = fields.Many2one('transaction.root', compute='_compute_transaction_root', store=True)

#     _sql_constraints = [(
#         'trans_code_unique', 'UNIQUE(property_id, trans_code)',
#         'Transaction code already exists with this name! Transaction code must be unique!'
#     )]

#     @api.constrains('trans_code','trans_revtype')
#     def _check_trans_code(self):
#         for record in self:
#             trans_revtype=record.trans_revtype
#             trans_code=record.trans_code
#             if trans_revtype == 'P':
#                 if trans_code and not str(trans_code).isdigit():
#                     raise UserError(_("Transaction code must be digit"))
#                 else:
#                     if int(record.trans_code) < 9000:
#                         raise UserError(_("Payment Code must be greather than 9000 "))
                   
#             elif record.trans_revtype != 'P':
#                 if trans_code and not str(trans_code).isdigit():
#                     raise UserError(_("Transaction code must be digit"))
#                 else:
#                     if int (record.trans_code) > 9000:
#                         raise UserError(_("Revenue code must be less than 9000 "))

#     @api.depends('trans_code')
#     def _compute_transaction_root(self):
#         # this computes the first 2 digits of the transaction.
#         # This field should have been a char, but the aim is to use it in a side panel view with hierarchy, and it's only supported by many2one fields so far.
#         # So instead, we make it a many2one to a psql view with what we need as records.
#         for record in self:
#             record.root_id = record.trans_code and (ord(record.trans_code[0]) * 1000 + ord(record.trans_code[1])) or False
                    
# Transaction Root
class TransactionRoot(models.Model):
    _name = 'transaction.root'
    _description = 'Transaction codes first 2 digits'
    _auto = False

    name = fields.Char()
    revname = fields.Char()
    parent_id = fields.Many2one('transaction.root', string="Superior Level")
    group = fields.Many2one('sub.group')
    # transgroup_id = fields.Many2one('transaction.group')

                    #   LEFT(trans_code,2) AS name, LEFT(revtype_id,1)
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
            SELECT DISTINCT ASCII(trans_code) * 1000 + ASCII(SUBSTRING(trans_code,2,1)) AS id,
                   LEFT(trans_code,2) AS name,
                   subgroup_name as revname,
                   ASCII(trans_code) AS parent_id,
                   subgroup_id as group
            FROM transaction_transaction WHERE trans_code IS NOT NULL AND subgroup_id IS NOT NULL
            UNION ALL
            SELECT DISTINCT ASCII(trans_code) AS id,
                   LEFT(trans_code,1) AS name,
                   revtype_name as revname,
                   NULL::int AS parent_id,
                   subgroup_id as group
            FROM transaction_transaction WHERE trans_code IS NOT NULL
            )''' % (self._table,)
        )

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "({}) {}".format(record.revname, record.name)))
        return result

# Reservation Type
class RsvnType(models.Model):
    _name = "rsvn.type"
    _description = "Reservation Type"

    rsvn_name = fields.Char(string="Reservation Type", size=30, required=True)
    rsvn_options = fields.Selection([
        ('CF', 'Confirmed'),
        ('UC', 'Unconfirmed'),
    ], string="Options", required=True)
    
#Reservation Status
class RsvnStatus(models.Model):

    _name = "rsvn.status"
    _description = "Reservation Status"

    rsvn_code = fields.Char(string="Reservation Status", size=3, required=True)
    rsvn_status = fields.Char(string="Description", required=True)

#Credit Limit
class CreditLimit(models.Model):
    _name = "credit.limit"
    _description = "Credit Limit"
    _group = 'payment_type'


    property_id = fields.Many2one('property.property',
    string="Property",
    required=True, readonly=True)
    payment_type = fields.Selection([
    ('CA','Cash'),
    ('CL','City Ledger'),
    ('AX','American Express'),
    ('DC','Diner Club'),
    ('MC','Master Card'),
    ('VS','Visa Card'),
    ('JC','JCB Card'),
    ('LC','Local Card'),
    ('UP','Union Pay Card'),
    ('OT','Others'),
    ],
    string="Payment Type")
    crd_startdate = fields.Date(string="Start Date", required=True)
    crd_enddate = fields.Date(string="End Date",required=True)#compute="get_end_date",
    crd_limit = fields.Float(string="Credit Limit")

    @api.onchange('crd_startdate','crd_enddate')
    @api.constrains('crd_startdate','crd_enddate')
    def get_two_date_comp(self):
        start_date = self.crd_startdate
        end_date = self.crd_enddate
        if start_date and end_date and start_date > end_date:
            raise ValidationError("End Date cannot be set before Start Date.")

    @api.onchange('payment_type','crd_enddate')
    def get_end_date(self):
        same_payment_objs = self.env['credit.limit'].search([('payment_type','=',self.payment_type)])
        tmp_end_date = datetime.date(1000, 1, 11)
        same_payment = self.env['credit.limit'] # This is Null Object assignment
        for rec in same_payment_objs:
            if rec.crd_enddate > tmp_end_date:
                tmp_end_date = rec.crd_enddate
                same_payment = rec
            if same_payment:
                self.crd_startdate = same_payment.crd_enddate + timedelta(days = 1)

#Rate Code
class RateCode(models.Model):
    _name = "rate.code"
    _description = "Rate Code"
    

    property_id = fields.Many2one('property.property',
                                  string="Property",
                                  required=True, readonly=True)
    rate_code = fields.Char(string="Rate Code", required=True)
    ratecode_name = fields.Char(string="Rate Code Name", required=True, size=10)
    roomtype_id = fields.Many2one('room.type', string="Room Type", required=True)
    transcation_id = fields.Many2one('transcation.transcation', string="Transcation")
    ratecode_type = fields.Char(string="Rate Code Type", required=True)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    normal_price1 = fields.Integer(string="Normal Price 1")
    normal_price2 = fields.Integer(string="Normal Price 2")
    normal_price3 = fields.Integer(string="Normal Price 3")
    normal_price4 = fields.Integer(string="Normal Price 4")
    weekend_price1 = fields.Integer(string="Weekend Price 1")
    weekend_price2 = fields.Integer(string="Weekend Price 2")
    weekend_price3 = fields.Integer(string="Weekend Price 3")
    weekend_price4 = fields.Integer(string="Weekend Price 4")
    special_price1 = fields.Integer(string="Special Price 1")
    special_price2 = fields.Integer(string="Special Price 2")
    special_price3 = fields.Integer(string="Special Price 3")
    special_price4 = fields.Integer(string="Special Price 4")

    @api.onchange('start_date','end_date')
    @api.constrains('start_date','end_date')
    def get_two_date_comp(self):
        startdate = self.start_date
        enddate = self.end_date
        if startdate and enddate and startdate > enddate:
            raise ValidationError("End Date cannot be set before Start Date.")

    @api.onchange('rate_code','end_date')
    def get_end_date(self):
        same_ratecode_objs = self.env['rate.code'].search([('rate_code','=',self.rate_code)])
        tmp_end_date = datetime.date(1000, 1, 11)
        same_ratecode = self.env['rate.code'] # This is Null Object assignment
        for rec in same_ratecode_objs:
            if rec.end_date > tmp_end_date:
                tmp_end_date = rec.end_date
                same_ratecode = rec
            if same_ratecode:
                self.start_date = same_ratecode.end_date + timedelta(days = 1)

    # def name_get(self):
    #     result = []
    #     for record in self:
    #         result.append((record.id, "({}) {}".format(record.rate_code, record.record_name)))
    #     return result
                
    # property_id = fields.Many2one('property.property',
    #                               string="Property",
    #                               required=True, readonly=True)
    # crd_startdate = fields.Date(string="Start Date", required=True)
    # crd_enddate = fields.Date(string="End Date", required=True)
    # crd_cash = fields.Float(string="Cash")
    # crd_cl = fields.Float(string="City Ledger")
    # crd_ax = fields.Float(string="Amex Card")
    # crd_dc = fields.Float(string="Diner Club")
    # crd_mc = fields.Float(string="Master Card")
    # crd_vs = fields.Float(string="Visa Card")
    # crd_jcb = fields.Float(string="JCB Card")
    # crd_lc = fields.Float(string="Local Card")
    # crd_un = fields.Float(string="Union Pay Card")
    # crd_others = fields.Float(string="Others")

    # @api.onchange('crd_startdate','crd_enddate')
    # @api.constrains('crd_startdate','crd_enddate')
    # def get_two_date_comp(self):
    #     for record in self:
    #         start_date = record.crd_startdate
    #         end_date = record.crd_enddate
    #         if start_date and end_date and start_date > end_date:
    #             raise ValidationError("End Date cannot be set before Start Date.")

