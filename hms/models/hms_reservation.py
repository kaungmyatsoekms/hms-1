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
    is_arrival_today = fields.Boolean(string="Is Arrival Today",
                                    compute='_compute_is_arrival_today')
    is_full_cancel = fields.Boolean(string='Is Fully Canceled', default=False)
    state = fields.Selection([
            ('booking','Booking'),
            ('reservation','Reservation'),
            ('confirm','Confirm'),
            ('cancel','Cancel'),
            ('checkin','Checkin'),
            ], 'Status', readonly=True, default=lambda *a: 'booking')
    property_id = fields.Many2one('property.property',string="Property", default=lambda self: self.env.user.property_id.id)
    user_id = fields.Many2one('res.users', string='Salesperson', default=lambda self: self.env.user.id)
    date_order = fields.Datetime('Date Ordered', readonly=True, required=True,
                                 index=True,
                                 default=(lambda *a: time.strftime(dt)))
    type = fields.Selection(string='Type',
        selection=[('individual', 'Individual'), ('group', 'Group')],
        compute='_compute_type', inverse='_write_type', track_visibility=True)
    is_company = fields.Boolean(string='Is a Company', default=False)
    is_group=fields.Boolean(string="Is a Group", default=False)
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
    sales_id = fields.Many2one('res.partner', string="Sales", domain="[('company_type', '=','person')]")
    contact_id = fields.Many2one('res.partner', domain="[('company_type', '=','person')]", string="Contact")
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

    #Fields for statinfo
    rsvn_room_count = fields.Integer(string="Reservation", compute='_compute_rsvn_rooms')
    confirm_room_count = fields.Integer(string="Confirm", compute='_compute_confirm_rooms')
    cancel_room_count = fields.Integer(string="Canceled", compute='_compute_cancel_rooms')
    checkin_room_count = fields.Integer(string="Check-in", compute='_compute_checkin_rooms')

    def _compute_rsvn_rooms(self):
        tmp = 0
        for record in self.reservation_line_ids:
            if record.state == 'reservation':
                tmp = tmp + record.rooms
        self.rsvn_room_count = tmp

    def _compute_confirm_rooms(self):
        tmp = 0
        for record in self.reservation_line_ids:
            if record.state == 'confirm':
                tmp = tmp + record.rooms
        self.confirm_room_count = tmp

    def _compute_cancel_rooms(self):
        tmp = 0
        for record in self.reservation_line_ids:
            if record.state == 'cancel':
                tmp = tmp + record.rooms
        self.cancel_room_count = tmp

    def _compute_checkin_rooms(self):
        tmp = 0
        for record in self.reservation_line_ids:
            if record.state == 'checkin':
                tmp = tmp + record.rooms
        self.checkin_room_count = tmp

    #Arrival Today
    def _compute_is_arrival_today(self):
        arrival_date = self.arrival
        if datetime.strptime(
            str(arrival_date),
            DEFAULT_SERVER_DATE_FORMAT).date() == datetime.now().date():
            self.is_arrival_today = True
        else:
            self.is_arrival_today = False

    def name_get(self):
        result = []
        for record in self:
            if record.guest_id:
                result.append((record.id, "{}".format(record.guest_id.name)))
            else:
                result.append((record.id, "{}".format(record.group_id.name)))
        return result

    # Radio Button for Individual & Group Function
    @api.depends('is_group')
    def _compute_type(self):
        for partner in self:
            if partner.is_group or self._context.get('default_type') == 'group':
                partner.type = 'group'
                partner.is_group = True
            else:
                partner.type='individual'

    def _write_type(self):
        for partner in self:
            partner.is_group = partner.type == 'group'

    @api.onchange('type')
    def onchange_type(self):
        self.is_group = (self.type == 'group')

    #Button Function
    # Button Show for after save button
    def _compute_is_reservation(self):
        self.is_reservation = True

    def set_to_booking_reservation(self):
        for record in self:
            record.state = 'booking'
        return True

    def accept_booking_status(self):
        self.write({'state': 'reservation'})
        for rec in self.reservation_line_ids:
            if rec.is_rsvn_details is True and rec.state == 'booking':
                rec.write({'state': 'reservation'})
        for rec in self:
            val = self.env['rsvn.type'].search([('rsvn_name', '=',
                                                 'Unconfirmed')])
        for rec in self:
            val = self.env['rsvn.type'].search([('rsvn_name', '=',
                                                    'Unconfirmed')])
            self.reservation_type = val

    def confirm_status(self):
        self.write({'state': 'confirm'})
        for rec in self.reservation_line_ids:
            if rec.is_rsvn_details is True:
                rec.write({'state': 'confirm'})
        for rec in self:
            val = self.env['rsvn.type'].search([('rsvn_name', '=', 'Confirmed')
                                                ])
            self.reservation_type = val

    # Cancel Status & Cancel Table
    def cancel_status(self):
        self.write({'state': 'cancel'})

    def copy_cancel_record(self):
        if self.state == 'cancel':
            res = {}
            self.env['hms.cancel.rsvn'].create({
                'is_full_cancel': True,
                'state': self.state,
                'property_id': self.property_id.id,
                'user_id': self.user_id.id,
                'date_order':self.date_order,
                'is_company': self.is_company,
                'is_group': self.is_group,
                'company_id': self.company_id.id,
                'group_id': self.group_id.id,
                'guest_id': self.guest_id.id,
                'arrival': self.arrival,
                'departure': self.departure,
                'nights': self.nights,
                'no_ofrooms': self.no_ofrooms,
                'market': self.market.id,
                'source': self.source.id,
                'sales_id': self.sales_id.id,
                'contact_id': self.contact_id.id,
                'reservation_type': self.reservation_type.id,
                'reservation_status': self.reservation_status.id,
                'arrival_flight': self.arrival_flight,
                'arrival_flighttime': self.arrival_flighttime,
                'dep_flight': self.dep_flight,
                'dep_flighttime': self.dep_flighttime,
                'eta': self.eta,
                'etd': self.etd,
                'reason_id': self.reason_id.id,
                'reservation_line_ids': self.reservation_line_ids,
                'confirm_no': self.confirm_no,
                'internal_notes': self.internal_notes,
            })
            return res
    
    # Check In Status
    
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

    def unconfirm_status(self):
        self.write({'state': 'reservation'})
        for rec in self:
            val = self.env['rsvn.type'].search([('rsvn_name', '=',
            'Unconfirmed')])
            self.reservation_type = val

    def re_reservation(self):
        if self.reservation_type.rsvn_name == 'Confirmed':
            self.write({'state': 'confirm'})
        else:
            self.write({'state': 'reservation'})

    # Confirm State in All Reservation Details confirm
    @api.onchange('no_ofrooms', 'confirm_room_count')
    def onchange_confirm_state(self):
        if self.confirm_room_count == self.no_ofrooms:
            self.write({'state': 'confirm'})
            for rec in self:
                val = self.env['rsvn.type'].search([('rsvn_name', '=',
                                                     'Confirmed')])
                self.reservation_type = val

    #Change Room Nights
    # @api.onchange('reservation_line_ids')
    # def onchange_num_of_rooms(self):
    #     temp = 0
    #     for record in self:
    #         if record.reservation_line_ids:
    #             for r in record.reservation_line_ids:
    #                 temp = temp + r.rooms
    #             if record.no_ofrooms < temp:
    #                 record.no_ofrooms = temp
                    # record.reservation_line_ids.rooms = 1

    @api.onchange('reservation_type')
    def onchange_state(self):
        rsvntype = self.reservation_type
        if rsvntype and rsvntype == 'Confirmed':
            self.state = 'confirm'
    
    @api.constrains('arrival')
    def check_arrival_date(self):
        arrival_date = self.arrival
        if arrival_date:
            if datetime.strptime(
                    str(arrival_date),
                    DEFAULT_SERVER_DATE_FORMAT).date() < datetime.now().date():
                raise ValidationError(
                    _('Check-in date should be greater than or equal to the current date.'
                      ))
                self.arrival = datetime.now().date()

    @api.constrains('departure')
    def compare_two_date(self):
        arrival_date = self.arrival
        departure_date = self.departure
        if arrival_date and departure_date:
            if arrival_date > departure_date:
                raise ValidationError(
                    _('Check-out date should be greater than Check-in date.'))

    # Change Departure Date
    @api.onchange('arrival')
    def onchange_departure_date(self):
        arrivaldate = self.arrival
        no_of_night = self.nights
        if arrivaldate and no_of_night:
            self.departure = arrivaldate+ timedelta(days=no_of_night)

    # Change Departure Date 
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
    
    # All Split Rsvn Action
    def action_split(self): 
        # arrival = self.arrival
        # departure = self.departure
        for resv_line in self.reservation_line_ids:
            room = resv_line.rooms
            if room and room >= 2: 
                resv_line.update({'rooms':1})
                vals = []
                for record in range(room-1):
                    vals.append((0,0,{'rooms':1,
                    'arrival':resv_line.arrival, 'departure':resv_line.departure,
                    'arrival_flight':resv_line.arrival_flight, 'dep_flight':resv_line.dep_flight,
                    'arrival_flighttime':resv_line.arrival_flighttime, 'dep_flighttime':resv_line.dep_flighttime,
                    'market':resv_line.market.id, 'source':resv_line.source.id,
                    'reservation_type':resv_line.reservation_type.id, 'reservation_status':resv_line.reservation_status.id,
                    'eta':resv_line.eta, 'etd':resv_line.etd, 'room_type':resv_line.room_type.id,
                    'pax':resv_line.pax, 'child':resv_line.child, 'ratecode_id':resv_line.ratecode_id.id,
                    'room_rate':resv_line.room_rate, 'updown_amt':resv_line.updown_amt,
                    'updown_pc':resv_line.updown_pc, 'reason_id':resv_line.reason_id.id,
                    'package_id':resv_line.package_id.id, 'rate_nett':resv_line.rate_nett,
                    'fo_remark':resv_line.fo_remark, 'hk_remark':resv_line.hk_remark,
                    'cashier_remark':resv_line.cashier_remark, 'general_remark':resv_line.general_remark,
                    'madeondate':resv_line.madeondate, 'citime':resv_line.citime, 'cotime':resv_line.cotime,
                    'extrabed':resv_line.extrabed,'extrabed_amount':resv_line.extrabed_amount,'extrabed_bf':resv_line.extrabed_bf,
                    'extrapax':resv_line.extrapax, 'extrapax_amount':resv_line.extrapax_amount,'extrapax_bf':resv_line.extrapax_bf,
                    'child_bfpax':resv_line.child_bfpax, 'child_bf':resv_line.child_bf,'extra_addon':resv_line.extra_addon,
                    'pickup':resv_line.pickup, 'dropoff':resv_line.dropoff, 'arrival_trp':resv_line.arrival_trp,
                    'arrival_from':resv_line.arrival_from, 'departure_trp':resv_line.departure_trp,'departure_from':resv_line.departure_from,
                    'visa_type':resv_line.visa_type,'visa_issue':resv_line.visa_issue,'visa_expire':resv_line.visa_expire,
                    }))
                self.update({'reservation_line_ids':vals})

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
        
    cancel_rsvn_id = fields.Many2one('hms.cancel.rsvn', string="Cancel ID")
    is_partial_cancel = fields.Boolean(string='Is Partially Canceled', default=False)
    company_id = fields.Many2one('res.partner', string="Company",domain="['&',('profile_no','!=',''),('is_company','=',True)]", related='reservation_id.company_id')
    group_id = fields.Many2one('res.partner', string="Group", domain="[('is_group','=',True)]", related='reservation_id.group_id')
    guest_id = fields.Many2one('res.partner', string="Guest", domain="[('is_guest','=',True)]")        
    is_rsvn_details = fields.Boolean(string="Is Reservation Details",
                                     compute='_compute_is_rsvn_details')
    is_arrival_today = fields.Boolean(string="Is Arrival Today", compute='_compute_is_arrival_today')
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
    market = fields.Many2one('market.segment',string="Market")
    source = fields.Many2one('market.source',string="Source")
    reservation_type = fields.Many2one('rsvn.type',"Reservation Type", readonly=True)
    reservation_status = fields.Many2one('rsvn.status',"Reservation Status")
    arrival_flight = fields.Char("Arrival Flight")
    arrival_flighttime = fields.Float("AR_Flight Time")
    dep_flight = fields.Char("Departure Flight")
    dep_flighttime = fields.Float("DEP_Flight Time")
    eta = fields.Float("ETA")
    etd = fields.Float("ETD")

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
    nights = fields.Integer(string="Nights")
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

    reservation_user_id = fields.Many2one('res.users',string="User", related ='reservation_id.user_id')
    madeondate = fields.Datetime("Date", related='reservation_id.date_order')
    citime = fields.Datetime("Check-In Time")
    cotime = fields.Datetime("Check-Out Time")

    extrabed = fields.Char("Extra Bed")
    extrabed_amount = fields.Integer("Number of Extra Bed")
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
    
    def _compute_is_arrival_today(self):
        arrival_date = self.arrival
        if datetime.strptime(
                str(arrival_date),
                DEFAULT_SERVER_DATE_FORMAT).date() == datetime.now().date():
            self.is_arrival_today = True
        else:
            self.is_arrival_today = False
    
    def set_to_booking(self):
        for record in self:
            record.state = 'booking'
        return True

    @api.onchange('visa_issue','visa_expire')
    @api.constrains('visa_issue','visa_expire')
    def get_two_date_comp(self):
        for record in self:
            startdate = record.visa_issue
            enddate = record.visa_expire
            if startdate and enddate and startdate > enddate:
                raise ValidationError("Expired Date cannot be set before Issue Date.")

    @api.onchange('property_id')
    def property_onchange(self):
        res = {}
        res['domain']={'room_no':[('id', 'in', self.property_id.propertyroom_ids.ids)]}
        return res

    # Confirm Status
    def confirm_status(self):
        self.write({'state': 'confirm'})
    
    def change_to_confirm_state(self):
        for record in self:
            if record.state == 'confirm':
                record.reservation_id.write({'state': 'confirm'})

    def unconfirm_status(self):
        self.write({'state': 'reservation'})

    # Cancel Status & Cancel Table
    def cancel_status(self):
        self.write({'state': 'cancel'})
    
    def copy_cancel_record(self):
        if self.state == 'cancel':
            res = {}
            self.env['hms.cancel.rsvn'].create({
                'is_partial_cancel':
                True,
                'state':
                self.state,
                'property_id':
                self.property_id.id,
                'reservation_id':
                self.reservation_id.id,
                'user_id':
                self.reservation_user_id.id,
                'date_order':
                self.madeondate,
                'company_id':
                self.company_id.id,
                'group_id':
                self.group_id.id,
                'guest_id':
                self.guest_id.id,
                'arrival':
                self.arrival,
                'departure':
                self.departure,
                'nights':
                self.nights,
                'no_ofrooms':
                self.rooms,
                'market':
                self.market.id,
                'source':
                self.source.id,
                'reservation_type':
                self.reservation_type.id,
                'reservation_status':
                self.reservation_status.id,
                'arrival_flight':
                self.arrival_flight,
                'arrival_flighttime':
                self.arrival_flighttime,
                'dep_flight':
                self.dep_flight,
                'dep_flighttime':
                self.dep_flighttime,
                'eta':
                self.eta,
                'etd':
                self.etd,
                'reason_id':
                self.reason_id.id,
                'confirm_no':
                self.confirm_no,
                'room_no':
                self.room_no.id,
                'room_type':
                self.room_type.id,
                'pax':
                self.pax,
                'child':
                self.child,
                'ratecode_id':
                self.ratecode_id.id,
                'room_rate':
                self.room_rate,
                'updown_amt':
                self.updown_amt,
                'updown_pc':
                self.updown_pc,
                'package_id':
                self.package_id.id,
                'allotment_id':
                self.allotment_id,
                'rate_nett':
                self.rate_nett,
                'fo_remark':
                self.fo_remark,
                'hk_remark':
                self.hk_remark,
                'cashier_remark':
                self.cashier_remark,
                'general_remark':
                self.general_remark,
                'citime':
                self.citime,
                'cotime':
                self.cotime,
                'extrabed':
                self.extrabed,
                'extrabed_amount':
                self.extrabed_amount,
                'extrabed_bf':
                self.extrabed_bf,
                'extrapax':
                self.extrapax,
                'extrapax_amount':
                self.extrapax_amount,
                'extrapax_bf':
                self.extrapax_bf,
                'child_bfpax':
                self.child_bfpax,
                'child_bf':
                self.child_bf,
                'extra_addon':
                self.extra_addon,
                'pickup':
                self.pickup,
                'dropoff':
                self.dropoff,
                'arrival_trp':
                self.arrival_trp,
                'arrival_from':
                self.arrival_from,
                'departure_trp':
                self.departure_trp,
                'departure_from':
                self.departure_from,
                'visa_type':
                self.visa_type,
                'visa_issue':
                self.visa_issue,
                'visa_expire':
                self.visa_expire,
                'arrive_reason_id':
                self.arrive_reason_id,
            })
            return res

    def re_reservation(self):
        if self.reservation_type.rsvn_name == 'Confirmed':
            self.write({'state': 'confirm'})
        else:
            self.write({'state': 'reservation'})

    def checkin_status(self):
        self.write({'state': 'checkin'})

    @api.onchange('reservation_id')
    def onchange_rsvn_data(self):
        self.market = self.reservation_id.market
        self.source = self.reservation_id.source
        self.reservation_status = self.reservation_id.reservation_status
        self.reservation_type = self.reservation_id.reservation_type
        self.arrival = self.reservation_id.arrival
        self.arrival_flight = self.reservation_id.arrival_flight
        self.arrival_flighttime = self.reservation_id.arrival_flighttime
        self.departure = self.reservation_id.departure
        self.dep_flight = self.reservation_id.dep_flight
        self.dep_flighttime = self.reservation_id.dep_flighttime
        self.eta = self.reservation_id.eta
        self.etd = self.reservation_id.etd

    # @api.onchange('id', 'rooms')
    # def onchange_rsvn_rooms(self):
    #     for record in self:
    #         last_id = self.env['hms.reservation.line'].search([],
    #                                                           order='id desc',
    #                                                           limit=1)
    #         rsvn_id = self.env['hms.reservation'].search([],
    #                                                      order='id desc',
    #                                                      limit=1)
    #         if last_id and record.reservation_id == rsvn_id:
    #             prev_rooms = last_id.rooms
    #             record.rooms = record.reservation_id.no_ofrooms - prev_rooms


    def action_split(self):
        _logger.info('self = %s',self)
        rooms=self.rooms-1
        if rooms:
            super(ReservationLine,self).update({'rooms':1})
            for rec in range(rooms):
                self.env['hms.reservation.line'].create({
                    'rooms' : 1,
                })


# Cancel Reservation
class CancelReservation(models.Model):
    _name = 'hms.cancel.rsvn'
    _description = "Cancel Reservation"
    _inherit = ['mail.thread']

    is_full_cancel = fields.Boolean(string='Is Fully Canceled', default=False)
    is_partial_cancel = fields.Boolean(string='Is Partially Canceled',
                                       default=False)
    is_company = fields.Boolean(string='Is a Company', default=False)
    is_group = fields.Boolean(string="Is a Group", default=False)
    sales_id = fields.Many2one('res.partner',
                               string="Sales",
                               domain="[('company_type', '=','person')]")
    contact_id = fields.Many2one('res.partner',
                                 domain="[('company_type', '=','person')]",
                                 string="Contact")
    internal_notes = fields.Text(string="Internal Notes")
    # Common fields in both reservation & reservation line
    state = fields.Selection([
        ('booking', 'Booking'),
        ('reservation', 'Reservation'),
        ('confirm', 'Confirm'),
        ('cancel', 'Cancel'),
        ('checkin', 'Checkin'),
    ],
                             'Status',
                             readonly=True,
                             default=lambda *a: 'booking')
    property_id = fields.Many2one(
        'property.property',
        string="Property",
        default=lambda self: self.env.user.property_id.id)
    user_id = fields.Many2one('res.users',
                              string='Salesperson',
                              default=lambda self: self.env.user.id)
    date_order = fields.Datetime('Date Ordered',
                                 readonly=True,
                                 index=True,
                                 default=(lambda *a: time.strftime(dt)))
    company_id = fields.Many2one(
        'res.partner',
        string="Company",
        domain="['&',('profile_no','!=',''),('is_company','=',True)]")
    group_id = fields.Many2one('res.partner',
                               string="Group",
                               domain="[('is_group','=',True)]")
    guest_id = fields.Many2one('res.partner',
                               string="Guest",
                               domain="[('is_guest','=',True)]")
    arrival = fields.Date(string="Arrival Date", default=datetime.today())
    departure = fields.Date(
        string="Departure Date",
        default=lambda *a:
        (datetime.now() + timedelta(days=(1))).strftime('%Y-%m-%d'))
    nights = fields.Integer(string="Nights")
    no_ofrooms = fields.Integer(string="Number of Rooms")
    market = fields.Many2one('market.segment',
                             string="Market",
                             domain="[('id', '=?', market_ids)]")
    source = fields.Many2one('market.source', string="Market Source")
    reservation_type = fields.Many2one('rsvn.type',
                                       string="Reservation Type",
                                       default=2)
    reservation_status = fields.Many2one('rsvn.status',
                                         string="Reservation Status")
    arrival_flight = fields.Char(string="Arrival Flight", size=10)
    arrival_flighttime = fields.Float(string="AR-Flight Time")
    dep_flight = fields.Char(string="Departure Flight")
    dep_flighttime = fields.Float(string="DEP-Flight Time")
    eta = fields.Float(string="ETA")
    etd = fields.Float(string="ETD")
    reason_id = fields.Many2one('hms.reason', string="Reason")
    reservation_line_ids = fields.One2many('hms.reservation.line',
                                           'cancel_rsvn_id',
                                           string="Reservation Line")
    confirm_no = fields.Char(string="Confirm Number", readonly=True)

    # Fields from Reservation Line
    reservation_id = fields.Many2one('hms.reservation', string="Reservation")
    room_no = fields.Many2one('property.room', string="Room No")
    room_type = fields.Many2one('room.type',
                                string="Room Type",
                                domain="[('id', '=?', roomtype_ids)]")
    pax = fields.Integer("Pax", default=1)
    child = fields.Integer("Child")
    ratecode_id = fields.Many2one('rate.code', string="Rate Code")
    room_rate = fields.Float("Room Rate")
    updown_amt = fields.Float("Updown Amount")
    updown_pc = fields.Float("Updown PC")
    package_id = fields.Many2one('package.package', string="Package")
    allotment_id = fields.Char(string="Allotment")
    rate_nett = fields.Float(string="Rate Nett")
    fo_remark = fields.Char(string="F.O Remark")
    hk_remark = fields.Char(string="H.K Remark")
    cashier_remark = fields.Char(string="Cashier Remark")
    general_remark = fields.Char(string="General Remark")
    # specialrequest_id = fields.One2many('hms.special.request',
    #                                     'reservationline_id',
    #                                     string="Special Request")
    citime = fields.Datetime("Check-In Time")
    cotime = fields.Datetime("Check-Out Time")

    extrabed = fields.Char("Extra Bed")
    extrabed_amount = fields.Integer("Number of Extra Bed")
    extrabed_bf = fields.Float("Extra Bed Breakfast")
    extrapax = fields.Float("Extra Pax")
    extrapax_amount = fields.Float("Number of Extra Pax")
    extrapax_bf = fields.Float("Extra Pax Breakfast")
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

    # New Fields
    cancel_user_id = fields.Many2one('res.users',
                                     string='Salesperson',
                                     default=lambda self: self.env.user.id)
    cancel_datetime = fields.Datetime('Date Ordered',
                                      readonly=True,
                                      index=True,
                                      default=(lambda *a: time.strftime(dt)))   
