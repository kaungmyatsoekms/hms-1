from odoo import models, fields, api, tools


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
    name = fields.Char(required=True, index=True)
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
    comments = fields.Text(string='Notes')
    building_ids = fields.One2many('building.building',
                                   'property_id',
                                   string="Buildings")
    building_count = fields.Integer("Building",
                                    compute='_compute_building_count')

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


class Contact(models.Model):
    _name = "contact.contact"
    _description = "Contact"

    name = fields.Char(string='Contact Person', required=True)
    image = fields.Binary(string='Image', attachment=True, store=True)
    title = fields.Many2one('res.partner.title')
    position = fields.Char(string='Job Position')
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')


class Building(models.Model):
    _name = "building.building"
    _description = "Building"

    name = fields.Char(string='Building Name', required=True)
    building_type = fields.Many2one('building.type',
                                    string='Building Types',
                                    required=True)
    building_location = fields.Char(string='Location')
    building_img = fields.Binary(string='Building Image',
                                 attachment=True,
                                 store=True)
    building_des = fields.Text(string='Description')
    property_id = fields.Many2one('property.property',
                                  String="Property Name",
                                  required=True)


class BuildingType(models.Model):
    _name = "building.type"
    _description = "Building Type"

    name = fields.Char(string='Building Type', required=True)
    code = fields.Char(string='Building Type Code', required=True)

    @api.model
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.name,
                                                       record.code)))
        return result


class RoomLocation(models.Model):
    _name = "room.location"
    _description = "Room Location"

    property_id = fields.Many2one('property.property',
                                  string="Property",
                                  required=True)
    area_type = fields.Many2one('area.type',
                                string='Area Types',
                                required=True)
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    description = fields.Text(string='Description')


class AreaType(models.Model):
    _name = "area.type"
    _description = "Area Type"

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)

    @api.model
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.name,
                                                       record.code)))
        return result


class RoomType(models.Model):
    _name = "room.type"
    _description = "Room Type"

    name = fields.Char(string='Room Name', required=True)
    code = fields.Char(string='Room Code', required=True)
    rate = fields.Char(string='Room Price', required=True)
    bedqty = fields.Integer(string='Number of Beds', required=True)
    roomtotal = fields.Integer(string='Total Rooms', required=True)
    img = fields.Binary(string='Image', attachment=True, store=True)
    description = fields.Text(string='Description')


class RoomView(models.Model):
    _name = "room.view"
    _description = "Room View"

    name = fields.Char(string='View Name', required=True)
    code = fields.Char(string='View Code', required=True)
    description = fields.Text(string='Description')
    img = fields.Binary(string='Image', attachment=True, store=True)


class RoomFacility(models.Model):
    _name = "room.facility"
    _description = "Room Facility"

    name = fields.Char(string="Room Facility Name", required=True)
    code = fields.Char(string="Room Facility Code", required=True)
    description = fields.Text(string="Description")
    img = fields.Binary(string="Image", attachment=True, store=True)


class RoomFacilityType(models.Model):
    _name = "room.facility.type"
    _description = "Room Facility Type"

    name = fields.Char(string="Room Facility Type Name", required=True)
    code = fields.Char(string="Room Facility Type Code", required=True)


class Room(models.Model):
    _name = "room.room"
    _description = "Hotel Room"

    room_no = fields.Char(string="Room No", required=True)
    roomtype_code = fields.Char(string="Room Type Code", required=True)
    roomview_code = fields.Char(string="Room View Code", required=True)
    roomfacility_code = fields.Char(string="Room Facility Code", required=True)
    roomrate_code = fields.Char(string="Room Price", required=True)
    roombed_qty = fields.Integer(string="Number of Beds", required=True)
    room_size = fields.Char(string="Room Size")
    room_extension = fields.Char(string="Room Extension")
    room_des = fields.Text(string="Description")
    room_img = fields.Binary(string="Image", attachment=True, store=True)
