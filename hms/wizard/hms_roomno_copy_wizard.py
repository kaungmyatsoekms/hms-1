import datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class RoomNoCopyWizard(models.TransientModel):
    _name = "hms.roomno_copy_wizard"
    _description = "Copy Wizard"

    def get_propertyroom_id(self):
        propertyroom_id = self.env['hms.property.room'].browse(
            self._context.get('active_id',[])
        )
        if propertyroom_id:
            return propertyroom_id

    is_roomtype_fix = fields.Boolean(related="roomtype_id.fix_type")
    propertyroom_id = fields.Many2one("hms.property.room",
                                     default=get_propertyroom_id,
                                     store=True)
    property_id = fields.Many2one("hms.property",related="propertyroom_id.property_id")
    room_no = fields.Char(string="Room No", required=True)
    roomtype_ids = fields.Many2many("hms.roomtype",
                                    related="propertyroom_id.roomtype_ids")
    roomtype_id = fields.Many2one('hms.roomtype',
                                  string="Room Type",
                                  related="propertyroom_id.roomtype_id")
    bedtype_ids = fields.Many2many('hms.bedtype', related="roomtype_id.bed_type")
    bedtype_id = fields.Many2one('hms.bedtype', string='Bed Type', domain="[('id', '=?', bedtype_ids)]")
    roomview_ids = fields.Many2many('hms.roomview', string="Room View Code",related="propertyroom_id.roomview_ids")
    building_ids = fields.Many2many("hms.building",
                                    related="propertyroom_id.building_ids")
    building_id = fields.Many2one('hms.building',
                                  string="Room Building",
                                  related="propertyroom_id.building_id")
    roomlocation_id = fields.Many2one('hms.roomlocation',
                                      string="Location",
                                      related="propertyroom_id.roomlocation_id")
    facility_ids = fields.One2many('hms.room.facility',
                                    string="Room Facility",
                                    related="propertyroom_id.facility_ids")
    room_bedqty = fields.Integer(string="Number of Beds",
                                 related="propertyroom_id.room_bedqty")
    room_size = fields.Char(string="Room Size",related="propertyroom_id.room_size")
    room_extension = fields.Char(string="Room Extension",related="propertyroom_id.room_extension")
    room_img = fields.Binary(string="Image",related="propertyroom_id.room_img")
    room_desc = fields.Text(string="Description",related="propertyroom_id.room_desc")
    room_connect = fields.Char(string="Connecting Room",related="propertyroom_id.room_connect")

    def action_roomno_copy_wiz(self):

        facility = []
        for rec in self.facility_ids:
            facility.append((0,0,{
                'facilitytype_id' : rec.facilitytype_id.id,
                'amenity_ids' : rec.amenity_ids,
                'facility_desc' : rec.facility_desc,
            }))

        vals = []
        vals.append((0,0,{
            'property_id' : self.property_id.id,
            'room_no' : self.room_no,
            'roomtype_id' : self.roomtype_id.id,
            'bedtype_id' :self.bedtype_id.id,
            'roomview_ids' : self.roomview_ids,
            'building_id' : self.building_id.id,
            'roomlocation_id' : self.roomlocation_id.id,
            'facility_ids' : facility,
            'room_bedqty' : self.room_bedqty,
            'room_size' : self.room_size,
            'room_extension' : self.room_extension,
            'room_img' : self.room_img,
            'room_desc' : self.room_desc,
            'room_connect' : self.room_connect,
        }))

        self.property_id.update({'propertyroom_ids': vals})

        return {
            'name':_('Copy'),
            'view_type':'form',
            'view_mode':'form',
            'view_id':self.env.ref('hms.property_room_view_form').id,
            'res_model':'hms.property.room',
            'context':"{'type':'out_propertyroom'}",
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

        # return {
        #     'name':_('Copy'),
        #     'view_type':'form',
        #     'view_mode':'form',
        #     'view_id':self.env.ref('hms.view_roomno_copy_wiz').id,
        #     'res_model':'hms.roomno_copy_wizard',
        #     'context':"{'type':'out_roomno_copy_wizard'}",
        #     'type': 'ir.actions.client',
        #     'tag': 'reload',
        #     'target':'new',
        # }

        
        