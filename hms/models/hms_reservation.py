from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules import get_module_resource
from odoo.tools import *
import base64
from datetime import datetime

class HMSReason(models.Model):
    _name = "hms.reason"
    _description = "Reason"

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    type_id = fields.Many2one('hms.reasontype', string="Reason Type", required=True)

class HMSReasonType(models.Model):
    _name = "hms.reasontype"
    _description = "Reason Type"

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", size=3, required=True)
    reason_ids = fields.One2many('hms.reason','type_id', string="Reason", required=True)

#Department
class Department(models.Model):
    _name = "hms.department"
    _description = "Department"

    name = fields.Char(string="Department Name", required=True)

#Special Request
class SpecialRequest(models.Model):
    _name = "hms.special.request"
    _description = "Special Request"

    reservationline_id = fields.Many2one('hms.reservation.line', string="Reservation Line")
    department_id = fields.Char("Department")
    date = fields.Date("Date")
    name = fields.Char("Name")

# Reservation Line
class ReservationLine(models.Model):
    _name = "hms.reservation.line"
    _description = "Reservation Line"

    reservation_id = fields.Many2one('hms.reservation',string="Reservation")
    confirm_no = fields.Char(string="Confirm No.", readonly=True,related='reservation_id.confirm_no')
    share_no = fields.Char(string="Share No.")
    state = fields.Char(string="State")

    market = fields.Char(string="Market")
    Source = fields.Char(string="Source")
    reservation_type = fields.Char("Reservation Type")
    reservation_status = fields.Char("Reservation Status")
    arrival_flight = fields.Char("Arrival Flight")
    arrival_flighttime = fields.Datetime("AR_Flight Time")
    dep_flight = fields.Char("Departure Flight")
    dep_flighttime = fields.Datetime("DEP_Flight Time")
    eta = fields.Datetime("ETA")
    etd = fields.Datetime("ETD")

    room_type = fields.Many2one('room.type', string="Room Type")
    arrival = fields.Date("Arrival")
    departure = fields.Date("Departure")
    rooms = fields.Integer("Rooms")
    pax = fields.Integer("Pax")
    child = fields.Integer("Child")
    ratecode_id = fields.Many2one('rate.code', string="Rate Code")
    room_rate = fields.Float("Room Rate")
    updown_amt = fields.Float("Updown Amount")
    updown_pc = fields.Float("Updown PC")
    reason_id = fields.Many2one('hms.reason',string="Reason")
    package_id = fields.Many2one('package.package', string="Package")
    allotment_id = fields.Char(string="Allotment")
    rate_nett = fields.Float(string="Rate Nett")
    fo_remark = fields.Char(string="F.O Remark")
    hk_remark = fields.Char(string="H.K Remark")
    cashier_remark = fields.Char(string="Cashier Remark")
    general_remark = fields.Char(string="General Remark")
    specialrequest_id = fields.One2many('hms.special.request','reservationline_id', string="Special Request")

    reservation_user_id = fields.Char("User")
    madeondate = fields.Date("Date")
    citime = fields.Datetime("Check-In Time")
    cotime = fields.Datetime("Check-Out Time")

    extrabed = fields.Char("Extra Bed")
    extabed_amount = fields.Integer("Number of Extra Bed")
    extrabed_bf = fields.Float("Extra Bed Breakfast")
    extrapax = fields.Float("Extra Pax")
    extrapax_amount = fields.Float("Number of Extra Pax")
    extrapax_bf =fields.Float("Extra Pax Breakfast")
    child_bfpax = fields.Float("Child BF-Pax")
    child_bf = fields.Float("Child Breakfast")
    extra_addon = fields.Float("Extra Addon")

    pickup = fields.Datetime("Pick Up Time")
    dropoff = fields.Datetime("Drop Off Time")
    arrival_trp = fields.Char("Arrive Transport")
    arrival_from = fields.Char("Arrive From")
    departure_trp = fields.Char("Departure Transport")
    departure_from = fields.Char("Departure From")
    visa_type = fields.Char("Visa Type")
    visa_issue = fields.Date("Visa Issue Date")
    visa_expire = fields.Date("Visa Expired Date")
    arrive_reason_id = fields.Char("Arrive Reason")

    @api.onchange('visa_issue','visa_expire')
    @api.constrains('visa_issue','visa_expire')
    def get_two_date_comp(self):
        startdate = self.visa_issue
        enddate = self.visa_expire
        if startdate and enddate and startdate > enddate:
            raise ValidationError("Expired Date cannot be set before Issue Date.")

# Reservation
class Reservation(models.Model):
    _name = 'hms.reservation'
    _description = "Reservation"

    state = fields.Selection([
            ('draft','Draft'),
            ('confirm','Confirm'),
            ('cancel','Cancel'),
            ('done','Done'),
    ])
    property_id = fields.Many2one('property.property', readonly=True)
    type = fields.Selection(string='Type',
        selection=[('individual', 'Individual'), ('group', 'Group')],
        compute='_compute_company_type', inverse='_write_company_type')
    is_company = fields.Boolean(string='Is a Contact', default=False)
    company_id = fields.Many2one('res.partner', string="Company")
    group_id = fields.Many2one('res.partner', string="Group")
    guest_id = fields.Many2one('res.partner', string="Guest")
    arrival = fields.Date(string="Arrival Date")
    departure = fields.Date(string="Departure Date")
    nights = fields.Integer(string="Number of Nights")
    no_ofrooms = fields.Integer(string="Number of Rooms")
    market = fields.Many2one('market.segment', string="Market")
    source = fields.Many2one('market.source', string="Market Source")
    sales_id = fields.Many2one('res.partner', string="Sale")
    contact_id = fields.Many2one('res.partner', string="Contact")
    reservation_type = fields.Many2one('rsvn.type', string="Reservation Type")
    reservation_status = fields.Many2one('rsvn.status', string="Reservation Status")
    arrival_flight = fields.Char(string="Arrival Flight")
    arrival_flighttime = fields.Datetime(string="AR-Flight Time")
    dep_flight = fields.Char(string="Departure Flight")
    dep_flighttime = fields.Datetime(string="DEP-Flight Time")
    eta = fields.Datetime(string="ETA")
    etd = fields.Datetime(string="ETD")
    reservation_line_ids = fields.One2many('hms.reservation.line','reservation_id',string="Reservation Line")
    confirm_no = fields.Char(string="Confirm Number", readonly=True)
    internal_notes = fields.Text(string="Internal Notes")

    @api.depends('is_company')
    def _compute_company_type(self):
        for partner in self:
            partner.type = 'group' if partner.is_company else 'individual'

    def _write_company_type(self):
        for partner in self:
            partner.is_company = partner.type == 'group'

    @api.onchange('type')
    def onchange_company_type(self):
        self.is_company = (self.type == 'group')

    @api.onchange('arrival','departure')
    @api.constrains('arrival','departure')
    def get_two_date_comp(self):
        startdate = self.arrival
        enddate = self.departure
        if startdate and enddate and startdate > enddate:
            raise ValidationError("Departure Date cannot be set before Arrival Date.")

    @api.model
    def create(self, values):
        
        property_id = values.get('property_id')
        property_id = self.env['property.property'].search(
            [('id', '=', property_id)])
        
        if property_id:
            if property_id.confirm_id_format:
                format_ids = self.env['pms.format.detail'].search(
                [('format_id', '=', property_id.confirm_id_format.id)],
                order='position_order asc')
            val = []
            for ft in format_ids:
                if ft.value_type == 'dynamic':
                    if property_id.code and ft.dynamic_value == 'property code':
                        val.append(property_id.code)
                if ft.value_type == 'fix':
                        val.append(ft.fix_value)
                if ft.value_type == 'digit':
                    sequent_ids = self.env['ir.sequence'].search([
                        ('code', '=', property_id.confirm_id_format.code)
                    ])
                    sequent_ids.write({'padding': ft.digit_value})
                if ft.value_type == 'datetime':
                    mon = yrs = ''
                    if ft.datetime_value == 'MM':
                        mon = datetime.today().month
                        val.append(mon)
                    if ft.datetime_value == 'MMM':
                        mon = datetime.today().strftime('%b')
                        val.append(mon)
                    if ft.datetime_value == 'YY':
                        yrs = datetime.today().strftime("%y")
                        val.append(yrs)
                    if ft.datetime_value == 'YYYY':
                        yrs = datetime.today().strftime("%Y")
                        val.append(yrs)
            space = []
            p_no_pre = ''
            if len(val) > 0:
                for l in range(len(val)):
                    p_no_pre += str(val[l])
            p_no = ''
            p_no += self.env['ir.sequence'].\
                    next_by_code(property_id.confirm_id_format.code) or 'New'
            pf_no = p_no_pre + p_no

            values.update({'confirm_no':pf_no})
        return super(Reservation,self).create(values)