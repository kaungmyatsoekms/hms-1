import base64
import logging
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules import get_module_resource
from odoo.tools import *
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as dt
_logger = logging.getLogger(__name__)


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

# Reservation
class Reservation(models.Model):
    _name = 'hms.reservation'
    _description = "Reservation"
    _order = 'confirm_no desc'
    _inherit = ['mail.thread']

    is_reservation = fields.Boolean(string="Is Reservation",
                                    compute='_compute_is_reservation')
    button_hide = fields.Boolean(string="Button Hide", default=False)
    state = fields.Selection([
            ('booking','Booking'),
            ('reservation','Reservation'),
            ('confirm','Confirm'),
            ('cancel','Cancel'),
            ('checkin','Checkin'),
    ],
    'State', readonly=True,
                             default=lambda *a: 'booking')
    property_id = fields.Many2one('property.property',string="Property", default=lambda self: self.env.user.property_id.id)
    date_order = fields.Datetime('Date Ordered', readonly=True, required=True,
                                 index=True,
                                 default=(lambda *a: time.strftime(dt)))
    type = fields.Selection(string='Type',
        selection=[('individual', 'Individual'), ('group', 'Group')],
        compute='_compute_type', inverse='_write_type', track_visibility=True)
    is_company = fields.Boolean(string='Is a Company', default=False)
    is_group=fields.Boolean(string="Is a Group")
    is_individual = fields.Boolean(string="Is a Individual", default=True)
    company_id = fields.Many2one('res.partner', string="Company",domain="['&',('profile_no','!=',''),('is_company','=',True)]")
    group_id = fields.Many2one('res.partner', string="Group", domain="[('is_group','=',True)]")
    guest_id = fields.Many2one('res.partner', string="Guest", domain="[('is_guest','=',True)]")
    arrival = fields.Date(string="Arrival Date", default=datetime.today(), required=True)
    departure =  fields.Date(
        string="Departure Date",
        default=lambda *a:
        (datetime.now() + timedelta(days=(1))).strftime('%Y-%m-%d'), required=True)
    nights = fields.Integer(string="Nights")
    no_ofrooms = fields.Integer(string="Number of Rooms", default=1,required=True)
    market_ids = fields.Many2many('market.segment', related="property_id.market_ids")
    market = fields.Many2one('market.segment', string="Market", domain="[('id', '=?', market_ids)]",required=True)
    source = fields.Many2one('market.source', string="Market Source", required=True)
    sales_id = fields.Many2one('res.partner', string="Sales")
    contact_id = fields.Many2one('res.partner', string="Contact")
    reservation_type = fields.Many2one('rsvn.type', string="Reservation Type", required=True, default=2)
    reservation_status = fields.Many2one('rsvn.status', string="Reservation Status")
    arrival_flight = fields.Char(string="Arrival Flight",size=10)
    arrival_flighttime = fields.Float(string="AR-Flight Time")
    dep_flight = fields.Char(string="Departure Flight")
    dep_flighttime = fields.Float(string="DEP-Flight Time")
    eta = fields.Float(string="ETA")
    etd = fields.Float(string="ETD")
    reservation_line_ids = fields.One2many('hms.reservation.line','reservation_id',string="Reservation Line")
    confirm_no = fields.Char(string="Confirm Number", readonly=True)
    internal_notes = fields.Text(string="Internal Notes")

    def name_get(self):
        result = []
        for record in self:
            if record.guest_id:
                result.append((record.id, "{}".format(record.guest_id.name)))
            else:
                result.append((record.id, "{}".format(record.group_id.name)))
        return result

    def _compute_is_reservation(self):
        self.is_reservation = True

    def set_to_booking_reservation(self):
        for record in self:
            record.state = 'booking'
        return True

    def accept_booking_status(self):
        self.write({'state': 'reservation'})
        for rec in self:
            val = self.env['rsvn.type'].search([('rsvn_name', '=',
                                                    'Unconfirmed')])
            self.reservation_type = val

    def confirm_status(self):
        self.write({'state': 'confirm'})
        for rec in self:
            val = self.env['rsvn.type'].search([('rsvn_name', '=', 'Confirmed')
                                                ])
            self.reservation_type = val
    
    def cancel_status(self):
        self.write({'state': 'cancel'})
        for rec in self:
            val = self.env['rsvn.type'].search([('rsvn_name', '=',
                                                 'Unconfirmed')])
            self.reservation_type = val

    def checkin_status(self):
        self.write({'state': 'checkin'})
        for rec in self:
            val = self.env['rsvn.type'].search([('rsvn_name', '=', 'Confirmed')
                                                ])
            self.reservation_type = val

    # Change Room Nights
    @api.onchange('reservation_line_ids')
    def onchange_num_of_rooms(self):
        temp = 0
        for record in self:
            if record.reservation_line_ids:
                for r in record.reservation_line_ids:
                    temp = temp + r.rooms
                if record.no_ofrooms < temp:
                    record.no_ofrooms = temp
                    # record.reservation_line_ids.rooms = 1

    @api.onchange('reservation_type')
    def onchange_state(self):
        rsvntype = self.reservation_type
        if rsvntype and rsvntype == 'Confirmed':
            self.state = 'confirm'
            self.button_hide = True

    @api.depends('is_individual','is_group')
    def _compute_type(self):
        for partner in self:
            if partner.is_individual or self._context.get(
                    'default_type') == 'individual':
                partner.type = 'individual'
                partner.is_individaul = True
            elif partner.is_group or self._context.get(
                    'default_type') == 'group':
                partner.type = 'group'
                partner.is_group = True

    def _write_type(self):
        for partner in self:
            partner.is_group = partner.type == 'group'
            partner.is_individaul = partner.type == 'individual'

    # @api.onchange('type')
    # def onchange_type(self):
    #     if self.type == 'group':
    #         self.is_group = True
    #         self.is_individaul = False
    #     elif self.type =='individual':
    #         self.is_group = False
    #         self.is_individaul = True

    # @api.onchange('type')
    # def onchange_company_type(self):
    #     self.is_company = (self.type == 'group')

    # @api.onchange('arrival','departure')
    # @api.constrains('arrival','departure')
    # def get_two_date_comp(self):
    #     """
    #     When date_order is less then check-in date or
    #     Checkout date should be greater than the check-in date.
    #     """
    #     startdate = self.arrival
    #     enddate = self.departure
    #     if startdate and enddate:
    #         # if startdate < self.date_order:
    #         if datetime.strptime(str(startdate), DEFAULT_SERVER_DATE_FORMAT).date() < datetime.now().date():
    #             self.arrival = datetime.today()
    #             raise ValidationError(_('Check-in date should be greater than or equal \
    #                                      the current date.'))
    #         if startdate > enddate:
    #             raise ValidationError(_('Check-out date should be greater \
    #                                      than Check-in date.'))
    
    # Change Departure Date
    @api.onchange('arrival')
    def onchange_departure_date(self):
        arrivaldate = self.arrival
        no_of_night = self.nights
        if arrivaldate and no_of_night:
            self.departure = arrivaldate+ timedelta(days=no_of_night)
            # if no_of_night == 1:
            #     self.departure = arrivaldate + timedelta(days=1)
            # elif no_of_night > 1:
            #     self.departure = arrivaldate + timedelta(days=no_of_night)
    
    @api.onchange('nights')
    def onchange_dep_date(self):
        arrivaldate = self.arrival
        no_of_night = self.nights
        if arrivaldate and no_of_night:
            self.departure = arrivaldate + timedelta(days=no_of_night)

    # Change Room Nights
    @api.onchange('departure')
    def onchange_nights(self):
        d1 = datetime.strptime(str(self.arrival), '%Y-%m-%d')
        d2 = datetime.strptime(str(self.departure), '%Y-%m-%d')
        d3 = d2 - d1
        days = str(d3.days)
        self.nights = int(days)

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
                            ('code', '=',property_id.code+property_id.confirm_id_format.code)
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
                # space = []
                p_no_pre = ''
                if len(val) > 0:
                    for l in range(len(val)):
                        p_no_pre += str(val[l])
                p_no = ''
                p_no += self.sudo().env['ir.sequence'].sudo().\
                        next_by_code(property_id.code+property_id.confirm_id_format.code) or 'New'
                pf_no = p_no_pre + p_no

            # if property_id.cancel_id_format:
            #     format_ids = self.env['pms.format.detail'].search(
            #     [('format_id', '=', property_id.cancel_id_format.id)],
            #     order='position_order asc')
            #     val = []
            #     for ft in format_ids:
            #         if ft.value_type == 'dynamic':
            #             if property_id.code and ft.dynamic_value == 'property code':
            #                 val.append(property_id.code)
            #         if ft.value_type == 'fix':
            #                 val.append(ft.fix_value)
            #         if ft.value_type == 'digit':
            #             sequent_ids = self.env['ir.sequence'].search([
            #                 ('code', '=',property_id.code+property_id.cancel_id_format.code)
            #             ])
            #             sequent_ids.write({'padding': ft.digit_value})
            #         if ft.value_type == 'datetime':
            #             mon = yrs = ''
            #             if ft.datetime_value == 'MM':
            #                 mon = datetime.today().month
            #                 val.append(mon)
            #             if ft.datetime_value == 'MMM':
            #                 mon = datetime.today().strftime('%b')
            #                 val.append(mon)
            #             if ft.datetime_value == 'YY':
            #                 yrs = datetime.today().strftime("%y")
            #                 val.append(yrs)
            #             if ft.datetime_value == 'YYYY':
            #                 yrs = datetime.today().strftime("%Y")
            #                 val.append(yrs)
            #     # space = []
            #     p_no_pre = ''
            #     if len(val) > 0:
            #         for l in range(len(val)):
            #             p_no_pre += str(val[l])
            #     p_no = ''
            #     p_no += self.sudo().env['ir.sequence'].sudo().\
            #             next_by_code(property_id.code+property_id.cancel_id_format.code) or 'New'
            #     pf_no = p_no_pre + p_no

            values.update({'confirm_no':pf_no})
        return super(Reservation,self).create(values)

# Reservation Line
class ReservationLine(models.Model):
    _name = "hms.reservation.line"
    _description = "Reservation Line"

    def get_arrival(self):
        if self._context.get('arrival') != False:
            return self._context.get('arrival')

    def get_departure(self):
        if self._context.get('departure') != False:
            return self._context.get('departure')
    
    def get_rooms(self):
        if self._context.get('rooms') != False:
            return self._context.get('rooms')
            
    is_rsvn_details = fields.Boolean(string="Is Reservation Details",
                                     compute='_compute_is_rsvn_details')
    reservation_id = fields.Many2one('hms.reservation',string="Reservation")
    property_id = fields.Many2one('property.property',string="Property", readonly=True,related='reservation_id.property_id')
    confirm_no = fields.Char(string="Confirm No.", readonly=True,related='reservation_id.confirm_no')
    state = fields.Selection([
            ('booking','Booking'),
            ('reservation','Reservation'),
            ('confirm','Confirm'),
            ('cancel','Cancel'),
            ('checkin','Checkin'),
    ])
    market_ids = fields.Many2many('market.segment', related="property_id.market_ids")
    market = fields.Many2one('market.segment',string="Market", readonly=False, related='reservation_id.market')
    source = fields.Many2one('market.source',string="Source", readonly=False, related='reservation_id.source')
    reservation_type = fields.Many2one('rsvn.type',"Reservation Type", readonly=True,related='reservation_id.reservation_type')
    reservation_status = fields.Many2one('rsvn.status',"Reservation Status", readonly=False,related='reservation_id.reservation_status')
    arrival_flight = fields.Char("Arrival Flight",readonly=False, related='reservation_id.arrival_flight')
    arrival_flighttime = fields.Float("AR_Flight Time", readonly=False, related='reservation_id.arrival_flighttime')
    dep_flight = fields.Char("Departure Flight", readonly=False, related='reservation_id.dep_flight')
    dep_flighttime = fields.Float("DEP_Flight Time", readonly=False, related='reservation_id.dep_flighttime')
    eta = fields.Float("ETA", readonly=False, related='reservation_id.eta')
    etd = fields.Float("ETD", readonly=False, related='reservation_id.etd')

    room_no = fields.Many2one('property.room',string="Room No")
    roomtype_ids = fields.Many2many('room.type', related="property_id.roomtype_ids")
    room_type = fields.Many2one('room.type', string="Room Type", domain="[('id', '=?', roomtype_ids)]")
    arrival = fields.Date("Arrival",
                    default=get_arrival,
                    readonly=False,
                    required=True,
                    store=True,
                    track_visibility=True)
    departure = fields.Date("Departure",
                    default=get_departure,
                    readonly=False,
                    required=True,
                    store=True,
                    track_visibility=True)
    rooms = fields.Integer("Rooms",default=get_rooms)
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

    def _compute_is_rsvn_details(self):
        self.is_rsvn_details = True

    @api.onchange('visa_issue','visa_expire')
    @api.constrains('visa_issue','visa_expire')
    def get_two_date_comp(self):
        startdate = self.visa_issue
        enddate = self.visa_expire
        if startdate and enddate and startdate > enddate:
            raise ValidationError("Expired Date cannot be set before Issue Date.")

    @api.onchange('property_id')
    def property_onchange(self):
        res = {}
        res['domain']={'room_no':[('id', 'in', self.property_id.propertyroom_ids.ids)]}
        return res

    def confirm_status(self):
        self.write({'state': 'confirm'})

    def cancel_status(self):
        self.write({'state': 'cancel'})

    def checkin_status(self):
        self.write({'state': 'checkin'})


    @api.onchange('id', 'rooms')
    def onchange_rsvn_rooms(self):
        for record in self:
            last_id = self.env['hms.reservation.line'].search([],
                                                              order='id desc',
                                                              limit=1)
            rsvn_id = self.env['hms.reservation'].search([],
                                                         order='id desc',
                                                         limit=1)
            if last_id and record.reservation_id == rsvn_id:
                prev_rooms = last_id.rooms
                record.rooms = record.reservation_id.no_ofrooms - prev_rooms

    def action_split(self):
        _logger.info('self = %s',self)
        rooms=self.rooms-1
        if rooms:
            super(ReservationLine,self).update({'rooms':1})
            for rec in range(rooms):
                self.env['hms.reservation.line'].create({
                    'rooms' : 1,

                })

    
