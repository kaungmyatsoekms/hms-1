from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError
from odoo.modules import get_module_resource
#from odoo.tools import image_colorize, image_resize_image_big
from odoo.tools import *
import base64

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
    code = fields.Char(string='Hotel Code', required=True)
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
    roomqty = fields.Integer(string='Total Rooms')
    property_license = fields.Char(string='Property License')
    rating = fields.Selection([
        ('one', 'One Star'),
        ('two', 'Two Star'),
        ('three', 'Three Star'),
        ('four', 'Four Star'),
        ('five', 'Five Star'),
    ],
                              string='Property Rating')
    logo = fields.Binary(string='Logo', attachment=True, store=True)
    image = fields.Binary(string='Image', attachment=True, store=True)
    contact_ids = fields.Many2many('contact.contact')
    bankinfo_ids = fields.Many2many('bank.info', string="Bank Info")
    comments = fields.Text(string='Notes')
    roomtype_ids = fields.Many2many('room.type')
    building_ids = fields.Many2many('building.building')
    propertyroom_ids = fields.One2many('property.room','property_id', string="Property Room")
    building_count = fields.Integer("Building",
                                    compute='_compute_building_count')

    # @api.depends('propertyroom_ids')
    # def _compute_property_id(self):
    #     for statement in self:
    #         statement.propertyroom_ids.property_id = statement.property.id

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
    
    def _compute_building_count(self):
        self.building_count = len(self.building_ids)
    
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

    bank_name = fields.Char(string="Bank Name", required=True)
    bank_branch = fields.Char(string="Branch Name", required=True)
    bank_account = fields.Char(string="Bank Account", required=True)
    bank_desc = fields.Text(string="Description")


class Building(models.Model):
    _name = "building.building"
    _description = "Building"
    _rec_name = 'building_type'

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

    # @api.model
    # def name_get(self):
    #     result = []
    #     for record in self:
    #         result.append((record.id, "{}".format(record.building_name)))
    #     return result

    
    # @api.depends('building_capacity','location_ids')
    # def _room_location_count(self):
       
    #         return len(locations)

    @api.model
    def create(self, values):
        locations = values['location_ids']
        building_capacity = values['building_capacity']
        if values['location_ids'][0][2]:
            if len(values['location_ids'][0][2]) > building_capacity:
                raise UserError(_("Location number must less than building capacity."))
        return super(Building, self).create(values)


    
class BuildingType(models.Model):
    _name = "building.type"
    _description = "Building Type"

    building_type = fields.Char(string='Building Type', required=True)
    buildingtype_desc = fields.Char(string='Description', required=True)

    @api.model
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.buildingtype_desc,
                                                       record.building_type)))
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
    _rec_name = 'facilitytype_desc'

    facility_type = fields.Char(string="Room Facility Type ", size=3, required=True)
    facilitytype_desc = fields.Char(string="Description", required=True)
    
    # @api.model
    # def name_get(self):
    #     res = []
    #     for record in self:
    #         res.append((record.id, "{} ({})".format(record.facilitytype_desc, record.facility_type)))
    #     return res


class PropertyRoom(models.Model):
    _name = "property.room"
    _description = "Property Room"

    room_no = fields.Char(string="Room No", required=True)
    property_id = fields.Many2one('property.property', string="Property", required=True)
    roomtype_id = fields.Many2one('room.type', string="Room Type", required=True)
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

    # def open_one2many_line(self):
    #     context = self.env.context
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Open Line',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'property.room',
    #         'res_id': context.get('default_active_id'),
    #         'target': 'new',
    #     }


    # def _get_default_property_id(self, cr, uid, context=None):
    #     res = self.pool.get('property.property').search(cr, uid, [('property_id','=','')], context=context)
    #     return res and res[0] or False

    # Building Link with Property 
    @api.onchange('property_id')
    def onchange_property_id(self):
        building_list =[]
        domain={}
        for rec in self:
            if(rec.property_id.building_ids):
                for building in rec.property_id.building_ids:
                    building_list.append(building.id)
                domain = {'building_id':[('id','=', building_list)]}
                return{'domain': domain}
    
    # Room Type link with Property
    @api.onchange('property_id')
    def onchange_property_id1(self):
        roomtype_list =[]
        domain={}
        for rec in self:
            if(rec.property_id.roomtype_ids):
                for roomtype in rec.property_id.roomtype_ids:
                    roomtype_list.append(roomtype.id)
                domain = {'roomtype_id':[('id','=', roomtype_list)]}
                return{'domain': domain}

    # Room location link with Building
    @api.onchange('building_id')
    def onchange_building_id(self):
        location_list = []
        domain ={}
        for rec in self:
            if (rec.building_id.location_ids):
                for location in rec.building_id.location_ids:
                    location_list.append(location.id)
                domain = {'roomlocation_id': [('id','=', location_list)]}
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

class MarketGroup(models.Model):
    _name = "market.group" 
    _description = "Market Group"

    group_code = fields.Char(string="Group Code", size=3, required=True)
    group_name = fields.Char(string="Group Name", required=True)


    @api.model
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.group_code, record.group_name)))
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

    package_code = fields.Char(string="Package Code", size=3, required=True)
    package_name = fields.Char(string="Package Name", required=True)