import base64
import logging
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules import get_module_resource
from odoo.tools import *
from datetime import datetime, date, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as dt
_logger = logging.getLogger(__name__)


class HMSReason(models.Model):
    _name = "hms.reason"
    _description = "Reason"

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    type_id = fields.Many2one('hms.reasontype',
                              string="Reason Type",
                              required=True)


class HMSReasonType(models.Model):
    _name = "hms.reasontype"
    _description = "Reason Type"

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", size=3, required=True)
    reason_ids = fields.One2many('hms.reason',
                                 'type_id',
                                 string="Reason",
                                 required=True)


#Department
class Department(models.Model):
    _name = "hms.department"
    _description = "Department"

    name = fields.Char(string="Department Name", required=True)


#Special Request
class SpecialRequest(models.Model):
    _name = "hms.special.request"
    _description = "Special Request"

    reservationline_id = fields.Many2one('hms.reservation.line',
                                         string="Reservation Line")
    department_id = fields.Char("Department")
    date = fields.Date("Date")
    name = fields.Char("Name")


# Reservation
class Reservation(models.Model):
    _name = 'hms.reservation'
    _description = "Reservation"
    _order = 'confirm_no desc'
    _inherit = ['mail.thread']

    sequence = fields.Integer(default=1)
    color = fields.Integer(string='Color Index', compute="set_kanban_color")
    active = fields.Boolean('Active', default=True, track_visibility=True)
    is_dummy = fields.Boolean(string="Dummy Room?",default = False, readonly = True)
    dummy_readonly = fields.Boolean(default = False)
    is_reservation = fields.Boolean(string="Is Reservation",
                                    compute='_compute_is_reservation')
    is_arrival_today = fields.Boolean(string="Is Arrival Today",
                                      compute='_compute_is_arrival_today')
    is_full_cancel = fields.Boolean(string='Is Fully Canceled', default=False)
    state = fields.Selection([
        ('booking', 'Booking'),
        ('reservation', 'Reservation'),
        ('confirm', 'Confirm'),
        ('cancel', 'Cancel'),
        ('checkin', 'Checkin'),
    ],
                             'Status',
                             readonly=True,
                             default='booking')
    property_id = fields.Many2one(
        'property.property',
        string="Property",
        default=lambda self: self.env.user.property_id.id)
    user_id = fields.Many2one('res.users',string='Salesperson', default=lambda self: self.env.uid)
    date_order = fields.Datetime('Date Ordered',
                                 readonly=True,
                                 required=True,
                                 index=True,
                                 default=(lambda *a: time.strftime(dt)))
    type = fields.Selection(string='Type',
                            selection=[('individual', 'Individual'),
                                       ('group', 'Group')],
                            compute='_compute_type',
                            inverse='_write_type',
                            track_visibility=True)
    is_company = fields.Boolean(string='Is a Company', default=False)
    is_group = fields.Boolean(string="Is a Group", default=False)
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
    roomtype_id = fields.Many2one('room.type',default=1)
    arrival = fields.Date(string="Arrival Date",
                          default=datetime.today(),
                          required=True)
    departure = fields.Date(
        string="Departure Date",
        default=lambda *a:
        (datetime.now() + timedelta(days=(1))).strftime('%Y-%m-%d'),
        required=True)
    nights = fields.Integer(string="Nights")
    rooms = fields.Integer(string="Number of Rooms", default=1, required=True)
    market_ids = fields.Many2many('market.segment',
                                  related="property_id.market_ids")
    market = fields.Many2one('market.segment',
                             string="Market",
                             domain="[('id', '=?', market_ids)]",
                             required=True)
    source = fields.Many2one('market.source',
                             string="Market Source",
                             required=True)
    sales_id = fields.Many2one('res.users', string="Sales", default=lambda self: self.env.uid)
    contact_id = fields.Many2one(
        'res.partner',
        domain=
        "[('company_type', '=','person'),('is_guest','!=',True),('is_group','!=',True),('is_company','!=',True)]",
        string="Contact")
    reservation_type = fields.Many2one('rsvn.type',
                                       string="Reservation Type",
                                       required=True,
                                       readonly=True,
                                       default=2, store=True)
    reservation_status = fields.Many2one(
        'rsvn.status',
        string="Reservation Status",
        domain="[('rsvntype_id', '=', reservation_type)]",
        required=True, store=True)
    arrival_flight = fields.Char(string="Arrival Flight", size=10)
    arrival_flighttime = fields.Float(string="AR-Flight Time")
    dep_flight = fields.Char(string="Departure Flight")
    dep_flighttime = fields.Float(string="DEP-Flight Time")
    eta = fields.Float(string="ETA", help="ETA")
    etd = fields.Float(string="ETD", help="ETD")
    reservation_line_ids = fields.One2many(
        'hms.reservation.line',
        'reservation_id',
        string="Reservation Line",
        track_visibility=True,
        context={'active_test': False},
        readonly=False,
        states={'cancel': [('readonly', True)]})
    confirm_no = fields.Char(string="Confirm Number", readonly=True)
    reason_id = fields.Many2one('hms.reason',
                                string="Reason",
                                domain="[('type_id.code', '=', 'CXL')]")
    internal_notes = fields.Text(string="Internal Notes")

    #Fields for statinfo
    rsvn_room_count = fields.Integer(string="Reservation",
                                     compute='_compute_rsvn_rooms')
    confirm_room_count = fields.Integer(string="Confirm",
                                        compute='_compute_confirm_rooms')
    cancel_room_count = fields.Integer(string="Canceled",
                                       compute='_compute_cancel_rooms')
    checkin_room_count = fields.Integer(string="Check-in",
                                        compute='_compute_checkin_rooms')

    def name_get(self):
        result = []
        for record in self:
            if record.guest_id:
                result.append((record.id, "{}".format(record.guest_id.name)))
            else:
                result.append((record.id, "{}".format(record.group_id.name)))
        return result

    def _compute_rsvn_rooms(self):
        hfo_reservation = self.env['hms.reservation.line'].search([('reservation_id', '=', self.id),('room_type.code', '=', 'HFO')])
        no_hfo_reservation = list(set(self.reservation_line_ids) - set(hfo_reservation))
        tmp = 0
        for record in no_hfo_reservation:
            if record.state == 'reservation':
                tmp = tmp + record.rooms
        self.rsvn_room_count = tmp

    def _compute_confirm_rooms(self):
        hfo_reservation = self.env['hms.reservation.line'].search([('reservation_id', '=', self.id),('room_type.code', '=', 'HFO')])
        no_hfo_reservation = list(set(self.reservation_line_ids) - set(hfo_reservation))
        tmp = 0
        for record in no_hfo_reservation:
            if record.state == 'confirm':
                tmp = tmp + record.rooms
        self.confirm_room_count = tmp

    def _compute_cancel_rooms(self):
        hfo_reservation = self.env['hms.reservation.line'].search([('reservation_id', '=', self.id),('room_type.code', '=', 'HFO')])
        no_hfo_reservation = list(set(self.reservation_line_ids) - set(hfo_reservation))
        tmp = 0
        for record in no_hfo_reservation:
            if record.active is False and record.state == 'cancel':
                tmp = tmp + record.rooms
        self.cancel_room_count = tmp

    def _compute_checkin_rooms(self):
        hfo_reservation = self.env['hms.reservation.line'].search([('reservation_id', '=', self.id),('room_type.code', '=', 'HFO')])
        no_hfo_reservation = list(set(self.reservation_line_ids) - set(hfo_reservation))
        tmp = 0
        for record in no_hfo_reservation:
            if record.state == 'checkin':
                tmp = tmp + record.rooms
        self.checkin_room_count = tmp

    def set_kanban_color(self):
        for record in self:
            color = 0
            if record.state == 'booking':
                color = 3
            elif record.state == 'reservation':
                color = 4
            elif record.state == 'confirm':
                color = 10
            record.color = color

    @api.depends('rooms')
    def _compute_rsvn_line_rooms(self):
        for rec in self:
            line_rooms_total = 0
            if rec.reservation_line_ids:
                for record in rec.reservation_line_ids:
                    line_rooms_total = line_rooms_total + record.rooms

                    if line_rooms_total < rec.rooms:
                        rec.no_ofrooms = rec.rooms - line_rooms_total
                    else:
                        rec.no_ofrooms = 1
            else:
                rec.no_ofrooms = rec.rooms

    #Arrival Today
    def _compute_is_arrival_today(self):
        arrival_date = self.arrival
        if datetime.strptime(
                str(arrival_date),
                DEFAULT_SERVER_DATE_FORMAT).date() == datetime.now().date():
            self.is_arrival_today = True
        else:
            self.is_arrival_today = False

    # Radio Button for Individual & Group Function
    @api.depends('is_group')
    def _compute_type(self):
        for partner in self:
            if partner.is_group or self._context.get(
                    'default_type') == 'group':
                partner.type = 'group'
                partner.is_group = True
            else:
                partner.type = 'individual'

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

    def accept_booking_status(self):
        self.write({'state': 'reservation'})
        
        for rec in self.reservation_line_ids:
            reduce = True
            property_id = rec.property_id.id
            arrival = rec.arrival
            departure = rec.departure
            room_type = rec.room_type.id
            rooms = rec.rooms
            state = rec.state
            status = 'reservation'
            rec._state_update_forecast(state,property_id,arrival,departure,room_type,rooms,reduce,status)
            rec.write({'state': status})

    def checkin_status(self):
        self.write({'state': 'checkin'})
        for rec in self:
            val = self.env['rsvn.type'].search([('rsvn_name', '=', 'Confirmed')
                                                ])
            self.reservation_type = val

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
            self.departure = arrivaldate + timedelta(days=no_of_night)

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

    #Create Function
    @api.model
    def create(self, values):
        property_id = values.get('property_id')
        property_id = self.env['property.property'].search([('id', '=',
                                                             property_id)])
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
                            ('code', '=', property_id.code +
                             property_id.confirm_id_format.code)
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

            values.update({'confirm_no': pf_no})
            res = super(Reservation, self).create(values)

            if  res.is_dummy is True :
                vals = []
                vals.append((0,0,{
                    'state' : 'booking',
                    'reservation_id' : res.id,
                    'confirm_no' : res.confirm_no,
                    'property_id':res.property_id.id,
                    'company_id' : res.company_id.id,
                    'group_id' : res.group_id,
                    'guest_id' : res.guest_id,
                    'room_type' : res.roomtype_id.id,
                    'arrival' : res.arrival,
                    'departure' : res.departure,
                    'nights' : res.nights,
                    'rooms' : 1,
                    'market' : res.market.id,
                    'source' : res.source.id,
                    'reservation_type' : res.reservation_type.id,
                    'reservation_status' : res.reservation_status.id,
                    'arrival_flight' : res.arrival_flight,
                    'arrival_flighttime' : res.arrival_flighttime,
                    'dep_flight' : res.dep_flight,
                    'dep_flighttime' : res.dep_flighttime,
                    'eta' : res.eta,
                    'etd' : res.etd,
                }))
                res.update({'reservation_line_ids': vals,'dummy_readonly': True})

        return res

    # Write Function
    def write(self, values):
        res = super(Reservation, self).write(values)
        dummy = values.get('is_dummy')
        if 'is_dummy' in values.keys():
            if dummy is True:
                vals = []
                vals.append((0,0,{
                    'state' : 'booking',
                    'reservation_id' : self.id,
                    'confirm_no' : self.confirm_no,
                    'property_id':self.property_id.id,
                    'company_id' : self.company_id.id,
                    'group_id' : self.group_id.id,
                    'guest_id' : self.guest_id.id,
                    'room_type' : self.roomtype_id.id,
                    'arrival' : self.arrival,
                    'departure' : self.departure,
                    'nights' : self.nights,
                    'rooms' : 1,
                    'market' : self.market.id,
                    'source' : self.source.id,
                    'reservation_type' : self.reservation_type.id,
                    'reservation_status' : self.reservation_status.id,
                    'arrival_flight' : self.arrival_flight,
                    'arrival_flighttime' : self.arrival_flighttime,
                    'dep_flight' : self.dep_flight,
                    'dep_flighttime' : self.dep_flighttime,
                    'eta' : self.eta,
                    'etd' : self.etd,
                }))
                self.update({'reservation_line_ids': vals,'dummy_readonly': True})

        return res

    # Unlink Function
    def unlink(self):

        reservation_line_objs = self.env['hms.reservation.line']
        for record in self:
            # state = record.state
            # rooms = record.rooms
            # room_type = record.roomtype_id.id
            # property_id = record.property_id.id
            # arrival = record.arrival
            # departure = record.departure
            # reduce = True
            # status = 'HFO'
            # record.reservation_line_ids._state_update_forecast(state,property_id,arrival,departure,room_type,rooms,reduce,status)
            reservation_line_objs += self.env['hms.reservation.line'].search([('reservation_id', '=', record.id)])
            reservation_line_objs.unlink()
        
        res = super(Reservation, self).unlink()
        return res
    # All Split Rsvn Action
    def action_split(self):
        # arrival = self.arrival
        # departure = self.departure
        for resv_line in self.reservation_line_ids:
            room = resv_line.rooms
            if room and room >= 2:
                resv_line.update({'rooms': 1})
                vals = []
                for record in range(room - 1):
                    vals.append((0, 0, {
                        'rooms':
                        1,
                        'arrival':
                        resv_line.arrival,
                        'departure':
                        resv_line.departure,
                        'arrival_flight':
                        resv_line.arrival_flight,
                        'dep_flight':
                        resv_line.dep_flight,
                        'arrival_flighttime':
                        resv_line.arrival_flighttime,
                        'dep_flighttime':
                        resv_line.dep_flighttime,
                        'market':
                        resv_line.market.id,
                        'source':
                        resv_line.source.id,
                        'reservation_type':
                        resv_line.reservation_type.id,
                        'reservation_status':
                        resv_line.reservation_status.id,
                        'eta':
                        resv_line.eta,
                        'etd':
                        resv_line.etd,
                        'room_type':
                        resv_line.room_type.id,
                        'pax':
                        resv_line.pax,
                        'child':
                        resv_line.child,
                        'ratecode_id':
                        resv_line.ratecode_id.id,
                        'room_rate':
                        resv_line.room_rate,
                        'updown_amt':
                        resv_line.updown_amt,
                        'updown_pc':
                        resv_line.updown_pc,
                        'reason_id':
                        resv_line.reason_id.id,
                        'package_id':
                        resv_line.package_id.id,
                        'rate_nett':
                        resv_line.rate_nett,
                        'fo_remark':
                        resv_line.fo_remark,
                        'hk_remark':
                        resv_line.hk_remark,
                        'cashier_remark':
                        resv_line.cashier_remark,
                        'general_remark':
                        resv_line.general_remark,
                        'madeondate':
                        resv_line.madeondate,
                        'citime':
                        resv_line.citime,
                        'cotime':
                        resv_line.cotime,
                        'extrabed':
                        resv_line.extrabed,
                        'extrabed_amount':
                        resv_line.extrabed_amount,
                        'extrabed_bf':
                        resv_line.extrabed_bf,
                        'extrapax':
                        resv_line.extrapax,
                        'extrapax_amount':
                        resv_line.extrapax_amount,
                        'extrapax_bf':
                        resv_line.extrapax_bf,
                        'child_bfpax':
                        resv_line.child_bfpax,
                        'child_bf':
                        resv_line.child_bf,
                        'extra_addon':
                        resv_line.extra_addon,
                        'pickup':
                        resv_line.pickup,
                        'dropoff':
                        resv_line.dropoff,
                        'arrival_trp':
                        resv_line.arrival_trp,
                        'arrival_from':
                        resv_line.arrival_from,
                        'departure_trp':
                        resv_line.departure_trp,
                        'departure_from':
                        resv_line.departure_from,
                        'visa_type':
                        resv_line.visa_type,
                        'visa_issue':
                        resv_line.visa_issue,
                        'visa_expire':
                        resv_line.visa_expire,
                    }))
                self.update({'reservation_line_ids': vals})

    # @api.onchange('state','reservation_line_ids')
    # def _change_hfo_state(self):
    #     for record in self:
    #         hfo_reservation = self.env['hms.reservation.line'].search([('reservation_id', '=', record.id),('room_type.code', '=', 'HFO')])
    #         for rec in hfo_reservation:
    #             rec.state = record.state

# Reservation Line
class ReservationLine(models.Model):
    _name = "hms.reservation.line"
    _description = "Reservation Line"

    def get_rooms(self):
        if self._context.get('rooms') != False:
            return self._context.get('rooms')

    def get_rsvn_type(self):
        if self._context.get('reservation_type') != False:
            return self._context.get('reservation_type')

    def get_rsvn_status(self):
        if self._context.get('reservation_status') != False:
            return self._context.get('reservation_status')
            
    def get_arrival(self):
        if self._context.get('arrival') != False:
            return self._context.get('arrival')

    def get_departure(self):
        if self._context.get('departure') != False:
            return self._context.get('departure')

    def get_nights(self):
        if self._context.get('nights') != False:
            return self._context.get('nights')

    def get_state(self):
        if self._context.get('state') != False:
            return self._context.get('state')

    is_no_show = fields.Boolean(string = "No Show",default = False, readonly=True)
    is_roomtype_fix = fields.Boolean(string = "Fixed Type?", readonly=False, related="room_type.fix_type")
    sequence = fields.Integer(default=1)
    color = fields.Integer(string='Color Index', compute="set_kanban_color")
    ispartial = fields.Boolean('Partial',default=True)
    active = fields.Boolean('Active', default=True, track_visibility=True)
    cancel_rsvn_ids = fields.One2many('hms.cancel.rsvn',
                                      'reservation_line_id',
                                      string="Cancel Reservation")
    company_id = fields.Many2one(
        'res.partner',
        string="Company",
        domain="['&',('profile_no','!=',''),('is_company','=',True)]",
        related='reservation_id.company_id')
    group_id = fields.Many2one('res.partner',
                               string="Group",
                               domain="[('is_group','=',True)]",
                               related='reservation_id.group_id')
    guest_id = fields.Many2one('res.partner',
                               string="Guest Name",
                               domain="[('is_guest','=',True)]")
    is_arrival_today = fields.Boolean(string="Is Arrival Today",
                                      compute='_compute_is_arrival_today')
    reservation_id = fields.Many2one('hms.reservation', string="Reservation")
    property_id = fields.Many2one('property.property',
                                  string="Property",
                                  readonly=True,
                                  related='reservation_id.property_id')
    confirm_no = fields.Char(string="Confirm No.",
                             readonly=True,
                             related='reservation_id.confirm_no')
    state = fields.Selection([
        ('booking', 'Booking'),
        ('reservation', 'Reservation'),
        ('confirm', 'Confirm'),
        ('cancel', 'Cancel'),
        ('checkin', 'Checkin'),
    ],
                             default=get_state,
                             store=True)
    # default=lambda *a: 'booking')
    market_ids = fields.Many2many('market.segment',
                                  related="property_id.market_ids")
    market = fields.Many2one('market.segment',
                             string="Market",
                             domain="[('id', '=?', market_ids)]")
    source = fields.Many2one('market.source', string="Source")
    reservation_type = fields.Many2one('rsvn.type',
                                       "Reservation Type", default=get_rsvn_type,
                                       readonly=True, store=True)
    reservation_status = fields.Many2one('rsvn.status',
                                         "Reservation Status",
                                         domain="[('rsvntype_id', '=', reservation_type)]", 
                                         default=get_rsvn_status, store=True)
    arrival_flight = fields.Char("Arrival Flight")
    arrival_flighttime = fields.Float("AR_Flight Time")
    dep_flight = fields.Char("Departure Flight")
    dep_flighttime = fields.Float("DEP_Flight Time")
    eta = fields.Float("ETA")
    etd = fields.Float("ETD")

    room_no = fields.Many2one('property.room', string="Room No")
    roomtype_ids = fields.Many2many('room.type',
                                    related="property_id.roomtype_ids")
    room_type = fields.Many2one('room.type',
                                string="Room Type",
                                domain="[('id', '=?', roomtype_ids)]",
                                delegate=True,
                                ondelete='cascade',
                                index=True)
    bedtype_ids = fields.Many2many('bed.type', related="room_type.bed_type")
    bedtype_id = fields.Many2one('bed.type', domain="[('id', '=?', bedtype_ids)]" )
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
    nights = fields.Integer(string="Nights", default=get_nights)
    rooms = fields.Integer("Rooms")
    avail_room_ids = fields.Many2many('property.room',
                                      string="Room Nos",
                                      compute='get_avail_room_ids')
    pax = fields.Integer("Pax", default=1)
    child = fields.Integer("Child")
    ratecode_id = fields.Many2one('rate.code', string="Rate Code")
    room_rate = fields.Float("Room Rate")
    updown_amt = fields.Float("Updown Amount")
    updown_pc = fields.Float("Updown PC")
    reason_id = fields.Many2one('hms.reason',
                                string="Reason",
                                domain="[('type_id', '=', 1)]")
    discount_reason_id = fields.Many2one('hms.reason',
                                         string="Discount Reason",
                                         domain="[('type_id', '=', 2)]")
    package_id = fields.Many2one('package.package', string="Package")
    allotment_id = fields.Char(string="Allotment")
    rate_nett = fields.Float(string="Rate Nett")
    fo_remark = fields.Char(string="F.O Remark")
    hk_remark = fields.Char(string="H.K Remark")
    cashier_remark = fields.Char(string="Cashier Remark")
    general_remark = fields.Char(string="General Remark")
    specialrequest_id = fields.One2many('hms.special.request',
                                        'reservationline_id',
                                        string="Special Request")

    reservation_user_id = fields.Many2one('res.users',
                                          string="User",
                                          related='reservation_id.user_id')
    madeondate = fields.Datetime("Date", related='reservation_id.date_order')
    citime = fields.Datetime("Check-In Time")
    cotime = fields.Datetime("Check-Out Time")

    extrabed = fields.Integer("Extra Bed")
    extrabed_amount = fields.Integer("Number of Extra Bed")
    extrabed_bf = fields.Float("Extra Bed Breakfast")
    extrapax = fields.Integer("Extra Pax")
    extrapax_amount = fields.Float("Number of Extra Pax")
    extrapax_bf = fields.Float("Extra Pax Breakfast")
    child_bfpax = fields.Integer("Child BF-Pax")
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

    room_transaction_line_ids = fields.One2many(
        'hms.room.transaction.charge.line', 'reservation_line_id', "Charges")

    def set_kanban_color(self):
        for record in self:
            color = 0
            if record.state == 'booking':
                color = 3
            elif record.state == 'reservation':
                color = 4
            elif record.state == 'confirm':
                color = 10
            record.color = color

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

    def set_room_status_checkin(self):
        """
        This method is used to change the state
        to occupied of the hotel room.
        ---------------------------------------
        @param self: object pointer
        """
        return self.write({ 'color': 2})


    @api.constrains('arrival')
    def check_arrival_date(self):
        for rec in self:
            arrival_date = rec.arrival
            if arrival_date:
                if datetime.strptime(str(arrival_date),
                                     DEFAULT_SERVER_DATE_FORMAT).date(
                                     ) < datetime.now().date():
                    raise ValidationError(
                        _('Check-in date should be greater than or equal to the current date.'
                          ))
                    rec.arrival = datetime.now().date()

    @api.constrains('departure')
    def compare_two_date(self):
        for rec in self:
            arrival_date = rec.arrival
            departure_date = rec.departure
            if arrival_date and departure_date:
                if arrival_date > departure_date:
                    raise ValidationError(
                        _('Check-out date should be greater than Check-in date.'
                          ))

    # Change Departure Date
    @api.onchange('arrival')
    def onchange_departure_date(self):
        arrivaldate = self.arrival
        no_of_night = self.nights
        if arrivaldate and no_of_night:
            self.departure = arrivaldate + timedelta(days=no_of_night)

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

    @api.onchange('visa_issue', 'visa_expire')
    @api.constrains('visa_issue', 'visa_expire')
    def get_two_date_comp(self):
        for record in self:
            startdate = record.visa_issue
            enddate = record.visa_expire
            if startdate and enddate and startdate > enddate:
                raise ValidationError(
                    "Expired Date cannot be set before Issue Date.")

    # Cancel Status & Cancel Table
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
                'reservation_line_id':
                self.id,
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

    # For Edit Button to Open Current Record in Edit Mode
    def action_show_record_details(self):
        # self.ensure_one()
        view = self.env.ref('hms.reservation_line_view_form')
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hms.reservation.line',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'res_id': self.id,
            'context': dict(self.env.context),
            'target': 'current',
        }

    # Re-Reservation 
    def re_reservation(self):
        if self.reservation_type.rsvn_name == 'Confirmed':
            self.write({'state': 'confirm'})
        else:
            self.write({'state': 'reservation'})

    def checkin_status(self):
        self.write({'state': 'checkin'})

    @api.onchange('reservation_id')
    def onchange_rsvn_data(self):
        # self.market = self.reservation_id.market
        # self.source = self.reservation_id.source
        # self.reservation_status = self.reservation_id.reservation_status
        # self.reservation_type = self.reservation_id.reservation_type
        # self.arrival = self.reservation_id.arrival
        self.arrival_flight = self.reservation_id.arrival_flight
        self.arrival_flighttime = self.reservation_id.arrival_flighttime
        # self.departure = self.reservation_id.departure
        self.dep_flight = self.reservation_id.dep_flight
        self.dep_flighttime = self.reservation_id.dep_flighttime
        self.eta = self.reservation_id.eta
        self.etd = self.reservation_id.etd
        # self.state = self.reservation_id.state

    @api.depends('room_no', 'property_id', 'arrival', 'departure', 'room_type','bedtype_id')
    def get_avail_room_ids(self):
        for rec in self:
            room_type = rec.room_type._origin.id
            room_type_obj = self.env['room.type'].search([
                ('id', '=', room_type)
            ])

            bedtype_id = rec.bedtype_id._origin.id

            avail_rooms=[]
            if room_type_obj.fix_type == True:

                total_room_per_roomtype = self.env['property.room'].search([
                    ('property_id', '=', rec.property_id.id),
                    ('roomtype_id', '=', room_type)
                ]).ids

                occ_room_per_roomtype = self.env['hms.reservation.line'].search([
                    ('property_id', '=', rec.property_id.id),
                    ('room_type', '=', room_type),
                    ('arrival', '<', rec.departure),
                    ('departure', '>', rec.arrival)
                ]).room_no.ids

                avail_rooms = list(
                    set(total_room_per_roomtype) - set(occ_room_per_roomtype))

                current_rooms = self.reservation_id.reservation_line_ids.filtered(
                    lambda r: r.room_type.id == rec.room_type.id and r.arrival <
                    rec.departure and r.departure > rec.arrival).room_no.ids

                avail_rooms = list(set(avail_rooms) - set(current_rooms))
                # rec.avail_room_ids = avail_rooms

            elif room_type_obj.fix_type == False:

                if bedtype_id:

                    total_room_per_roomtype = self.env['property.room'].search([
                        ('property_id', '=', rec.property_id.id),
                        ('roomtype_id', '=', room_type),
                        ('bedtype_id', '=', bedtype_id),
                    ]).ids

                    occ_room_per_roomtype = self.env['hms.reservation.line'].search([
                        ('property_id', '=', rec.property_id.id),
                        ('room_type', '=', room_type),
                        ('bedtype_id', '=', bedtype_id),
                        ('arrival', '<', rec.departure),
                        ('departure', '>', rec.arrival)
                    ]).room_no.ids

                    avail_rooms = list(set(total_room_per_roomtype) - set(occ_room_per_roomtype))

                    current_rooms = self.reservation_id.reservation_line_ids.filtered(
                        lambda x: x.room_type.id == rec.room_type.id and x.arrival <
                        rec.departure and x.departure > rec.arrival and x.bedtype_id.id == rec.bedtype_id.id).room_no.ids

                    avail_rooms = list(set(avail_rooms) - set(current_rooms))

                    if len(avail_rooms) == 0:

                        total_room_per_roomtype = self.env['property.room'].search([
                            ('property_id', '=', rec.property_id.id),
                            ('roomtype_id', '=', room_type),
                            ('zip_type', '=', True),
                        ]).ids

                        occ_room_per_roomtype = self.env['hms.reservation.line'].search([
                            ('property_id', '=', rec.property_id.id),
                            ('room_type', '=', room_type),
                            ('arrival', '<', rec.departure),
                            ('departure', '>', rec.arrival),
                        ]).room_no.ids

                        avail_rooms = list(set(total_room_per_roomtype) - set(occ_room_per_roomtype))

                        current_rooms = self.reservation_id.reservation_line_ids.filtered(
                            lambda x: x.room_type.id == rec.room_type.id and x.arrival <
                            rec.departure and x.departure > rec.arrival and x.bedtype_id == rec.bedtype_id.id).room_no.ids

                        avail_rooms = list(set(avail_rooms) - set(current_rooms))

            rec.avail_room_ids = avail_rooms
                    
    @api.constrains('id','rooms')
    def _change_update_rooms(self):
        for rec in self:
            line_rooms_total = 0
            for record in rec.reservation_id.reservation_line_ids:
                if record.room_type.code[0] != "H":
                    line_rooms_total = line_rooms_total + record.rooms
            if self.reservation_id.rooms != line_rooms_total:
                self.reservation_id.rooms = line_rooms_total

    @api.constrains('arrival','departure')
    def _update_arrival_departure(self):
        tmp_arrival_date = date(9999, 1, 11)
        tmp_departure_date = date(1000, 1, 11)
        # hfo_reservation = self.env['hms.reservation.line'].search([('reservation_id', '=', self.reservation_id.id),('room_type', '=ilike', 'H%')])
        for rec in self.reservation_id.reservation_line_ids:
            if rec.room_type[0] != 'H':
                if rec.arrival < tmp_arrival_date:
                    tmp_arrival_date = rec.arrival
                if rec.departure > tmp_departure_date:
                    tmp_departure_date = rec.departure
        self.reservation_id.write({'arrival': tmp_arrival_date})
        self.reservation_id.write({'departure': tmp_departure_date})
        # hfo_reservation = self.reservation_id.reservation_line_ids.filtered(
        #                 lambda r: r.room_type[0] == 'H' )
        # hfo_reservation.arrival = tmp_arrival_date
        # hfo_reservation.departure = tmp_departure_date
        # if hfo_reservation :
        #     hfo_reservation.update({'arrival': tmp_arrival_date,'departure': tmp_departure_date})

    # @api.onchange('reservation_id')
    # def onchange_hfo_arrival(self):



    @api.onchange('arrival', 'departure', 'room_type', 'rooms')
    def onchange_roomtype(self):
        for rec in self:
            if not rec.room_type:
                if not rec.rooms:
                    # Save Record for Reservation Line
                    occ_room_per_room = self.env[
                        'hms.reservation.line'].search([
                            ('property_id', '=', rec.property_id.id),
                            ('reservation_id', '=',
                             rec.reservation_id._origin.id),
                            ('arrival', '<', rec.departure),
                            ('departure', '>', rec.arrival)
                        ])
                    occ_room_count = sum(occ_room_per_room.mapped('rooms'))
                    for occ_room in occ_room_per_room:
                        if occ_room.id == rec.id:
                            occ_room_count -= rec.rooms

                    # Current Virtual Rooms Before Save to database
                    current_rooms = rec.reservation_id.reservation_line_ids.filtered(
                        lambda r: r._origin.id not in occ_room_per_room.ids and
                        r.arrival < rec.departure and r.departure > rec.arrival
                    )

                    current_rooms_tmp = self.env['hms.reservation.line']
                    current_rooms = current_rooms - occ_room_per_room
                    len_current_count = len(current_rooms)
                    count = 1
                    for curr_room in current_rooms:
                        if curr_room._origin.id not in occ_room_per_room.ids and count < len_current_count:
                            current_rooms_tmp += curr_room
                        count += 1

                    current_rooms = current_rooms_tmp
                    curr_room_count = sum(current_rooms.mapped('rooms'))
                    t_rooms = occ_room_count + curr_room_count
                    total_rooms = rec.get_rooms()
                    if total_rooms > t_rooms:
                        rec.rooms = total_rooms - t_rooms
                    else:
                        rec.rooms = 1
                return

            room_type = rec.room_type._origin.id
            rt_avails = self.env['roomtype.available'].search([
                ('property_id', '=', rec.property_id.id),
                ('ravail_date', '>=', rec.arrival),
                ('ravail_date', '<', rec.departure),
                ('ravail_rmty', '=', room_type)
            ])
            avail_count = 0
            available_room = 0
            vals = []
            for rtavail in rt_avails:
                avail_room_count = rtavail.ravail_totalroom
                occ_room_count = rtavail.ravail_booking + rtavail.ravail_unconfirm
                # Save Record for Reservation Line
                occ_room_per_roomtype = self.env[
                    'hms.reservation.line'].search([
                        ('property_id', '=', rec.property_id.id),
                        ('room_type', '=', room_type),
                        ('arrival', '<', rec.departure),
                        ('departure', '>', rec.arrival)
                    ])
                # occ_room_count = sum(occ_room_per_roomtype.mapped('rooms'))
                # for occ_room in occ_room_per_roomtype:
                #     if occ_room.id == rec.id:
                #         occ_room_count -= rec.rooms

                # Current Virtual Rooms Before Save to database
                current_rooms = rec.reservation_id.reservation_line_ids.filtered(
                    lambda r: r._origin.id not in occ_room_per_roomtype.ids and
                    r.room_type.id == rec.room_type.id and r.arrival < rec.
                    departure and r.departure > rec.arrival)

                current_rooms_tmp = self.env['hms.reservation.line']
                current_rooms = current_rooms - occ_room_per_roomtype
                for curr_room in current_rooms:
                    if curr_room._origin.id not in occ_room_per_roomtype.ids:
                        current_rooms_tmp += curr_room
                current_rooms = current_rooms_tmp
                curr_room_count = sum(current_rooms.mapped('rooms'))
                if current_rooms and type(rec.id) != int:
                    curr_room_count -= sum(rec.mapped('rooms')) * 2

                avail_room_count = avail_room_count - (occ_room_count +
                                                       curr_room_count)

                if avail_room_count >= rec.rooms:
                    avail_count += 1
                    vals.append({
                        'occupied_date': rtavail.ravail_date,
                        'room_type': rec.room_type.name,
                        'total_room': rec.rooms,
                        'status': 'Available',
                        'overbook_rooms': 0,
                    })
                else:
                    over_booking = rec.rooms - avail_room_count
                    avail_count -= 1
                    vals.append({
                        'occupied_date': rtavail.ravail_date,
                        'room_type': rec.room_type.name,
                        'total_room': rec.rooms,
                        'status': 'Overbooking',
                        'overbook_rooms': over_booking,
                    })
            if avail_count < 0:
                message = "Booking Date" + "\t" + "Room Type" + "\t" + "Booking Room" + "\t" + "Status" + "\t" + "\t" + "Overbook" + "\n"
                if vals:
                    for val in vals:
                        date = val["occupied_date"].strftime('%d/%m/%Y')
                        message += ' ' + date + "\t" + val[
                            "room_type"] + "\t" + "\t" + str(
                                val["total_room"]
                            ) + "\t" + "\t" + val["status"] + "\t"

                        if val["overbook_rooms"]:
                            message += "\t" + str(val["overbook_rooms"]) + "\n"
                        else:
                            message += "\n"

                return {
                    'warning': {
                        'title': _('Warning'),
                        'message': _(' %s ' % (message))
                    }
                }

        return

    # Split Reservation
    def action_split(self):
        _logger.info('self = %s', self)
        rooms = self.rooms - 1
        if rooms:
            # super(ReservationLine,self).update({'rooms':1})
            self.update({'rooms': 1})
            vals = []
            for rec in range(rooms):
                vals.append((0, 0, {
                    'rooms': 1,
                    'arrival': self.arrival,
                    'departure': self.departure,
                    'arrival_flight': self.arrival_flight,
                    'dep_flight': self.dep_flight,
                    'arrival_flighttime': self.arrival_flighttime,
                    'dep_flighttime': self.dep_flighttime,
                    'market': self.market.id,
                    'source': self.source.id,
                    'reservation_type': self.reservation_type.id,
                    'reservation_status': self.reservation_status.id,
                    'eta': self.eta,
                    'etd': self.etd,
                    'room_type': self.room_type.id,
                    'pax': self.pax,
                    'child': self.child,
                    'ratecode_id': self.ratecode_id.id,
                    'room_rate': self.room_rate,
                    'updown_amt': self.updown_amt,
                    'updown_pc': self.updown_pc,
                    'reason_id': self.reason_id.id,
                    'package_id': self.package_id.id,
                    'rate_nett': self.rate_nett,
                    'fo_remark': self.fo_remark,
                    'hk_remark': self.hk_remark,
                    'cashier_remark': self.cashier_remark,
                    'general_remark': self.general_remark,
                    'madeondate': self.madeondate,
                    'citime': self.citime,
                    'cotime': self.cotime,
                    'extrabed': self.extrabed,
                    'extrabed_amount': self.extrabed_amount,
                    'extrabed_bf': self.extrabed_bf,
                    'extrapax': self.extrapax,
                    'extrapax_amount': self.extrapax_amount,
                    'extrapax_bf': self.extrapax_bf,
                    'child_bfpax': self.child_bfpax,
                    'child_bf': self.child_bf,
                    'extra_addon': self.extra_addon,
                    'pickup': self.pickup,
                    'dropoff': self.dropoff,
                    'arrival_trp': self.arrival_trp,
                    'arrival_from': self.arrival_from,
                    'departure_trp': self.departure_trp,
                    'departure_from': self.departure_from,
                    'visa_type': self.visa_type,
                    'visa_issue': self.visa_issue,
                    'visa_expire': self.visa_expire,
                }))
            self.reservation_id.update({'reservation_line_ids': vals})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.model
    def create(self, values):
        # _logger.info(values)
        res = super(ReservationLine, self).create(values)

        state = res.state
        rooms = res.rooms
        room_type = res.room_type.id
        property_id = res.property_id.id
        arrival = res.arrival
        departure = res.departure
        reduce = False
        status = ''
        self._state_update_forecast(state,property_id,arrival,departure,room_type,rooms,reduce,status)
        
        return res

    # Write Function
    def write(self, values):

        rooms_changes = self._origin.read(['rooms'])
        index = len(rooms_changes) - 1
        rooms_dict = rooms_changes[index]
        rooms = int(rooms_dict['rooms'])
        old_room_type = self.room_type
        arrival = self.arrival
        departure = self.departure
        night_changes = self._origin.read(['nights'])
        ind = len(night_changes) - 1
        nights_dict = night_changes[ind]
        nights = int(nights_dict['nights'])

        # Restrict dragging state to booking state
        if 'state' in values.keys():
            previous_state = self.state
            new_state = values.get('state')
            if new_state == 'booking' and (previous_state in [
                    'reservation', 'confirm'
            ]):
                raise ValidationError(
                    _("You can't go back from '%s' state to 'booking' state!" %
                      (previous_state)))

        if 'rooms' in values.keys() or 'arrival' in values.keys(
        ) or 'departure' in values.keys() or 'room_type' in values.keys(
        ) or 'nights' in values.keys():
            property_id = self.property_id
            state = self.state
            newroom_type = values.get('room_type')
            newroom_type = self.env['room.type'].search([('id', '=',
                                                          newroom_type)])
            new_arrival = values.get('arrival')
            if new_arrival:
                new_arrival = datetime.strptime(str(new_arrival),
                                                '%Y-%m-%d').date()
            new_departure = values.get('departure')
            if new_departure:
                new_departure = datetime.strptime(str(new_departure),
                                                  '%Y-%m-%d').date()
            new_nights = values.get('nights')
            new_rooms = values.get('rooms')
            status = 'reduce'
            # Reduce on Availability and room Type avaialable
            self._state_update_forecast(self.state,property_id.id,arrival,departure,old_room_type.id,rooms,True,status)
            # oldrt_avails = self.env['roomtype.available'].search([
            #     ('property_id', '=', property_id.id),
            #     ('ravail_date', '>=', arrival),
            #     ('ravail_date', '<', departure),
            #     ('ravail_rmty', '=', old_room_type.id)
            # ])
            # oldavails = self.env['availability.availability'].search([
            #     ('property_id', '=', property_id.id),
            #     ('avail_date', '>=', arrival), ('avail_date', '<', departure)
            # ])
            # olddep_avails = self.env['availability.availability'].search([
            #     ('property_id', '=', property_id.id),
            #     ('avail_date', '=', departure)
            # ])
            # if self.state == 'confirm':
            #     for record in oldrt_avails:
            #         record.ravail_occupancy -= rooms
            #     for avail in oldavails:
            #         avail.avail_occupancy -= rooms
            #         if avail.avail_date == arrival:
            #             avail.avail_arrival -= rooms
            #     for depavail in olddep_avails:
            #         if depavail.avail_date == departure:
            #             depavail.avail_dep -= rooms
            # elif self.state == 'reservation':
            #     for record in oldrt_avails:
            #         record.ravail_unconfirm -= rooms
            #     for avail in oldavails:
            #         avail.avail_unconfirm -= rooms
            # elif self.state == 'booking':
            #     for record in oldrt_avails:
            #         record.ravail_booking -= rooms
            #     for avail in oldavails:
            #         avail.avail_booking -= rooms


            # Check & Retreive for New Availability
            rt_avails = self.env['roomtype.available']
            avails = self.env['availability.availability']
            dep_avails = self.env['availability.availability']
            # Check & Retreive for New Availability
            if new_arrival or new_departure or new_nights:
                if newroom_type:
                    rt_avails = self.env['roomtype.available'].search([
                        ('property_id', '=', property_id.id),
                        ('ravail_date', '>=', new_arrival),
                        ('ravail_date', '<', new_departure),
                        ('ravail_rmty', '=', newroom_type.id)
                    ])
                else:
                    rt_avails = self.env['roomtype.available'].search([
                        ('property_id', '=', property_id.id),
                        ('ravail_date', '>=', new_arrival),
                        ('ravail_date', '<', new_departure),
                        ('ravail_rmty', '=', old_room_type.id)
                    ])
                avails = self.env['availability.availability'].search([
                    ('property_id', '=', property_id.id),
                    ('avail_date', '>=', new_arrival),
                    ('avail_date', '<', new_departure)
                ])
                dep_avails = self.env['availability.availability'].search([
                    ('property_id', '=', property_id.id),
                    ('avail_date', '=', new_departure)
                ])
                if new_rooms:
                    if self.state == 'confirm':
                        for record in rt_avails:
                            record.ravail_occupancy += new_rooms
                        for avail in avails:
                            avail.avail_occupancy += new_rooms
                            if avail.avail_date == new_arrival:
                                avail.avail_arrival += new_rooms
                        for depavail in dep_avails:
                            if depavail.avail_date == new_departure:
                                depavail.avail_dep += new_rooms
                    elif self.state == 'reservation':
                        for record in rt_avails:
                            record.ravail_unconfirm += new_rooms
                        for avail in avails:
                            avail.avail_unconfirm += new_rooms
                    elif self.state == 'booking':
                        for record in rt_avails:
                            record.ravail_booking += new_rooms
                        for avail in avails:
                            avail.avail_booking += new_rooms
                else:  # Old Rooms Update for changes arrival/departure & nights
                    if self.state == 'confirm':
                        for record in rt_avails:
                            record.ravail_occupancy += rooms
                        for avail in avails:
                            avail.avail_occupancy += rooms
                            if avail.avail_date == new_arrival:
                                avail.avail_arrival += rooms
                        for depavail in dep_avails:
                            if depavail.avail_date == new_departure:
                                depavail.avail_dep += rooms
                    elif self.state == 'reservation':
                        for record in rt_avails:
                            record.ravail_unconfirm += rooms
                        for avail in avails:
                            avail.avail_unconfirm += rooms
            else:  # Old Arrival/Departure/Nights Update for Availability
                if newroom_type:
                    rt_avails = self.env['roomtype.available'].search([
                        ('property_id', '=', property_id.id),
                        ('ravail_date', '>=', arrival),
                        ('ravail_date', '<', departure),
                        ('ravail_rmty', '=', newroom_type.id)
                    ])
                else:
                    rt_avails = self.env['roomtype.available'].search([
                        ('property_id', '=', property_id.id),
                        ('ravail_date', '>=', arrival),
                        ('ravail_date', '<', departure),
                        ('ravail_rmty', '=', old_room_type.id)
                    ])
                avails = self.env['availability.availability'].search([
                    ('property_id', '=', property_id.id),
                    ('avail_date', '>=', arrival),
                    ('avail_date', '<', departure)
                ])
                dep_avails = self.env['availability.availability'].search([
                    ('property_id', '=', property_id.id),
                    ('avail_date', '=', departure)
                ])
                # Update rooms for availability
                if new_rooms:
                    if self.state == 'confirm':
                        values.update({'color': 2, 'state': 'confirm'})
                        for record in rt_avails:
                            record.ravail_occupancy += new_rooms
                        for avail in avails:
                            avail.avail_occupancy += new_rooms
                            if avail.avail_date == arrival:
                                avail.avail_arrival += new_rooms
                        for depavail in dep_avails:
                            if depavail.avail_date == departure:
                                depavail.avail_dep += new_rooms
                    elif self.state == 'reservation':
                        values.update({'color': 3, 'state': 'reservation'})
                        for record in rt_avails:
                            record.ravail_unconfirm += new_rooms
                        for avail in avails:
                            avail.avail_unconfirm += new_rooms
                else:  # Old Rooms Update for changes arrival/departure & nights
                    if self.state == 'confirm':
                        values.update({'color': 2, 'state': 'confirm'})
                        for record in rt_avails:
                            record.ravail_occupancy += rooms
                        for avail in avails:
                            avail.avail_occupancy += rooms
                            if avail.avail_date == arrival:
                                avail.avail_arrival += rooms
                        for depavail in dep_avails:
                            if depavail.avail_date == departure:
                                depavail.avail_dep += rooms
                    elif self.state == 'reservation':
                        values.update({'color': 3, 'state': 'reservation'})
                        for record in rt_avails:
                            record.ravail_unconfirm += rooms
                        for avail in avails:
                            avail.avail_unconfirm += rooms

        res = super(ReservationLine, self).write(values)
        return res

    # Unlink Function
    def unlink(self):

        for record in self:
            state = record.state
            rooms = record.rooms
            room_type = record.room_type.id
            property_id = record.property_id.id
            arrival = record.arrival
            departure = record.departure
            reduce = True
            status = 'HFO'
            record._state_update_forecast(state,property_id,arrival,departure,room_type,rooms,reduce,status)

            record.reservation_id.rooms = record.reservation_id.rooms - record.rooms
        
        res = super(ReservationLine, self).unlink()
        return res

    # State Update Forecast
    def _state_update_forecast(self,state,property_id,arrival,departure,room_type,rooms,reduce,status):

        roomtype = self.env['room.type'].search([('id', '=', room_type)])

        if roomtype.code[0] != 'H':
            rt_avails = self.env['roomtype.available'].search([
                ('property_id', '=', property_id),
                ('ravail_date', '>=', arrival), ('ravail_date', '<', departure),
                ('ravail_rmty', '=', room_type)
            ])
            avails = self.env['availability.availability'].search([
                ('property_id', '=', property_id),
                ('avail_date', '>=', arrival), ('avail_date', '<', departure)
            ])
            dep_avails = self.env['availability.availability'].search([
                ('property_id', '=', property_id),
                ('avail_date', '=', departure)
            ])

            if reduce is True:
                if state == 'confirm':
                    for record in rt_avails:
                        record.ravail_occupancy -= rooms
                    for avail in avails:
                        avail.avail_occupancy -= rooms
                        if avail.avail_date == arrival:
                            avail.avail_arrival -= rooms
                    for depavail in dep_avails:
                        if depavail.avail_date == departure:
                            depavail.avail_dep -= rooms
                    state = status
                elif state == 'reservation':
                    for record in rt_avails:
                        record.ravail_unconfirm -= rooms
                    for avail in avails:
                        avail.avail_unconfirm -= rooms
                    state = status
                elif state == 'booking':
                    for record in rt_avails:
                        record.ravail_booking = record.ravail_booking - rooms
                    for avail in avails:
                        avail.avail_booking = avail.avail_booking - rooms
                    state = status
                    

            if state == 'confirm':
                for record in rt_avails:
                    record.ravail_occupancy += rooms
                for avail in avails:
                    avail.avail_occupancy += rooms
                    if avail.avail_date == arrival:
                        avail.avail_arrival += rooms
                for depavail in dep_avails:
                    if depavail.avail_date == departure:
                        depavail.avail_dep += rooms
            elif state == 'reservation':
                for record in rt_avails:
                    record.ravail_unconfirm += rooms
                for avail in avails:
                    avail.avail_unconfirm += rooms
            elif state == 'booking':
                for record in rt_avails:
                    record.ravail_booking = record.ravail_booking + rooms
                for avail in avails:
                    avail.avail_booking = avail.avail_booking + rooms

        # if roomtype.code[0] == 'H' :
        #     for rsvn in self:
        #         rsvn_state = reservation_id.state
        #         rsvn.write({'state' : rsvn_state})


    @api.model
    def _no_show_reservation(self):
        no_show_rsvn_lines = self.env['hms.reservation.line'].search([('arrival', '<', datetime.today()),('state', '=','confirm')])
        for no_show_rsvn_line in no_show_rsvn_lines:
            no_show_rsvn_line.update({'is_no_show': True})


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
    reservation_line_id = fields.Many2one('hms.reservation.line',
                                          string="Reservation Details")
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

# Room Reservation Summary
class RoomReservationSummary(models.Model):
    _name = 'room.reservation.summary'
    _description = 'Room reservation summary'

    property_id = fields.Many2one(
        'property.property',
        string="Property",
        default=lambda self: self.env.user.property_id.id)
    name = fields.Char('Reservation Summary',
                       default='Reservations Summary',
                       invisible=True)
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    summary_header = fields.Text('Summary Header')
    room_summary = fields.Text('Room Summary')

    @api.model
    def default_get(self, fields):
        """
        To get default values for the object.
        @param self: The object pointer.
        @param fields: List of fields for which we want default values
        @return: A dictionary which of fields with values.
        """
        if self._context is None:
            self._context = {}
        res = super(RoomReservationSummary, self).default_get(fields)
        # Added default datetime as today and date to as today + 30.
        from_dt = datetime.today()
        dt_from = from_dt.strftime(dt)
        to_dt = from_dt + relativedelta(days=30)
        dt_to = to_dt.strftime(dt)
        res.update({'date_from': dt_from, 'date_to': dt_to})

        if not self.date_from and self.date_to:
            date_today = datetime.datetime.today()
            first_day = datetime.datetime(date_today.year, date_today.month, 1,
                                          0, 0, 0)
            first_temp_day = first_day + relativedelta(months=1)
            last_temp_day = first_temp_day - relativedelta(days=1)
            last_day = datetime.datetime(last_temp_day.year,
                                         last_temp_day.month,
                                         last_temp_day.day, 23, 59, 59)
            date_froms = first_day.strftime(dt)
            date_ends = last_day.strftime(dt)
            res.update({'date_from': date_froms, 'date_to': date_ends})
        return res

    def room_reservation(self):
        '''
        @param self: object pointer
        '''
        mod_obj = self.env['ir.model.data']
        if self._context is None:
            self._context = {}
        model_data_ids = mod_obj.search([('model', '=', 'ir.ui.view'),
                                         ('name', '=', 'reservation_view_form')
                                         ])
        resource_id = model_data_ids.read(fields=['res_id'])[0]['res_id']
        return {
            'name': _('Reconcile Write-Off'),
            'context': self._context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hms.reservation',
            'views': [(resource_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.onchange('property_id', 'date_from', 'date_to')
    def get_room_summary(self):
        '''
        @param self: object pointer
         '''
        res = {}
        all_detail = []
        room_obj = self.env['property.room'].search([
            ('property_id', '=', self.property_id.id),
            ('roomtype_id.code', '!=', 'HFO')
        ])
        reservation_line_obj = self.env['hms.reservation.line'].search([
            ('property_id', '=', self.property_id.id)
        ])
        # folio_room_line_obj = self.env['folio.room.line']
        # user_obj = self.env['res.users']
        date_range_list = []
        main_header = []
        summary_header_list = ['Rooms']
        if self.date_from and self.date_to:
            if self.date_from > self.date_to:
                raise UserError(
                    _('Please Check Time period Date From can\'t \
                                   be greater than Date To !'))
            if self._context.get('tz', False):
                timezone = pytz.timezone(self._context.get('tz', False))
            else:
                timezone = pytz.timezone('UTC')
                dt_from = self.date_from.strftime(dt)
                dt_to = self.date_to.strftime(dt)
                d_frm_obj = datetime.strptime(dt_from, dt)\
                    .replace(tzinfo=pytz.timezone('UTC')).astimezone(timezone)
                d_to_obj = datetime.strptime(dt_to, dt)\
                    .replace(tzinfo=pytz.timezone('UTC')).astimezone(timezone)
                temp_date = d_frm_obj
                while (temp_date <= d_to_obj):
                    val = ''
                    val = (str(temp_date.strftime("%a")) + ' ' +
                        str(temp_date.strftime("%b")) + ' ' +
                        str(temp_date.strftime("%d")))
                    summary_header_list.append(val)
                    date_range_list.append(temp_date.strftime(dt))
                    temp_date = temp_date + timedelta(days=1)
                all_detail.append(summary_header_list)
                room_ids = room_obj
                all_room_detail = []
                for room in room_ids:
                    room_detail = {}
                    room_list_stats = []
                    room_detail.update({'name': room.room_no or ''})
                    for reservation_line in reservation_line_obj:
                        if room != reservation_line.room_no:
                            for chk_date in date_range_list:
                                room_list_stats.append({
                                    'state': 'Free',
                                    'date': chk_date,
                                    'room_id': room.id
                                })
                        if room == reservation_line.room_no and reservation_line.state == 'reservation':
                            for chk_date in date_range_list:
                                ch_dt = chk_date[:10] + '23:59:59'
                                ttime = datetime.strptime(ch_dt, dt)
                                c = ttime.replace(tzinfo=timezone).\
                                    astimezone(pytz.timezone('UTC'))
                                chk_date = c.strftime(dt)
                                arrival = reservation_line.arrival.strftime(dt)
                                departure = reservation_line.departure.strftime(dt)
                                if chk_date >= arrival and chk_date <= departure:
                                    room_list_stats.append({
                                        'state': 'Reserved',
                                        'date': chk_date,
                                        'room_id': room.id,
                                        'is_draft': 'No',
                                        'data_model': '',
                                        'data_id': 0
                                    })
                                else:
                                    room_list_stats.append({
                                        'state': 'Free',
                                        'date': chk_date,
                                        'room_id': room.id
                                    })

                room_detail.update({'value': room_list_stats})
                all_room_detail.append(room_detail)
            main_header.append({'header': summary_header_list})
            self.summary_header = str(main_header)
            self.room_summary = str(all_room_detail)
        return res

# QuickRoom Reservation
class QuickRoomReservation(models.TransientModel):
    _name = 'quick.room.reservation'
    _description = 'Quick Room Reservation'

    check_in = fields.Datetime('Check In', required=True)
    check_out = fields.Datetime('Check Out', required=True)
    rooms = fields.Integer('Rooms', required=True)
    # roomtype_id = fields.Many2one('room.type', 'Room Type', required=True)
    # room_id = fields.Many2one('property.room', 'Room', required=True)
    property_id = fields.Many2one('property.property', 'Hotel', required=True)
    # adults = fields.Integer('Adults', size=64)

    @api.onchange('check_out', 'check_in')
    def on_change_check_out(self):
        '''
        When you change checkout or checkin it will check whether
        Checkout date should be greater than Checkin date
        and update dummy field
        -----------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        '''
        if self.check_out and self.check_in:
            if self.check_out < self.check_in:
                raise ValidationError(
                    _('Checkout date should be greater \
                                         than Checkin date.'))

    @api.model
    def default_get(self, fields):
        """
        To get default values for the object.
        @param self: The object pointer.
        @param fields: List of fields for which we want default values
        @return: A dictionary which of fields with values.
        """
        if self._context is None:
            self._context = {}
        res = super(QuickRoomReservation, self).default_get(fields)
        if self._context:
            keys = self._context.keys()
            if 'date' in keys:
                res.update({'check_in': self._context['date']})
            if 'rooms' in keys:
                room = self._context['rooms']
                res.update({'rooms': int(room)})
        return res

    def room_reserve(self):
        """
        This method create a new record for hotel.reservation
        -----------------------------------------------------
        @param self: The object pointer
        @return: new record set for hotel reservation.
        """
        hotel_res_obj = self.env['hms.reservation']
        for res in self:
            rec = (hotel_res_obj.create({
                'arrival': res.check_in,
                'departure': res.check_out,
                'property_id': res.property_id.id,
                'rooms': res.rooms,
            }))
        return rec    


class OverBooking(models.Model):
    _name = "over.booking"
    _description = "Over Booking"

    reservation_line_id = fields.Many2one("hms.reservation.line", store=True)
    rt_avail_id = fields.Many2one('roomtype.available',
                                  string="Room Type Available")
    property_id = fields.Many2one("property.property", 'Property')
    overbook_date = fields.Date(string="Date")
    overbook_rooms = fields.Integer(string="Rooms")
