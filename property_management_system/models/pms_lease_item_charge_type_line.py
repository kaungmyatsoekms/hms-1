from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PMSLeaseUnitChargeTypeLine(models.Model):
    _name = 'pms.lease.unit.charge.type.line'
    _description = "Lease Agreement Unit Charge Type"
    _inherit = ['mail.thread']

    @api.model
    def _get_start_date(self):
        start_date = self.env.context.get('start_date')
        return start_date

    @api.model
    def _get_end_date(self):
        end_date = self.env.context.get('end_date')
        return end_date

    applicable_charge_id = fields.Many2one("pms.applicable.charge.type",
                                           "Charge Name",
                                           required=True,
                                           track_visibility=True)
    charge_type_id = fields.Many2one(
        "pms.charge_types",
        'Main Charge Type',
        related="applicable_charge_id.charge_type_id",
        required=True,
        track_visibility=True)
    calculation_method_id = fields.Many2one(
        'pms.calculation.method',
        "Calculation Method",
        related="applicable_charge_id.calculation_method_id",
        readonly=True)
    rate = fields.Float("Rate", store=True)
    total_amount = fields.Float("Total", compute="compute_total_amount")
    active = fields.Boolean(default=True)
    lease_line_id = fields.Many2one("pms.lease_agreement.line", "Lease Items")
    lease_id = fields.Many2one("pms.lease_agreement",
                               "Lease",
                               compute="get_lease_id")
    unit_no = fields.Many2one("pms.space.unit", "Unit", compute="get_lease_id")
    start_date = fields.Date("Start Date", default=_get_start_date)
    end_date = fields.Date("End Date", default=_get_end_date)

    @api.one
    @api.depends('lease_line_id')
    def get_lease_id(self):
        if self.lease_line_id:
            self.lease_id = self.lease_line_id.lease_agreement_id.id
            self.unit_no = self.lease_line_id.unit_no.id

    @api.one
    @api.depends('applicable_charge_id', 'calculation_method_id', 'rate')
    def compute_total_amount(self):
        if self.calculation_method_id.name == 'Fix':
            self.total_amount = self.rate
        if self.calculation_method_id.name == 'Percentage':
            if self.lease_line_id:
                self.total_amount = 0
        if self.calculation_method_id.name == 'Area':
            if self.lease_line_id:
                area = self.lease_line_id.unit_no.area
                self.total_amount = (area * self.rate)
        if self.calculation_method_id.name == 'MeterUnit':
            if self.lease_line_id and self.applicable_charge_id:
                if self.applicable_charge_id.use_formula == True:
                    self.rate = 0
                    self.total_amount = 0
                elif self.applicable_charge_id.use_formula != True and self.rate == 0:
                    self.rate = self.applicable_charge_id.rate
                    self.total_amount = self.rate
                else:
                    self.rate = self.rate
                    self.total_amount = self.rate
