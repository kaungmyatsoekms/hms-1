from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HMSTransactionChargeLine(models.Model):
    _name = 'hms.room.transaction.charge.line'
    _description = "Room Charges Type"
    _inherit = ['mail.thread']


    package_charge_id = fields.Many2one("hms.package.charge.line",
                                           "Package Name",
                                           required=True,
                                           track_visibility=True)
    charge_type_id = fields.Many2one(
        "hms.charge_types",
        'Main Charge Type',
        related="package_charge_id.charge_type_id",
        required=True,
        track_visibility=True)
    calculation_method_id = fields.Many2one(
        'hms.calculation.method',
        "Calculation Method",
        related="package_charge_id.calculation_method_id",
        readonly=True)
    rate = fields.Float("Rate", store=True)
    total_amount = fields.Float("Total") #, compute="compute_total_amount"
    active = fields.Boolean(default=True)
    reservation_line_id = fields.Many2one("hms.reservation.line", "Charges")
    reservation_id = fields.Many2one("hms.reservation",
                               "Reservation",
                               compute="get_reservation_id")
    room_no = fields.Many2one('property.room', "Room No", compute="get_reservation_id")
    trans_date = fields.Date("Date")

    @api.depends('reservation_line_id')
    def get_reservation_id(self):
        for rec in self:
            if rec.reservation_line_id:
                rec.reservation_id = rec.reservation_line_id.reservation_id.id
                rec.room_no = rec.reservation_line_id.room_no.id

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