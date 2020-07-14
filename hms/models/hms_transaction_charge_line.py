import base64
import logging

from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules import get_module_resource
from odoo.tools import *
from datetime import datetime, date, timedelta

POSTING_RYTHMS = [
    ('1', 'Post Every Night'),
    ('2', 'Post on Arrival Night'),
    ('3', 'Post on Last Night'),
    ('4', 'Post Every Night Except Arrival Night'),
    ('5', 'Post Every Night Except Last Night'),
    ('6', 'Post on Certain Nights of the Week'),
    ('7', 'Do Not Post on First and Last Night'),
]

CALCUATION_METHODS = [
    ('FIX', 'Fix Rate'),
    ('PP', 'Per Person'),
    ('PA', 'Per Adult'),
    ('PC', 'Per Child'),
    ('PR', 'Per Room'),
]

RATE_ATTRIBUTE = [
    ('INR', 'Include in Rate'),
    ('ARS', 'Add Rate Separate Line'),
    ('ARC', 'Add Rate Combined Line'),
    ('SS', 'Sell Separate'),
]


class HMSTransactionChargeLine(models.Model):
    _name = 'hms.room.transaction.charge.line'
    _description = "Room Charges Type"
    _inherit = ['mail.thread']

    reservation_line_id = fields.Many2one("hms.reservation.line", "Charges")
    property_id = fields.Many2one('property.property',
                                  string="Property",
                                  required=True)
    active = fields.Boolean(string="Active",
                            default=True,
                            track_visibility=True)
    sequence = fields.Integer(default=1)
    package_code = fields.Char(string="Package Code", size=4, required=True)
    package_name = fields.Char(string="Package Name", required=True)
    start_date = fields.Date(string="Start Date",
                             required=True,
                             help="Start of Package")
    end_date = fields.Date(string="End Date",
                           required=True,
                           help="End of Package")
    forecast_next_day = fields.Boolean(string="Forecast Next Day",
                                       track_visibility=True)
    post_next_day = fields.Boolean(string="Post Next Day",
                                   track_visibility=True)
    catering = fields.Boolean(string="Catering", track_visibility=True)
    transaction_id = fields.Many2one('transaction.transaction',
                                     string='Transaction')
    package_profit = fields.Many2one('transaction.transaction',
                                     string='Profit')
    package_loss = fields.Many2one('transaction.transaction', string='Loss')
    product_item = fields.Char('Product Item')
    include_service = fields.Boolean('Include Service', track_visibility=True)
    include_tax = fields.Boolean('Include Tax', track_visibility=True)
    allowance = fields.Boolean(string="Allowance", track_visibility=True)
    valid_eod = fields.Boolean(string="Valid C/O EOD", track_visibility=True)
    currency_id = fields.Char(string="Currency")
    posting_rythms = fields.Selection(POSTING_RYTHMS, string='Posting Rythms')
    Calculation_method = fields.Selection(CALCUATION_METHODS, string='Rating')
    Fix_price = fields.Float('Price')
    rate_attribute = fields.Selection(RATE_ATTRIBUTE,
                                      string="Attribute",
                                      index=True)
    # reservation_line_id = fields.Many2one("hms.reservation.line", "Charges")
    # reservation_id = fields.Many2one("hms.reservation",
    #                            "Reservation",
    #                            compute="get_reservation_id")
    # property_id = fields.Many2one('property.property', string="Property")
    # package_id = fields.Many2one('package.package',string='Package', related='reservation_line_id.package_id')
    # package_charge_id = fields.Many2one("hms.package.charge.line",
    #                                        "Package Name",
    #                                        required=True,
    #                                        track_visibility=True)
    # charge_type_id = fields.Many2one(
    #     "hms.charge_types",
    #     'Main Charge Type',
    #     related="package_charge_id.charge_type_id",
    #     required=True,
    #     track_visibility=True)
    # calculation_method_id = fields.Many2one(
    #     'hms.calculation.method',
    #     "Calculation Method",
    #     related="package_charge_id.calculation_method_id",
    #     readonly=True)
    # rate = fields.Float("Rate", store=True)
    # total_amount = fields.Float("Total") #, compute="compute_total_amount"
    # active = fields.Boolean(default=True)
    # room_no = fields.Many2one('property.room', "Room No", related='reservation_line_id.room_no')
    # transfer_room = fields.Many2one('property.room','Room No', related='reservation_line_id.room_no')
    # trans_date = fields.Date("Date")

    # @api.depends('reservation_line_id')
    # def get_reservation_id(self):
    #     for rec in self:
    #         if rec.reservation_line_id:
    #             rec.reservation_id = rec.reservation_line_id.reservation_id.id
    #             rec.room_no = rec.reservation_line_id.room_no.id

    # @api.depends('package_charge_id', 'calculation_method_id', 'rate')
    # def compute_total_amount(self):
    # if self.calculation_method_id.name == 'Fix':
    #     self.total_amount = self.rate
    # if self.calculation_method_id.name == 'Percentage':
    #     if self.lease_line_id:
    #         self.total_amount = 0
    # if self.calculation_method_id.name == 'Area':
    #     if self.lease_line_id:
    #         area = self.lease_line_id.unit_no.area
    #         self.total_amount = (area * self.rate)
    # if self.calculation_method_id.name == 'MeterUnit':
    #     if self.lease_line_id and self.applicable_charge_id:
    #         if self.applicable_charge_id.use_formula == True:
    #             self.rate = 0
    #             self.total_amount = 0
    #         elif self.applicable_charge_id.use_formula != True and self.rate == 0:
    #             self.rate = self.applicable_charge_id.rate
    #             self.total_amount = self.rate
    #         else:
    #             self.rate = self.rate
    #             self.total_amount = self.rate
