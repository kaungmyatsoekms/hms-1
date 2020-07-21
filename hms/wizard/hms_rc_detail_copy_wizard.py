import datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class RatecodeDetailCopyWizard(models.TransientModel):
    _name = "hms.rc_detail_copy_wizard"
    _description = "Copy Wizard"

    def get_ratecode_detail_id(self):
        ratecode_detail_id = self.env['ratecode.details'].browse(
            self._context.get('active_id',[])
        )
        if ratecode_detail_id:
            return ratecode_detail_id

    ratecode_detail_id = fields.Many2one('ratecode.details',default=get_ratecode_detail_id)
    ratehead_id = fields.Many2one('hms.ratecode.header',related="ratecode_detail_id.ratehead_id")
    property_id = fields.Many2one('property.property',
                                  readonly=True)
    season_code = fields.Char(string="Season",related="ratecode_detail_id.season_code")
    roomtype_ids = fields.Many2many("hms.roomtype",
                                    related="ratecode_detail_id.roomtype_ids")
    roomtype_id = fields.Many2many('hms.roomtype',
                                   related="ratecode_detail_id.roomtype_id")
    old_end_date = fields.Date(related="ratecode_detail_id.end_date")
    start_date = fields.Date(string="Start Date",
                             required=True)
    end_date = fields.Date(string="End Date", required=True)
    normal_price1 = fields.Float(string="1 Adult")
    normal_price2 = fields.Float(string="+2 Adult")
    normal_price3 = fields.Float(string="+3 Adult")
    normal_price4 = fields.Float(string="+4 Adult")
    normal_extra = fields.Float(string="Extra")
    weekend_price1 = fields.Float(string="Weekend 1 Adult")
    weekend_price2 = fields.Float(string="+2 Adult")
    weekend_price3 = fields.Float(string="+3 Adult")
    weekend_price4 = fields.Float(string="+4 Adult")
    weekend_extra = fields.Float(string="Extra")
    special_price1 = fields.Float(string="Special 1 Adult")
    special_price2 = fields.Float(string="+2 Adult")
    special_price3 = fields.Float(string="+3 Adult")
    special_price4 = fields.Float(string="+4 Adult")
    special_extra = fields.Float(string="Extra")
    extra_bed = fields.Float(string="Extra Bed")
    adult_bf = fields.Float(string="Adult Breakfast")
    child_bf = fields.Float(string="Child Breakfast")
    package_id = fields.Char(string="Package")
    discount_percent = fields.Float(string="Discount Percentage")
    discount_amount = fields.Float(string="Discount Amount")

    @api.onchange('old_end_date')
    def get_end_date(self):
        if self.old_end_date:
            self.start_date = self.old_end_date + timedelta(days=1)

    def action_rc_detail_copy_wiz(self):
        ratecode_detail_id = self.env['ratecode.details'].browse(
            self._context.get('active_id'))

        vals = []
        vals.append((0,0,{
            'ratehead_id': self.ratehead_id,
            'property_id': self.property_id.id,
            'season_code': self.season_code,
            'start_date' : self.start_date,
            'end_date' : self.end_date,
            'roomtype_ids' : self.roomtype_ids,
            'roomtype_id' : self.roomtype_id,
            'normal_price1' : self.normal_price1,
            'normal_price2' : self.normal_price2,
            'normal_price3' : self.normal_price3,
            'normal_price4' : self.normal_price4,
            'normal_extra' : self.normal_extra,
            'weekend_price1' : self.weekend_price1,
            'weekend_price2' : self.weekend_price2,
            'weekend_price3' : self.weekend_price3,
            'weekend_price4' : self.weekend_price4,
            'weekend_extra' : self.weekend_extra,
            'special_price1' : self.special_price1,
            'special_price2' : self.special_price2,
            'special_price3' : self.special_price3,
            'special_price4' : self.special_price4,
            'special_extra' : self.special_extra,
            'extra_bed' : self.extra_bed,
            'adult_bf' : self.adult_bf,
            'child_bf' : self.child_bf,
            'package_id' : self.package_id,
            'discount_percent' : self.discount_percent,
            'discount_amount' : self.discount_amount,
        }))

        ratecode_detail_id.ratehead_id.update({'ratecode_details': vals})
