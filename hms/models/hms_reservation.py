import base64
import logging
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules import get_module_resource
from odoo.tools import *
from datetime import datetime, date, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as dt
import pytz
import calendar
from odoo.tools.misc import formatLang, format_date, get_lang


class HMSReason(models.Model):
    _name = "hms.reason"
    _description = "Reason"

    is_csv = fields.Boolean(default=False)
    name = fields.Char(string="Name", required=True, help='Name')
    code = fields.Char(string="Code", required=True, help='Code')
    type_id = fields.Many2one('hms.reasontype',
                              string="Reason Type",
                              required=True,
                              help='Reason Type')


class HMSReasonType(models.Model):
    _name = "hms.reasontype"
    _description = "Reason Type"

    is_csv = fields.Boolean(default=False)
    name = fields.Char(string="Name", required=True, help='Name')
    code = fields.Char(string="Code", size=3, required=True, help='Code')
    reason_ids = fields.One2many('hms.reason',
                                 'type_id',
                                 string="Reason",
                                 required=True,
                                 help='Reason')


# Department
class Department(models.Model):
    _name = "hms.department"
    _description = "Department"

    name = fields.Char(string="Department Name",
                       required=True,
                       help='Department Name')


# Special Request
class SpecialRequest(models.Model):
    _name = "hms.special.request"
    _description = "Special Request"

    reservationline_id = fields.Many2one('hms.reservation.line',
                                         string="Reservation Line",
                                         help='Reservation Line')
    department_id = fields.Char("Department", help='Department')
    date = fields.Date("Date", help='Date')
    name = fields.Char("Name", help='Name')


# Reservation
class Reservation(models.Model):
    _name = 'hms.reservation'
    _description = "Reservation"
    _order = 'confirm_no desc'
    _inherit = ['mail.thread']

    is_no_show = fields.Boolean(default=False, string="No Show")
    sequence = fields.Integer(default=1)
    color = fields.Integer(string='Color Index',
                           compute="set_kanban_color",
                           help='Colour Index')
    active = fields.Boolean('Active', default=True, track_visibility=True)
    is_dummy = fields.Boolean(string="Dummy Room?",
                              default=False,
                              readonly=True)
    dummy_readonly = fields.Boolean(default=False)
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
    property_ids = fields.Many2many('hms.property',
                                    related="user_id.property_id")
    property_id = fields.Many2one('hms.property',
                                  string="Property",
                                  domain="[('id', '=?', property_ids)]",
                                  help='Property')
    user_id = fields.Many2one('res.users',
                              string='Salesperson',
                              default=lambda self: self.env.uid,
                              help='Salesperson')
    date_order = fields.Datetime('Date Ordered',
                                 readonly=True,
                                 required=True,
                                 index=True,
                                 default=(lambda *a: time.strftime(dt)),
                                 help='Date Ordered')
    type = fields.Selection(string='Type',
                            selection=[('individual', 'Individual'),
                                       ('group', 'Group')],
                            compute='_compute_type',
                            inverse='_write_type',
                            track_visibility=True,
                            help='Type')
    is_company = fields.Boolean(string='Is a Company', default=False)
    is_group = fields.Boolean(string="Is a Group", default=False)
    company_id = fields.Many2one(
        'res.partner',
        string="Company",
        domain="['&',('profile_no','!=',''),('is_company','=',True)]",
        help='Comapany')
    group_id = fields.Many2one('res.partner',
                               string="Group",
                               domain="[('is_group','=',True)]",
                               help='Group')
    guest_id = fields.Many2one('res.partner',
                               string="Guest",
                               domain="[('is_guest','=',True)]",
                               help='Guest')
    roomtype_id = fields.Many2one('hms.roomtype', default=1)
    arrival = fields.Date(string="Arrival Date",
                          default=datetime.today(),
                          required=True,
                          help='Arrival Date')
    departure = fields.Date(
        string="Departure Date",
        default=lambda *a:
        (datetime.now() + timedelta(days=(1))).strftime('%Y-%m-%d'),
        required=True,
        help='Departure Date')
    nights = fields.Integer(string="Nights", help='Nights')
    rooms = fields.Integer(string="Number of Rooms",
                           default=1,
                           required=True,
                           help='Number of Rooms')
    market_ids = fields.Many2many('hms.marketsegment',
                                  related="property_id.market_ids")
    market = fields.Many2one('hms.marketsegment',
                             string="Market",
                             domain="[('id', '=?', market_ids)]",
                             required=True,
                             help='Market')
    source = fields.Many2one('hms.marketsource',
                             string="Market Source",
                             required=True,
                             help='Market Source')
    sales_id = fields.Many2one('res.users',
                               string="Sales",
                               default=lambda self: self.env.uid,
                               help='Sales')
    contact_id = fields.Many2one(
        'res.partner',
        domain=
        "[('company_type', '=','person'),('is_guest','!=',True),('is_group','!=',True),('is_company','!=',True)]",
        string="Contact",
        help='Contact')
    reservation_type = fields.Many2one('hms.rsvntype',
                                       string="Reservation Type",
                                       readonly=True,
                                       default=2,
                                       store=True,
                                       help='Reservation Type')
    reservation_status = fields.Many2one(
        'hms.rsvnstatus',
        string="Reservation Status",
        domain="[('rsvntype_id', '=', reservation_type)]",
        required=True,
        store=True,
        help='Reservation Language')
    arrival_flight = fields.Char(string="Arrival Flight",
                                 size=10,
                                 help='Arrival Flight')
    arrival_flighttime = fields.Float(string="AR-Flight Time",
                                      help='Arrival Flight Time')
    dep_flight = fields.Char(string="Departure Flight",
                             help='Departure Flight')
    dep_flighttime = fields.Float(string="DEP-Flight Time",
                                  help='Departure Flight Time')
    eta = fields.Float(string="ETA", help="ETA")
    etd = fields.Float(string="ETD", help="ETD")
    reservation_line_ids = fields.One2many(
        'hms.reservation.line',
        'reservation_id',
        string="Reservation Line",
        track_visibility=True,
        readonly=False,
        states={'cancel': [('readonly', True)]})
    confirm_no = fields.Char(string="Confirm Number",
                             readonly=True,
                             help='Confirm Number')
    reason_id = fields.Many2one('hms.reason',
                                string="Reason",
                                domain="[('type_id.code', '=', 'CXL')]",
                                help='Reason')
    internal_notes = fields.Text(string="Internal Notes",
                                 help='Internal Notes')

    #Fields for statinfo
    rsvn_room_count = fields.Integer(string="Reservation",
                                     compute='_compute_rsvn_rooms')
    confirm_room_count = fields.Integer(string="Confirm",
                                        compute='_compute_confirm_rooms')
    cancel_room_count = fields.Integer(string="Canceled",
                                       compute='_compute_cancel_rooms')
    checkin_room_count = fields.Integer(string="Check-in",
                                        compute='_compute_checkin_rooms')

    @api.onchange('property_ids')
    def default_get_property_id(self):
        if self.property_ids:
            if len(self.property_ids) >= 1:
                self.property_id = self.property_ids[0]._origin.id
        else:
            return {
                'warning': {
                    'title':
                    _('No Property Permission'),
                    'message':
                    _("Select Property in User Setting or you can't create reservation"
                      )
                }
            }

    def name_get(self):
        result = []
        for record in self:
            if record.is_group is False:
                if record.company_id:
                    if record.guest_id:
                        result.append(
                            (record.id,
                             "{} ({})".format(record.company_id.name,
                                              record.guest_id.name)))
                    else:
                        result.append(
                            (record.id, "{}".format(record.company_id.name)))
                else:
                    result.append(
                        (record.id, "{}".format(record.guest_id.name)))
            else:
                if record.group_id:
                    result.append(
                        (record.id,
                         "{} ({})".format(record.company_id.name,
                                          record.group_id.group_name)))
                else:
                    result.append(
                        (record.id, "{}".format(record.company_id.name)))
        return result

    def _compute_rsvn_rooms(self):
        hfo_reservation = self.env['hms.reservation.line'].search([
            ('reservation_id', '=', self.id), ('room_type.code', '=', 'HFO')
        ])
        no_hfo_reservation = list(
            set(self.reservation_line_ids) - set(hfo_reservation))
        tmp = 0
        for record in no_hfo_reservation:
            if record.state == 'reservation':
                tmp = tmp + record.rooms
        self.rsvn_room_count = tmp

    def _compute_confirm_rooms(self):
        hfo_reservation = self.env['hms.reservation.line'].search([
            ('reservation_id', '=', self.id), ('room_type.code', '=', 'HFO')
        ])
        no_hfo_reservation = list(
            set(self.reservation_line_ids) - set(hfo_reservation))
        tmp = 0
        for record in no_hfo_reservation:
            if record.state == 'confirm':
                tmp = tmp + record.rooms
        self.confirm_room_count = tmp

    def _compute_cancel_rooms(self):
        hfo_reservation = self.env['hms.reservation.line'].search([
            ('reservation_id', '=', self.id), ('room_type.code', '=', 'HFO')
        ])
        no_hfo_reservation = list(
            set(self.reservation_line_ids) - set(hfo_reservation))
        tmp = 0
        for record in no_hfo_reservation:
            if record.is_cancel is True and record.state == 'cancel':
                tmp = tmp + record.rooms
        self.cancel_room_count = tmp

    def _compute_checkin_rooms(self):
        hfo_reservation = self.env['hms.reservation.line'].search([
            ('reservation_id', '=', self.id), ('room_type.code', '=', 'HFO')
        ])
        no_hfo_reservation = list(
            set(self.reservation_line_ids) - set(hfo_reservation))
        tmp = 0
        for record in no_hfo_reservation:
            if record.state == 'checkin':
                tmp = tmp + record.rooms
        self.checkin_room_count = tmp

    def action_rsvn_room_count(self):
        reservation_lines = self.reservation_line_ids.filtered(
            lambda x: x.state == "reservation" and x.room_type.code[0] != 'H')
        action = self.env.ref('hms.reservation_line_action_window').read()[0]
        if len(reservation_lines) > 1:
            action['domain'] = [('id', 'in', reservation_lines.ids)]
        elif len(reservation_lines) == 1:
            form_view = [(self.env.ref('hms.reservation_line_view_form').id,
                          'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = reservation_lines.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_type': 'out_reservation_line',
        }
        return action

    def action_confirm_room_count(self):
        reservation_lines = self.reservation_line_ids.filtered(
            lambda x: x.state == "confirm" and x.room_type.code[0] != 'H')
        action = self.env.ref('hms.reservation_line_action_window').read()[0]
        if len(reservation_lines) > 1:
            action['domain'] = [('id', 'in', reservation_lines.ids)]
        elif len(reservation_lines) == 1:
            form_view = [(self.env.ref('hms.reservation_line_view_form').id,
                          'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = reservation_lines.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_type': 'out_reservation_line',
        }
        return action

    def action_cancel_room_count(self):
        reservation_lines = self.reservation_line_ids.filtered(
            lambda x: x.state == "cancel" and x.room_type.code[0] != 'H')
        action = self.env.ref('hms.reservation_line_action_window').read()[0]
        if len(reservation_lines) > 1:
            action['domain'] = [('id', 'in', reservation_lines.ids)]
        elif len(reservation_lines) == 1:
            form_view = [(self.env.ref('hms.reservation_line_view_form').id,
                          'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = reservation_lines.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_type': 'out_reservation_line',
        }
        return action

    def action_checkin_room_count(self):
        reservation_lines = self.reservation_line_ids.filtered(
            lambda x: x.state == "checkin" and x.room_type.code[0] != 'H')
        action = self.env.ref('hms.reservation_line_action_window').read()[0]
        if len(reservation_lines) > 1:
            action['domain'] = [('id', 'in', reservation_lines.ids)]
        elif len(reservation_lines) == 1:
            form_view = [(self.env.ref('hms.reservation_line_view_form').id,
                          'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = reservation_lines.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_type': 'out_reservation_line',
        }
        return action

    def set_kanban_color(self):
        for record in self:
            color = 0
            if record.state == 'booking':
                color = 3
            elif record.state == 'reservation':
                color = 11
            elif record.state == 'confirm':
                color = 4
            elif record.state == 'checkin':
                color = 10
            elif record.state == 'cancel':
                color = 1
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
        for rec in self:
            arrival_date = rec.arrival
            if datetime.strptime(str(arrival_date), DEFAULT_SERVER_DATE_FORMAT
                                 ).date() == datetime.now().date():
                rec.is_arrival_today = True
            else:
                rec.is_arrival_today = False

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
            rec._state_update_forecast(state, property_id, arrival, departure,
                                       room_type, rooms, reduce, status)
            rec.write({'state': status})

    def checkin_status(self):
        for rec in self:
            flag = 0
            if rec.reservation_line_ids:
                for r in rec.reservation_line_ids:
                    if r.state == 'confirm' and r.is_arrival_today is True and r.guest_id and r.nationality_id and r.rooms == 1 and r.room_type and r.room_no and r.pax >= 1 and r.ratehead_id and r.ratecode_id:
                        citime = datetime.strptime(str(datetime.now()),
                                                   "%Y-%m-%d %H:%M:%S.%f")
                        r.write({
                            'state': 'checkin',
                            'citime': citime,
                        })
                        rec.write({'state': 'checkin'})
                    else:
                        flag += 1
                # Update HFO room state to checkin
                hfo_room = self.env['hms.reservation.line'].search([
                    ('reservation_id', '=', rec.id),
                    ('room_type', '=ilike', 'H%')
                ])
                if hfo_room and rec.state == 'checkin':
                    hfo_room.write({'state': 'checkin'})
                if flag > 0:
                    text = """Sorry! Rooms with Missing Required Information Cannot Check-In. You must fill the required information first."""
                    # query = 'delete from hms.checkin_message_wizard'
                    # self.env.cr.execute(query)
                    value = self.env['hms.checkin_message_wizard'].sudo(
                    ).create({'text': text})
                    return {
                        'type': 'ir.actions.act_window',
                        'name': 'Message',
                        'res_model': 'hms.checkin_message_wizard',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'target': 'new',
                        'res_id': value.id
                    }

    @api.onchange('reservation_type')
    def onchange_state(self):
        for rec in self:
            rsvntype = rec.reservation_type
            if rsvntype and rsvntype == 'Confirmed':
                rec.state = 'confirm'

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
        for rec in self:
            arrivaldate = rec.arrival
            no_of_night = rec.nights
            if arrivaldate and no_of_night:
                rec.departure = arrivaldate + timedelta(days=no_of_night)

    # Change Departure Date
    @api.onchange('nights')
    def onchange_dep_date(self):
        for rec in self:
            arrivaldate = rec.arrival
            no_of_night = rec.nights
            if arrivaldate and no_of_night:
                rec.departure = arrivaldate + timedelta(days=no_of_night)

    # Change Room Nights
    @api.onchange('departure')
    def onchange_nights(self):
        for rec in self:
            d1 = datetime.strptime(str(rec.arrival), '%Y-%m-%d')
            d2 = datetime.strptime(str(rec.departure), '%Y-%m-%d')
            d3 = d2 - d1
            days = str(d3.days)
            rec.nights = int(days)

    # Create HFO Room
    def create_hfo_room(self, state, reservation_id, confirm_no, property_id,
                        company_id, group_id, guest_id, roomtype_id, arrival,
                        departure, nights, market, source, reservation_type,
                        reservation_status, arrival_flight, arrival_flighttime,
                        dep_flight, dep_flighttime, eta, etd):

        vals = []
        total_hfo_room = self.env['hms.property.room'].search([
            ('property_id', '=', property_id),
            ('roomtype_id.code', '=ilike', 'H%')
        ]).ids
        occ_hfo_room = self.env['hms.reservation.line'].search([
            ('property_id', '=', property_id),
            ('room_type.code', '=ilike', 'H%'),
        ]).room_no.ids
        avail_room = list(set(total_hfo_room) - set(occ_hfo_room))
        room_no = 0
        if avail_room:
            room_no = avail_room[0]

        vals.append((0, 0, {
            'state': state,
            'reservation_id': reservation_id.id,
            'confirm_no': confirm_no,
            'property_id': property_id,
            'company_id': company_id,
            'group_id': group_id,
            'guest_id': guest_id,
            'room_type': roomtype_id,
            'room_no': room_no,
            'arrival': arrival,
            'departure': departure,
            'nights': nights,
            'rooms': 1,
            'market': market,
            'source': source,
            'reservation_type': reservation_type,
            'reservation_status': reservation_status,
            'arrival_flight': arrival_flight,
            'arrival_flighttime': arrival_flighttime,
            'dep_flight': dep_flight,
            'dep_flighttime': dep_flighttime,
            'eta': eta,
            'etd': etd,
        }))
        reservation_id.update({
            'reservation_line_ids': vals,
            'dummy_readonly': True
        })

    #Create Function
    @api.model
    def create(self, values):
        property_id = values.get('property_id')
        property_id = self.env['hms.property'].search([('id', '=', property_id)
                                                       ])
        if property_id:
            if property_id.confirm_id_format:
                format_ids = self.env['hms.format.detail'].search(
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
            if res.is_dummy is True:
                res.create_hfo_room(
                    res.state, res, res.confirm_no, res.property_id.id,
                    res.company_id.id, res.group_id.id, res.guest_id.id,
                    res.roomtype_id.id, res.arrival, res.departure, res.nights,
                    res.market.id, res.source.id, res.reservation_type.id,
                    res.reservation_status.id, res.arrival_flight,
                    res.arrival_flighttime, res.dep_flight, res.dep_flighttime,
                    res.eta, res.etd)

        return res

    # Write Function
    def write(self, values):
        res = super(Reservation, self).write(values)
        dummy = values.get('is_dummy')
        if 'is_dummy' in values.keys():
            if dummy is True:
                self.create_hfo_room(
                    self.state, self, self.confirm_no, self.property_id.id,
                    self.company_id.id, self.group_id.id, self.guest_id.id,
                    self.roomtype_id.id, self.arrival, self.departure,
                    self.nights, self.market.id, self.source.id,
                    self.reservation_type.id, self.reservation_status.id,
                    self.arrival_flight, self.arrival_flighttime,
                    self.dep_flight, self.dep_flighttime, self.eta, self.etd)

        return res

    # Unlink Function
    def unlink(self):

        reservation_line_objs = self.env['hms.reservation.line']
        for record in self:
            reservation_line_objs += self.env['hms.reservation.line'].search([
                ('reservation_id', '=', record.id)
            ])
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

    def action_confirm_letter_send(self):
        """ Open a window to compose an email, with the confirm letter template
            message loaded by default
        """
        self.ensure_one()
        template = self.env.ref('hms.confirm_letter_template', raise_if_not_found=False)
        # lang = get_lang(self.env)
        # if template and template.lang:
        #     lang = template._render_template(template.lang, 'hms.reservation', self.id)
        # else:
        #     lang = lang.code
        compose_form = self.env.ref('hms.confirm_letter_wizard_form', raise_if_not_found=False)
        ctx = {
            'default_model':'hms.reservation',
            'default_res_id':self.id,
            'default_use_template':bool(template),
            'default_template_id':template.id,
            'default_composition_mode':'comment',
            # 'mark_invoice_as_sent':True,
            # 'custom_layout':"mail.mail_notification_paynow",
            # 'model_description':self.with_context(lang=lang).type_name,
            'force_email':True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hms.confirm_letter',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

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

    is_cancel = fields.Boolean(string="Cancel", default=False, readonly=True)
    is_no_show = fields.Boolean(string="No Show", default=False, readonly=True)
    is_roomtype_fix = fields.Boolean(string="Fixed Type?",
                                     readonly=False,
                                     related="room_type.fix_type")
    sequence = fields.Integer(default=1)
    required_color = fields.Char(
        string=" ",
        compute="_compute_required_color",
        help=
        """- Red Color: If you do not choose Rate Code, Showing Red Color.This is the High Priority.
        - Orange Color: If you do not fill up Room No, Guest Name, Nationality, Showing Orange Color.This is the Medium Priority.
        - Green Color: This state will tell you are already fill basic information that you Check in.
        Note: You need to fill up full information when you get more information Eg. Travel Information etc..."""
    )
    color = fields.Integer(string='Color Index',
                           compute="set_kanban_color",
                           help='Colour Index')
    ispartial = fields.Boolean('Partial', default=True)
    active = fields.Boolean('Active', default=True, track_visibility=True)
    cancel_rsvn_ids = fields.One2many('hms.cancel.rsvn',
                                      'reservation_line_id',
                                      string="Cancel Reservation",
                                      help='Cancel Reservation')
    company_id = fields.Many2one(
        'res.partner',
        string="Company",
        domain="['&',('profile_no','!=',''),('is_company','=',True)]",
        related='reservation_id.company_id',
        help='Company')
    group_id = fields.Many2one('res.partner',
                               string="Group",
                               domain="[('is_group','=',True)]",
                               related='reservation_id.group_id',
                               help='Group')
    guest_id = fields.Many2one('res.partner',
                               string="Guest Name",
                               domain="[('is_guest','=',True)]",
                               help="GuestName")
    nationality_id = fields.Many2one('hms.nationality',
                                     string="Guest Nationality")
    is_arrival_today = fields.Boolean(string="Is Arrival Today",
                                      compute='_compute_is_arrival_today')
    reservation_id = fields.Many2one('hms.reservation',
                                     string="Reservation",
                                     help='Resrevation')
    property_id = fields.Many2one('hms.property',
                                  string="Property",
                                  readonly=True,
                                  related='reservation_id.property_id',
                                  store=True,
                                  help='Property')
    confirm_no = fields.Char(string="Confirm No.",
                             readonly=True,
                             related='reservation_id.confirm_no',
                             help='Confirm No.')
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
    market_ids = fields.Many2many('hms.marketsegment',
                                  related="property_id.market_ids")
    market = fields.Many2one('hms.marketsegment',
                             string="Market",
                             domain="[('id', '=?', market_ids)]",
                             help='Market')
    source = fields.Many2one('hms.marketsource',
                             string="Source",
                             help='Source')
    reservation_type = fields.Many2one('hms.rsvntype',
                                       "Reservation Type",
                                       default=get_rsvn_type,
                                       readonly=True,
                                       store=True,
                                       help='Reseravtion Type')
    reservation_status = fields.Many2one(
        'hms.rsvnstatus',
        "Reservation Status",
        domain="[('rsvntype_id', '=', reservation_type)]",
        default=get_rsvn_status,
        store=True,
        help='Reservation Status')
    arrival_flight = fields.Char("Arrival Flight", help='Arrival Flight')
    arrival_flighttime = fields.Float("AR_Flight Time",
                                      help='Arival Flight Time')
    dep_flight = fields.Char("Departure Flight", help='Departure Flight')
    dep_flighttime = fields.Float("DEP_Flight Time",
                                  help='Departure Flight Time')
    eta = fields.Float("ETA", help='ETA')
    etd = fields.Float("ETD", help='ETD')

    room_no = fields.Many2one('hms.property.room',
                              string="Room No",
                              help='Room No')
    roomtype_ids = fields.Many2many('hms.roomtype',
                                    related="property_id.roomtype_ids")
    room_type = fields.Many2one(
        'hms.roomtype',
        string="Room Type",
        domain="[('id', '=?', roomtype_ids),('id','!=',1)]",
        delegate=True,
        ondelete='cascade',
        index=True,
        help='Room Type')
    bedtype_ids = fields.Many2many('hms.bedtype', related="room_type.bed_type")
    bedtype_id = fields.Many2one('hms.bedtype',
                                 domain="[('id', '=?', bedtype_ids)]",
                                 help='Bed Type')
    system_date = fields.Date("System Date",
                              related="property_id.system_date",
                              help='System Date')
    arrival = fields.Date("Arrival",
                          default=get_arrival,
                          readonly=False,
                          required=True,
                          store=True,
                          track_visibility=True,
                          help='Arrival')
    departure = fields.Date("Departure",
                            default=get_departure,
                            readonly=False,
                            required=True,
                            store=True,
                            track_visibility=True,
                            help='Departure')
    nights = fields.Integer(string="Nights", default=get_nights, help='Nights')
    rooms = fields.Integer("Rooms", help='Rooms')
    avail_room_ids = fields.Many2many('hms.property.room',
                                      string="Room Nos",
                                      compute='get_avail_room_ids',
                                      help='Room Nos')
    pax = fields.Integer("Pax", default=1, help='Pax')
    child = fields.Integer("Child", help='Child')
    ratehead_id = fields.Many2one(
        'hms.ratecode.header',
        string="Rate Code",
        domain=
        "[('property_id', '=', property_id),('start_date', '<=', arrival), ('end_date', '>=', departure)]"
    )
    # ratecode_ids = fields.One2many(
    #     'hms.ratecode.details',
    #     'ratehead_id',
    #     readonly=True,
    #     domain=
    #     "[('ratehead_id', '=?', ratehead_id),('roomtype_id', '=?', room_type),'|','&',('start_date','<=',arrival),('end_date', '>=', arrival),'&',('start_date','<=',departure),('end_date', '>=', departure)]"
    # )
    ratecode_ids = fields.One2many('hms.ratecode.details',
                                   related='ratehead_id.ratecode_details')
    ratecode_id = fields.Many2one(
        'hms.ratecode.details',
        domain=
        "[('ratehead_id', '=?', ratehead_id),('roomtype_id', '=?', room_type),'|','&',('start_date','<=',arrival),('end_date', '>=', arrival),'&',('start_date','<=',departure),('end_date', '>=', departure)]"
    )
    room_rate = fields.Float("Room Rate",
                             compute='_compute_room_rate',
                             help="Included Rate")
    updown_amt = fields.Float("Updown Amount", help='Updown Amount')
    updown_pc = fields.Float("Updown PC", help='Updown Percentage')
    reason_id = fields.Many2one('hms.reason',
                                string="Reason",
                                domain="[('type_id', '=', 1)]",
                                help='Reason')
    discount_reason_id = fields.Many2one('hms.reason',
                                         string="Discount Reason",
                                         domain="[('type_id', '=', 2)]",
                                         help='Discount Reason')
    package_id = fields.Many2one('hms.package.group',
                                 related="ratehead_id.pkg_group_id",
                                 string="Package",
                                 help='Package')
    additional_pkg_ids = fields.Many2many(
        'hms.package.header',
        string="Additional Pkg",
        domain=
        "[('property_id', '=?', property_id),('is_sell_separate', '=', True)]",
        help='Additional Package')
    allotment_id = fields.Char(string="Allotment", help='Allotment')
    rate_nett = fields.Float(string="Rate Nett",
                             help="Rate Nett",
                             compute="_compute_rate_nett")
    fo_remark = fields.Char(string="F.O Remark", help='F.O Remark')
    hk_remark = fields.Char(string="H.K Remark", help='H.K Remark')
    cashier_remark = fields.Char(string="Cashier Remark",
                                 help='Cashier Remark')
    general_remark = fields.Char(string="General Remark",
                                 help='General Reamrk')
    specialrequest_id = fields.One2many('hms.special.request',
                                        'reservationline_id',
                                        string="Special Request",
                                        help='Special Request')
    reservation_user_id = fields.Many2one('res.users',
                                          string="User",
                                          related='reservation_id.user_id',
                                          help='User')
    madeondate = fields.Datetime("Date",
                                 related='reservation_id.date_order',
                                 help='Date')
    citime = fields.Datetime("Check-In Time", help='Check-In Time')
    cotime = fields.Datetime("Check-Out Time", help='Check-Out Time')

    extrabed = fields.Integer("Extra Bed", help="No. of Extra Bed")
    extrabed_amount = fields.Float("Extra Bed Amount",
                                   help="Extra Bed Amount",
                                   related="ratecode_id.extra_bed")
    child_bfpax = fields.Integer("Child BF-Pax", help="Child BF Pax")
    child_bf = fields.Float("Child Breakfast",
                            help="Child BF Amount",
                            related="ratecode_id.child_bf")
    extra_addon = fields.Float("Extra Addon", help="Extra Amount")

    pickup = fields.Datetime("Pick Up Time", help='Pick Up Time')
    dropoff = fields.Datetime("Drop Off Time", help='Drop Off Time')
    arrival_trp = fields.Char("Arrive Transport", help='Arrive Transport')
    arrival_from = fields.Char("Arrive From", help='Arrive From')
    departure_trp = fields.Char("Departure Transport",
                                help='Departure Transport')
    departure_from = fields.Char("Departure From", help='Departure From')
    visa_type = fields.Char("Visa Type", help='Visa Type')
    visa_issue = fields.Date("Visa Issue Date", help='Visa Issue Date')
    visa_expire = fields.Date("Visa Expired Date", help='Visa Expired Date')
    arrive_reason_id = fields.Char("Arrive Reason", help='Arrive Reason')
    room_transaction_line_ids = fields.One2many(
        'hms.room.transaction.charge.line',
        'reservation_line_id',
        "Charges",
        help='Charges')

    # def action_confirm_letter(self):
    #     """ Open a window to compose an email, with the confirm letter template
    #         message loaded by default
    #     """
    #     self.ensure_one()
    #     template = self.env.ref('hms.confirm_letter_template', raise_if_not_found=False)
    #     lang = get_lang(self.env)
    #     if template and template.lang:
    #         lang = template._render_template(template.lang, 'account.move', self.id)
    #     else:
    #         lang = lang.code
    #     compose_form = self.env.ref('account.account_invoice_send_wizard_form', raise_if_not_found=False)
    #     ctx = dict(
    #         default_model='account.move',
    #         default_res_id=self.id,
    #         default_use_template=bool(template),
    #         default_template_id=template and template.id or False,
    #         default_composition_mode='comment',
    #         mark_invoice_as_sent=True,
    #         custom_layout="mail.mail_notification_paynow",
    #         model_description=self.with_context(lang=lang).type_name,
    #         force_email=True
    #     )
    #     return {
    #         'name': _('Send Invoice'),
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'account.invoice.send',
    #         'views': [(compose_form.id, 'form')],
    #         'view_id': compose_form.id,
    #         'target': 'new',
    #         'context': ctx,
    #     }

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} - {}".format(record.room_type.name,
                                                       record.rooms)))
        return result

    # Compute Room Rate based on Pax
    def _check_rate(self, check_date, pax, rate, property_id):
        check_day = datetime.strptime(
            str(check_date), '%Y-%m-%d').weekday()  # get 'day' of arrival date
        temp = (calendar.day_name[check_day])  # get 'day' of arrival date
        weekend_days = self.env['hms.weekend'].search([('property_id', '=',
                                                        property_id)])
        # Get objs for special days based on property_id
        special_day_objs = self.env['hms.specialday'].search([
            ('property_id', '=', property_id)
        ])
        is_weekend = False
        if weekend_days:
            for weekend in weekend_days:
                if temp == 'Monday':
                    if weekend.monday is True:
                        is_weekend = True
                elif temp == 'Tuesday':
                    if weekend.tuesday is True:
                        is_weekend = True
                elif temp == 'Wednesday':
                    if weekend.wednesday is True:
                        is_weekend = True
                elif temp == 'Thursday':
                    if weekend.thursday is True:
                        is_weekend = True
                elif temp == 'Friday':
                    if weekend.friday is True:
                        is_weekend = True
                elif temp == 'Saturday':
                    if weekend.saturday is True:
                        is_weekend = True
                elif temp == 'Sunday':
                    if weekend.sunday is True:
                        is_weekend = True
                else:
                    is_weekend = False

        is_special_day = False
        for special_day in special_day_objs:
            if check_date == special_day.special_date:
                is_special_day = True
        if is_special_day is True and rate.special_price1 > 0.0:
            if pax == 1:
                room_rate = rate.special_price1
            elif pax == 2:
                room_rate = rate.special_price1 + rate.special_price2
            elif pax == 3:
                room_rate = rate.special_price1 + rate.special_price2 + rate.special_price3
            elif pax == 4:
                room_rate = rate.special_price1 + rate.special_price2 + rate.special_price3 + rate.special_price4
            else:
                x = pax - 4
                room_rate = rate.special_price1 + rate.special_price2 + rate.special_price3 + rate.special_price4 + (
                    rate.special_extra * x)
        elif is_weekend is True and rate.weekend_price1 > 0.0:
            if pax == 1:
                room_rate = rate.weekend_price1
            elif pax == 2:
                room_rate = rate.weekend_price1 + rate.weekend_price2
            elif pax == 3:
                room_rate = rate.weekend_price1 + rate.weekend_price2 + rate.weekend_price3
            elif pax == 4:
                room_rate = rate.weekend_price1 + rate.weekend_price2 + rate.weekend_price3 + rate.weekend_price4
            else:
                x = pax - 4
                room_rate = rate.weekend_price1 + rate.weekend_price2 + rate.weekend_price3 + rate.weekend_price4 + (
                    rate.weekend_extra * x)
        else:
            if pax == 1:
                room_rate = rate.normal_price1
            elif pax == 2:
                room_rate = rate.normal_price1 + rate.normal_price2
            elif pax == 3:
                room_rate = rate.normal_price1 + rate.normal_price2 + rate.normal_price3
            elif pax == 4:
                room_rate = rate.normal_price1 + rate.normal_price2 + rate.normal_price3 + rate.normal_price4
            else:
                x = pax - 4
                room_rate = rate.normal_price1 + rate.normal_price2 + rate.normal_price3 + rate.normal_price4 + (
                    rate.normal_extra * x)
        return room_rate

    # Compute Room Rate based on Pax
    @api.depends('ratecode_id')
    def _compute_room_rate(self):
        for rec in self:
            rec.room_rate = rec._check_rate(rec.arrival, rec.pax,
                                            rec.ratecode_id,
                                            rec.property_id.id)

    # Compute Rate Nett
    @api.depends('package_id')
    def _compute_rate_nett(self):
        for rec in self:
            rate = 0.0
            total_amount = 0.0
            for pkg in rec.package_id.package_ids:
                if pkg.rate_attribute == 'ARS' or pkg.rate_attribute == 'ARC':
                    rate = rec.rate_calculate(pkg, rec)
                    total_amount += rec.total_amount_calculate(rate, pkg, rec)
            rec.rate_nett = rec.room_rate + total_amount

    # Get default rate code based on ratehead_id
    @api.onchange('ratehead_id')
    def onchange_ratecode_id(self):
        for rec in self:
            if rec.ratehead_id:
                for r in rec.ratehead_id.ratecode_details:
                    if (rec.arrival >=
                            r.start_date) and (rec.arrival <= r.end_date) and (
                                rec.room_type._origin.id in r.roomtype_id.ids):
                        rec.ratecode_id = r
            else:
                rec.ratecode_id = False

    # Clear ratecode details when roomtye change
    @api.onchange('room_type')
    def onchange_ratecode_details(self):
        for rec in self:
            if rec.ratecode_id:
                rec.ratecode_id = False

    # Get Guest's Nationality from Contact
    @api.onchange('guest_id')
    def onchange_guest_nationality(self):
        for rec in self:
            if rec.guest_id:
                if rec.guest_id.nationality_id:
                    rec.nationality_id = rec.guest_id.nationality_id
                else:
                    rec.nationality_id = False

    # For Cancel Check-In Button
    def action_cancel_checkin(self):
        self.write({'state': 'confirm'})
        count = 0
        for rec in self:
            for record in rec.reservation_id.reservation_line_ids:
                if record.state == 'checkin':
                    if record.room_type.code[0] != 'H':
                        count += 1
            if count == 0:
                rec.reservation_id.write({'state': 'confirm'})
                hfo_reservation = self.env['hms.reservation.line'].search([
                    ('reservation_id', '=', rec.reservation_id.id),
                    ('room_type', '=ilike', 'H%')
                ])
                if hfo_reservation:
                    hfo_reservation.write({'state': 'confirm'})

    def set_kanban_color(self):
        for record in self:
            color = 0
            if record.state == 'booking':
                color = 3
            elif record.state == 'reservation':
                color = 11
            elif record.state == 'confirm':
                color = 4
            elif record.state == 'checkin':
                color = 10
            elif record.state == 'cancel':
                color = 1
            record.color = color

    def _compute_required_color(self):
        color_attribute = self.env['hms.color.attribute'].search([
            ('name', '=', 'Reservation')
        ])
        value_ids = color_attribute.value_ids
        high_color = " "
        medium_color = " "
        complete_color = " "
        for value in value_ids:
            if value.name == "High":
                high_color = value.html_color
            elif value.name == "Medium":
                medium_color = value.html_color
            elif value.name == "Complete":
                complete_color = value.html_color

        for record in self:
            room_no = self.env['hms.property.room']
            guest_name = self.env['res.partner']
            ratehead_id = self.env['hms.ratecode.header']
            nationality_id = self.env['hms.nationality']
            if (record.room_type.code != 'HFO'):
                if (record.ratehead_id == ratehead_id):
                    record.required_color = high_color
                elif (record.room_no == room_no
                      or record.guest_id == guest_name
                      or record.nationality_id == nationality_id):
                    record.required_color = medium_color
                else:
                    record.required_color = complete_color
            else:
                record.required_color = complete_color

    def _compute_is_arrival_today(self):
        for rec in self:
            arrival_date = rec.arrival
            if datetime.strptime(str(arrival_date), DEFAULT_SERVER_DATE_FORMAT
                                 ).date() == datetime.now().date():
                rec.is_arrival_today = True
            else:
                rec.is_arrival_today = False

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
        return self.write({'color': 2})

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
        for rec in self:
            arrivaldate = rec.arrival
            no_of_night = rec.nights
            if arrivaldate and no_of_night:
                rec.departure = arrivaldate + timedelta(days=no_of_night)

    # Change Departure Date
    @api.onchange('nights')
    def onchange_dep_date(self):
        for rec in self:
            arrivaldate = rec.arrival
            no_of_night = rec.nights
            if arrivaldate and no_of_night:
                rec.departure = arrivaldate + timedelta(days=no_of_night)

    # Change Room Nights
    @api.onchange('departure')
    def onchange_nights(self):
        for rec in self:
            d1 = datetime.strptime(str(rec.arrival), '%Y-%m-%d')
            d2 = datetime.strptime(str(rec.departure), '%Y-%m-%d')
            d3 = d2 - d1
            days = str(d3.days)
            rec.nights = int(days)

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

    # For Details Button in Cancel Record
    def action_show_cancel_record(self):
        view = self.env.ref('hms.line_cancel_view_form')
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

    @api.depends('room_no', 'property_id', 'arrival', 'departure', 'room_type',
                 'bedtype_id')
    def get_avail_room_ids(self):
        for rec in self:
            room_type = rec.room_type._origin.id
            room_type_obj = self.env['hms.roomtype'].search([('id', '=',
                                                              room_type)])

            bedtype_id = rec.bedtype_id._origin.id

            avail_rooms = []
            if room_type_obj.fix_type == True:

                total_room_per_roomtype = self.env['hms.property.room'].search(
                    [('property_id', '=', rec.property_id.id),
                     ('roomtype_id', '=', room_type)]).ids

                occ_room_per_roomtype = self.env[
                    'hms.reservation.line'].search([
                        ('id', '!=', rec._origin.id),
                        ('property_id', '=', rec.property_id.id),
                        ('room_type', '=', room_type),
                        ('arrival', '<', rec.departure),
                        ('departure', '>', rec.arrival)
                    ]).room_no.ids

                avail_rooms = list(
                    set(total_room_per_roomtype) - set(occ_room_per_roomtype))

                current_rooms = self.reservation_id.reservation_line_ids.filtered(
                    lambda r: r.room_type.id == rec.room_type.id and r.arrival
                    < rec.departure and r.departure > rec.arrival).room_no.ids

                avail_rooms = list(set(avail_rooms) - set(current_rooms))
                # rec.avail_room_ids = avail_rooms

            elif room_type_obj.fix_type == False:

                if bedtype_id:

                    total_room_per_roomtype = self.env[
                        'hms.property.room'].search([
                            ('property_id', '=', rec.property_id.id),
                            ('roomtype_id', '=', room_type),
                            ('bedtype_id', '=', bedtype_id),
                        ]).ids

                    occ_room_per_roomtype = self.env[
                        'hms.reservation.line'].search([
                            ('property_id', '=', rec.property_id.id),
                            ('room_type', '=', room_type),
                            ('bedtype_id', '=', bedtype_id),
                            ('arrival', '<', rec.departure),
                            ('departure', '>', rec.arrival)
                        ]).room_no.ids

                    avail_rooms = list(
                        set(total_room_per_roomtype) -
                        set(occ_room_per_roomtype))

                    current_rooms = self.reservation_id.reservation_line_ids.filtered(
                        lambda x: x.room_type.id == rec.room_type.id and x.
                        arrival < rec.departure and x.departure > rec.arrival
                        and x.bedtype_id.id == rec.bedtype_id.id).room_no.ids

                    avail_rooms = list(set(avail_rooms) - set(current_rooms))

                    if len(avail_rooms) == 0:

                        total_room_per_roomtype = self.env[
                            'hms.property.room'].search([
                                ('property_id', '=', rec.property_id.id),
                                ('roomtype_id', '=', room_type),
                                ('zip_type', '=', True),
                            ]).ids

                        occ_room_per_roomtype = self.env[
                            'hms.reservation.line'].search([
                                ('property_id', '=', rec.property_id.id),
                                ('room_type', '=', room_type),
                                ('arrival', '<', rec.departure),
                                ('departure', '>', rec.arrival),
                            ]).room_no.ids

                        avail_rooms = list(
                            set(total_room_per_roomtype) -
                            set(occ_room_per_roomtype))

                        current_rooms = self.reservation_id.reservation_line_ids.filtered(
                            lambda x: x.room_type.id == rec.room_type.id and x.
                            arrival < rec.departure and x.departure > rec.
                            arrival and x.bedtype_id == rec.bedtype_id.id
                        ).room_no.ids

                        avail_rooms = list(
                            set(avail_rooms) - set(current_rooms))

            rec.avail_room_ids = avail_rooms

    @api.constrains('id', 'rooms')
    def _change_update_rooms(self):
        for rec in self:
            line_rooms_total = 0
            for record in rec.reservation_id.reservation_line_ids:
                if record.room_type.code[0] != "H":
                    line_rooms_total = line_rooms_total + record.rooms
            if self.reservation_id.rooms != line_rooms_total:
                self.reservation_id.rooms = line_rooms_total

    @api.constrains('arrival', 'departure')
    def _update_arrival_departure(self):
        tmp_arrival_date = date(9999, 1, 11)
        tmp_departure_date = date(1000, 1, 11)
        for rec in self.reservation_id.reservation_line_ids:
            if rec.room_type.code[0] != 'H':
                if rec.arrival < tmp_arrival_date:
                    tmp_arrival_date = rec.arrival
                if rec.departure > tmp_departure_date:
                    tmp_departure_date = rec.departure

        d1 = datetime.strptime(str(tmp_arrival_date), '%Y-%m-%d')
        d2 = datetime.strptime(str(tmp_departure_date), '%Y-%m-%d')
        d3 = d2 - d1
        days = str(d3.days)
        if tmp_arrival_date != date(
                9999, 1, 11) and tmp_departure_date != date(1000, 1, 11):
            self.reservation_id.write({
                'arrival': tmp_arrival_date,
                'departure': tmp_departure_date,
                'nights': int(days)
            })

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
                    if total_rooms and t_rooms and total_rooms > t_rooms:
                        rec.rooms = total_rooms - t_rooms
                    else:
                        rec.rooms = 1
                return

            room_type = rec.room_type._origin.id
            rt_avails = self.env['hms.roomtype.available'].search([
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
        # return {
        #     'name':_('Copy'),
        #     'view_type':'form',
        #     'view_mode':'form',
        #     'view_id':self.env.ref('hms.property_room_view_form').id,
        #     'res_model':'hms.property.room',
        #     'context':"{'type':'out_propertyroom'}",
        #     'type': 'ir.actions.client',
        #     'tag': 'reload',
        #     'target':'new',
        # }
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    # Create Transaction Charge Lines
    def create_charge_line(self, property_id, transaction_id,
                           reservation_line_id, rate, total_amount, active,
                           package_id, transaction_date, total_room, delete,
                           rate_attribute):
        currency = reservation_line_id.ratecode_id.currency_id
        vals = []
        vals.append((0, 0, {
            'property_id': property_id.id,
            'transaction_id': transaction_id.id,
            'reservation_line_id': reservation_line_id.id,
            'rate': rate,
            'total_amount': total_amount,
            'active': active,
            'package_id': package_id.id,
            'transaction_date': transaction_date,
            'total_room': total_room,
            'delete': delete,
            'rate_attribute': rate_attribute,
            'ref': 'AUTO',
            'currency_id': currency.id,
        }))
        reservation_line_id.update({'room_transaction_line_ids': vals})

    # Update Transaction Charge Lines
    def update_charge_line(self, room_transaction_line_id, transaction_id,
                           rate, total_amount, active, package_id,
                           transaction_date, total_room, delete,
                           rate_attribute):
        room_transaction_line_id.update({
            'transaction_id': transaction_id.id,
            'rate': rate,
            'total_amount': total_amount,
            'active': active,
            'package_id': package_id.id,
            'transaction_date': transaction_date,
            'total_room': total_room,
            'delete': delete,
            'rate_attribute': rate_attribute,
            'ref': 'AUTO',
        })

    def get_posting_date(self, reservation_line_id, pkg):
        posting_dates = []
        res = reservation_line_id
        day_count = 0
        last_night = res.departure - timedelta(days=1)
        if pkg.posting_rythms == '1':
            for date in range(res.nights):
                post_dates = res.arrival + timedelta(days=day_count)
                posting_dates.append(post_dates)
                day_count += 1
        elif pkg.posting_rythms == '2':
            posting_dates.append(res.arrival)
        elif pkg.posting_rythms == '3':
            posting_dates.append(last_night)
        elif pkg.posting_rythms == '4':
            for date in range(res.nights):
                post_dates = res.arrival + timedelta(days=day_count)
                if post_dates != res.arrival:
                    posting_dates.append(post_dates)
                day_count += 1
        elif pkg.posting_rythms == '5':
            for date in range(res.nights):
                post_dates = res.arrival + timedelta(days=day_count)
                if last_night != post_dates:
                    posting_dates.append(post_dates)
                day_count += 1
        elif pkg.posting_rythms == '6':
            for date in range(res.nights):
                post_dates = res.arrival + timedelta(days=day_count)
                if post_dates != res.arrival and post_dates != last_night:
                    posting_dates.append(post_dates)
                day_count += 1
        return posting_dates

    def create_line_with_posting_rhythm(self, reservation_line_id,
                                        transaction_date, package_ids):
        res = reservation_line_id
        check_pkg = ''
        for pkg in package_ids:
            if pkg.rate_attribute != 'INR':
                check_pkg = pkg.rate_attribute
                posted_dates = res.get_posting_date(res, pkg)
                if transaction_date in posted_dates:
                    rate = res.rate_calculate(pkg, res)
                    total_amount = res.total_amount_calculate(rate, pkg, res)
                    if total_amount == 0.0 and rate > 0.0:
                        res.create_charge_line(res.property_id,
                                               pkg.transaction_id, res, rate,
                                               total_amount, False, pkg,
                                               transaction_date, res.rooms,
                                               False, pkg.rate_attribute)
                    else:
                        res.create_charge_line(res.property_id,
                                               pkg.transaction_id, res, rate,
                                               total_amount, True, pkg,
                                               transaction_date, res.rooms,
                                               False, pkg.rate_attribute)
        # For Room Charge Transaction
        if check_pkg != 'SS':
            pkg = self.env['hms.package.header']
            # Pass room rate from ratecode details based on transaction date
            ratecode_detail_obj = self.env['hms.ratecode.details'].search([
                ('property_id', '=', res.property_id.id),
                ('ratehead_id', '=', res.ratehead_id.id),
                ('start_date', '<=', transaction_date),
                ('end_date', '>=', transaction_date),
                ('roomtype_id', 'in', res.room_type.id)
            ])
            if ratecode_detail_obj and len(ratecode_detail_obj) == 1:
                temp_rate = res._check_rate(transaction_date, res.pax,
                                            ratecode_detail_obj,
                                            res.property_id.id)
            else:
                temp_rate = 0.0

            room_rate = temp_rate
            room_amount = temp_rate * res.rooms
            res.create_charge_line(res.property_id,
                                   res.ratecode_id.transaction_id, res,
                                   room_rate, room_amount, True, pkg,
                                   transaction_date, res.rooms, False, 'INR')

    def update_line_with_posting_rhythm(self, reservation_line_id, delete):
        res = reservation_line_id
        day_count = 0
        for rec in range(res.nights):
            transaction_date = res.arrival + timedelta(days=day_count)
            if res.package_id:
                total_amount_include = 0.0
                total_room_rate = 0.0
                room_transaction_line_objs = self.env[
                    'hms.room.transaction.charge.line'].search([
                        ('property_id', '=', res.property_id.id),
                        ('reservation_line_id', '=', res.id),
                        ('transaction_date', '=', transaction_date),
                        ('rate_attribute', '!=', 'SS'),
                        ('delete', '=', delete), '|', ('active', '=', True),
                        ('active', '=', False)
                    ])
                if room_transaction_line_objs:
                    for r in room_transaction_line_objs:
                        for pkg in res.package_id.package_ids:
                            if pkg.rate_attribute != 'INR':
                                posted_dates = res.get_posting_date(res, pkg)
                                if transaction_date in posted_dates:
                                    rate = res.rate_calculate(pkg, res)
                                    total_amount = res.total_amount_calculate(
                                        rate, pkg, res)
                                    if r.package_id.id == pkg.id and r.transaction_id.id == pkg.transaction_id.id:
                                        if total_amount == 0.0 and rate > 0.0:
                                            res.update_charge_line(
                                                r, pkg.transaction_id, rate,
                                                total_amount, False, pkg,
                                                transaction_date, res.rooms,
                                                False, pkg.rate_attribute)
                                        else:
                                            res.update_charge_line(
                                                r, pkg.transaction_id, rate,
                                                total_amount, True, pkg,
                                                transaction_date, res.rooms,
                                                False, pkg.rate_attribute)
                                    else:
                                        if not r.package_id:
                                            pkg = self.env[
                                                'hms.package.header']
                                            # Pass room rate from ratecode details based on transaction date
                                            ratecode_detail_obj = self.env[
                                                'hms.ratecode.details'].search(
                                                    [('property_id', '=',
                                                      res.property_id.id),
                                                     ('ratehead_id', '=',
                                                      res.ratehead_id.id),
                                                     ('start_date', '<=',
                                                      transaction_date),
                                                     ('end_date', '>=',
                                                      transaction_date),
                                                     ('roomtype_id', 'in',
                                                      res.room_type.id)])
                                            if ratecode_detail_obj and len(
                                                    ratecode_detail_obj) == 1:
                                                temp_rate = res._check_rate(
                                                    transaction_date, res.pax,
                                                    ratecode_detail_obj,
                                                    res.property_id.id)
                                            else:
                                                temp_rate = 0.0

                                            room_rate = temp_rate
                                            room_amount = temp_rate * res.rooms
                                            res.update_charge_line(
                                                r,
                                                res.ratecode_id.transaction_id,
                                                room_rate, room_amount, True,
                                                pkg, transaction_date,
                                                res.rooms, False, 'INR')
                else:
                    res.create_line_with_posting_rhythm(
                        res, transaction_date, res.package_id.package_ids)

            day_count += 1

    def update_additional_packages(self, reservation_line_id, delete, pkg):
        res = reservation_line_id
        day_count = 0
        for rec in range(res.nights):
            transaction_date = res.arrival + timedelta(days=day_count)
            if res.additional_pkg_ids:
                room_transaction_line_objs = self.env[
                    'hms.room.transaction.charge.line'].search([
                        ('property_id', '=', res.property_id.id),
                        ('reservation_line_id', '=', res.id),
                        ('transaction_date', '=', transaction_date),
                        ('rate_attribute', '=', 'SS'),
                        ('package_id', '=', pkg.id), ('delete', '=', delete),
                        '|', ('active', '=', True), ('active', '=', False)
                    ])
                if room_transaction_line_objs:
                    for r in room_transaction_line_objs:
                        posted_dates = res.get_posting_date(res, pkg)
                        if transaction_date in posted_dates:
                            rate = res.rate_calculate(pkg, res)
                            total_amount = res.total_amount_calculate(
                                rate, pkg, res)
                            if r.transaction_id.id == pkg.transaction_id.id:
                                if total_amount == 0.0 and rate > 0.0:
                                    res.update_charge_line(
                                        r, pkg.transaction_id, rate,
                                        total_amount, False, pkg,
                                        transaction_date, res.rooms, False,
                                        pkg.rate_attribute)
                                else:
                                    res.update_charge_line(
                                        r, pkg.transaction_id, rate,
                                        total_amount, True, pkg,
                                        transaction_date, res.rooms, False,
                                        pkg.rate_attribute)

                else:
                    res.create_line_with_posting_rhythm(
                        res, transaction_date, pkg)

            day_count += 1

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
        self._state_update_forecast(state, property_id, arrival, departure,
                                    room_type, rooms, reduce, status)
        # Room Transaction Charge Line Create
        day_count = 0
        for rec in range(res.nights):
            transaction_date = res.arrival + timedelta(days=day_count)
            if res.package_id:
                res.create_line_with_posting_rhythm(res, transaction_date,
                                                    res.package_id.package_ids)
            # Check for additional packages
            if res.additional_pkg_ids:
                # Create charge line for additional packages
                res.create_line_with_posting_rhythm(res, transaction_date,
                                                    res.additional_pkg_ids)
            day_count += 1
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
                    'reservation', 'confirm', 'checkin'
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
            newroom_type = self.env['hms.roomtype'].search([('id', '=',
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
            self._state_update_forecast(self.state, property_id.id, arrival,
                                        departure, old_room_type.id, rooms,
                                        True, status)

            # Check & Retreive for New Availability
            rt_avails = self.env['hms.roomtype.available']
            avails = self.env['hms.availability']
            dep_avails = self.env['hms.availability']
            # Check & Retreive for New Availability
            if new_arrival or new_departure or new_nights:
                if newroom_type:
                    rt_avails = self.env['hms.roomtype.available'].search([
                        ('property_id', '=', property_id.id),
                        ('ravail_date', '>=', new_arrival),
                        ('ravail_date', '<', new_departure),
                        ('ravail_rmty', '=', newroom_type.id)
                    ])
                else:
                    rt_avails = self.env['hms.roomtype.available'].search([
                        ('property_id', '=', property_id.id),
                        ('ravail_date', '>=', new_arrival),
                        ('ravail_date', '<', new_departure),
                        ('ravail_rmty', '=', old_room_type.id)
                    ])
                avails = self.env['hms.availability'].search([
                    ('property_id', '=', property_id.id),
                    ('avail_date', '>=', new_arrival),
                    ('avail_date', '<', new_departure)
                ])
                dep_avails = self.env['hms.availability'].search([
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
                    rt_avails = self.env['hms.roomtype.available'].search([
                        ('property_id', '=', property_id.id),
                        ('ravail_date', '>=', arrival),
                        ('ravail_date', '<', departure),
                        ('ravail_rmty', '=', newroom_type.id)
                    ])
                else:
                    rt_avails = self.env['hms.roomtype.available'].search([
                        ('property_id', '=', property_id.id),
                        ('ravail_date', '>=', arrival),
                        ('ravail_date', '<', departure),
                        ('ravail_rmty', '=', old_room_type.id)
                    ])
                avails = self.env['hms.availability'].search([
                    ('property_id', '=', property_id.id),
                    ('avail_date', '>=', arrival),
                    ('avail_date', '<', departure)
                ])
                dep_avails = self.env['hms.availability'].search([
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

        if 'ratehead_id' in values.keys() or 'ratecode_id' in values.keys(
        ) or 'package_id' in values.keys(
        ) or 'additional_pkg_ids' in values.keys() or 'rooms' in values.keys(
        ) or 'arrival' in values.keys() or 'departure' in values.keys(
        ) or 'room_type' in values.keys() or 'nights' in values.keys(
        ) or 'pax' in values.keys() or 'child' in values.keys(
        ) or 'extrabed' in values.keys() or 'child_bfpax' in values.keys():
            # If No Records >>> Create Room Transaction Charge Lines
            if not self.room_transaction_line_ids:
                day_count = 0
                for rec in range(self.nights):
                    transaction_date = self.arrival + timedelta(days=day_count)
                    if self.package_id:
                        self.create_line_with_posting_rhythm(
                            self, transaction_date,
                            self.package_id.package_ids)
                    if self.additional_pkg_ids:
                        # Create charge line for additional packages
                        self.create_line_with_posting_rhythm(
                            self, transaction_date, self.additional_pkg_ids)
                    day_count += 1

            # If Records >>> Update Room Transaction Charge Lines
            else:
                # Date & Nights Changes
                if arrival != self.arrival or departure != self.departure or nights != self.nights:
                    del_room_transaction_line_objs = self.env[
                        'hms.room.transaction.charge.line'].search([
                            ('property_id', '=', self.property_id.id),
                            ('reservation_line_id', '=', self.id), '|',
                            ('active', '=', True), ('active', '=', False)
                        ])
                    for r in del_room_transaction_line_objs:
                        r.update({
                            'active': False,
                            'delete': True,
                        })
                    self.update_line_with_posting_rhythm(self, True)
                    for pkg in self.additional_pkg_ids:
                        self.update_additional_packages(self, True, pkg)

                # No Date & Nights Changes (only other fields changes)
                else:
                    self.update_line_with_posting_rhythm(self, False)
                    # For additional packages
                    del_room_transaction_line_objs = self.env[
                        'hms.room.transaction.charge.line'].search([
                            ('property_id', '=', self.property_id.id),
                            ('reservation_line_id', '=', self.id),
                            ('rate_attribute', '=', 'SS'), '|',
                            ('active', '=', True), ('active', '=', False)
                        ])
                    for r in del_room_transaction_line_objs:
                        r.update({
                            'active': False,
                            'delete': True,
                        })
                    for pkg in self.additional_pkg_ids:
                        self.update_additional_packages(self, True, pkg)
        return res

    # Unlink Function
    def unlink(self):

        room_transaction_line_objs = self.env[
            'hms.room.transaction.charge.line']
        for record in self:
            state = record.state
            rooms = record.rooms
            room_type = record.room_type.id
            property_id = record.property_id.id
            arrival = record.arrival
            departure = record.departure
            reduce = True
            status = 'HFO'
            record._state_update_forecast(state, property_id, arrival,
                                          departure, room_type, rooms, reduce,
                                          status)

            record.reservation_id.rooms = record.reservation_id.rooms - record.rooms
            room_transaction_line_objs += self.env[
                'hms.room.transaction.charge.line'].search([
                    ('reservation_line_id', '=', record.id), '|',
                    ('active', '=', True), ('active', '=', False)
                ])
        room_transaction_line_objs.unlink()
        res = super(ReservationLine, self).unlink()
        return res

    # State Update Forecast
    def _state_update_forecast(self, state, property_id, arrival, departure,
                               room_type, rooms, reduce, status):

        roomtype = self.env['hms.roomtype'].search([('id', '=', room_type)])

        if roomtype.code[0] != 'H':
            rt_avails = self.env['hms.roomtype.available'].search([
                ('property_id', '=', property_id),
                ('ravail_date', '>=', arrival), ('ravail_date', '<',
                                                 departure),
                ('ravail_rmty', '=', room_type)
            ])
            avails = self.env['hms.availability'].search([
                ('property_id', '=', property_id),
                ('avail_date', '>=', arrival), ('avail_date', '<', departure)
            ])
            dep_avails = self.env['hms.availability'].search([
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

    # Scheduled Update No Show Reservation Daily
    @api.model
    def _no_show_reservation(self):
        no_show_rsvn_lines = self.env['hms.reservation.line'].search([
            ('arrival', '<', datetime.today()), ('state', '=', 'confirm')
        ])
        for no_show_rsvn_line in no_show_rsvn_lines:
            no_show_rsvn_line.update({'is_no_show': True})

    def rate_calculate(self, package_id, reservation_line_id):
        rate = 0.0
        if package_id.reservation_fields_id:
            if package_id.reservation_fields_id.code == 'BF':
                rate = reservation_line_id.ratecode_id.adult_bf
            elif package_id.reservation_fields_id.code == 'EB':
                rate = reservation_line_id.ratecode_id.extra_bed
            elif package_id.reservation_fields_id.code == 'CBF':
                rate = reservation_line_id.ratecode_id.child_bf
        else:
            rate = package_id.Fix_price
        return rate

    def total_amount_calculate(self, rate, package_id, reservation_line_id):
        total_amount = 0.0
        if package_id.Calculation_method == 'FIX':
            total_amount = rate * reservation_line_id.rooms
        elif package_id.Calculation_method == 'PA':
            total_amount = rate * reservation_line_id.pax * reservation_line_id.rooms
        elif package_id.Calculation_method == 'PC':
            total_amount = rate * reservation_line_id.child * reservation_line_id.rooms
        elif package_id.Calculation_method == 'CBP':
            total_amount = rate * reservation_line_id.child_bfpax * reservation_line_id.rooms
        elif package_id.Calculation_method == 'NEB':
            total_amount = rate * reservation_line_id.extrabed * reservation_line_id.rooms
        return total_amount

    @api.model
    def _remove_reservation_daily(self):
        out_date_rsvn_lines = self.env['hms.reservation.line'].search([
            ('arrival', '<', datetime.today()), ('active', '=', True), '|',
            ('state', '=', 'booking'), ('state', '=', 'reservation')
        ])
        for rsvn_line in out_date_rsvn_lines:
            rsvn_line.update({'active': False})

        out_date_reservations = self.env['hms.reservation'].search([
            ('arrival', '<', datetime.today())
        ])
        for rsvn in out_date_reservations:
            rsvn.update({'active': False})

    @api.onchange('room_type')
    def clear_bed_type(self):
        bedtype = self.env['hms.bedtype']
        if self.room_type.fix_type is True:
            self.bedtype_id = bedtype


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
                               domain="[('company_type', '=','person')]",
                               help='Sales')
    contact_id = fields.Many2one('res.partner',
                                 domain="[('company_type', '=','person')]",
                                 string="Contact",
                                 help='Contact')
    internal_notes = fields.Text(string="Internal Notes",
                                 help='Internal Notes')
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
        'hms.property',
        string="Property",
        default=lambda self: self.env.user.property_id.id,
        help='Property')
    user_id = fields.Many2one('res.users',
                              string='Salesperson',
                              default=lambda self: self.env.user.id,
                              help='Salesperson')
    date_order = fields.Datetime('Date Ordered',
                                 readonly=True,
                                 index=True,
                                 default=(lambda *a: time.strftime(dt)),
                                 help='Date Ordered')
    company_id = fields.Many2one(
        'res.partner',
        string="Company",
        domain="['&',('profile_no','!=',''),('is_company','=',True)]",
        help='Company')
    group_id = fields.Many2one('res.partner',
                               string="Group",
                               domain="[('is_group','=',True)]",
                               help='Group')
    guest_id = fields.Many2one('res.partner',
                               string="Guest",
                               domain="[('is_guest','=',True)]",
                               help='Guest')
    arrival = fields.Date(string="Arrival Date",
                          default=datetime.today(),
                          help='Arrival Date')
    departure = fields.Date(
        string="Departure Date",
        default=lambda *a:
        (datetime.now() + timedelta(days=(1))).strftime('%Y-%m-%d'),
        help='Departure Date')
    nights = fields.Integer(string="Nights", help='Nights')
    no_ofrooms = fields.Integer(string="Number of Rooms",
                                help='Number of Rooms')
    market = fields.Many2one('hms.marketsegment',
                             string="Market",
                             domain="[('id', '=?', market_ids)]",
                             help='Market')
    source = fields.Many2one('hms.marketsource',
                             string="Market Source",
                             help='Market Source')
    reservation_type = fields.Many2one('hms.rsvntype',
                                       string="Reservation Type",
                                       default=2,
                                       help='Reservation Type')
    reservation_status = fields.Many2one('hms.rsvnstatus',
                                         string="Reservation Status",
                                         help='Reservation Status')
    arrival_flight = fields.Char(string="Arrival Flight",
                                 size=10,
                                 help='Arrival Flight')
    arrival_flighttime = fields.Float(string="AR-Flight Time",
                                      help='Arrival Flight Time')
    dep_flight = fields.Char(string="Departure Flight",
                             help='Departure Flight')
    dep_flighttime = fields.Float(string="DEP-Flight Time",
                                  help='Departure Flight Time')
    eta = fields.Float(string="ETA", help='ETA')
    etd = fields.Float(string="ETD", help='ETD')
    reason_id = fields.Many2one('hms.reason', string="Reason", help='Reason')
    reservation_line_id = fields.Many2one('hms.reservation.line',
                                          string="Reservation Details",
                                          help='Reservation Details')
    confirm_no = fields.Char(string="Confirm Number",
                             readonly=True,
                             help='Confirm No')

    # Fields from Reservation Line
    reservation_id = fields.Many2one('hms.reservation',
                                     string="Reservation",
                                     help='Reseravtion')
    room_no = fields.Many2one('hms.property.room',
                              string="Room No",
                              help='Room No')
    room_type = fields.Many2one('hms.roomtype',
                                string="Room Type",
                                domain="[('id', '=?', roomtype_ids)]",
                                help='Room Type')
    pax = fields.Integer("Pax", default=1, help='Pax')
    child = fields.Integer("Child", help='Child')
    ratehead_id = fields.Many2one(
        'hms.ratecode.header',
        domain=
        "[('property_id', '=', property_id),('start_date', '<=', arrival), ('end_date', '>=', departure)]"
    )
    ratecode_id = fields.Many2one(
        'hms.ratecode.details',
        domain=
        "[('ratehead_id', '=?', ratehead_id),('roomtype_id', '=?', room_type)]"
    )
    room_rate = fields.Float("Room Rate",
                             compute='_compute_room_rate',
                             help='Room Rate')
    updown_amt = fields.Float("Updown Amount", help='Updown Amount')
    updown_pc = fields.Float("Updown PC", help='Updown Percentage')
    package_id = fields.Many2one(
        'hms.package.group',
        related="ratecode_id.ratehead_id.pkg_group_id",
        string="Package")
    additional_pkg_ids = fields.Many2many(
        'hms.package.header',
        string="Additional Pkg",
        domain=
        "[('property_id', '=?', property_id),('is_sell_separate', '=', True)]")
    allotment_id = fields.Char(string="Allotment", help='Allotment')
    rate_nett = fields.Float(string="Rate Nett", help='Rate Nett')
    fo_remark = fields.Char(string="F.O Remark", help='F.O Remark')
    hk_remark = fields.Char(string="H.K Remark", help='H.K Remark')
    cashier_remark = fields.Char(string="Cashier Remark",
                                 help='Cashier Remark')
    general_remark = fields.Char(string="General Remark",
                                 help='General Remark')
    # specialrequest_id = fields.One2many('hms.special.request',
    #                                     'reservationline_id',
    #                                     string="Special Request")
    citime = fields.Datetime("Check-In Time", help='Check-In Time')
    cotime = fields.Datetime("Check-Out Time", help='Check-Out Time')

    extrabed = fields.Integer("Extra Bed", help='Extra Bed')
    extrabed_amount = fields.Float("Number of Extra Bed",
                                   related="ratecode_id.extra_bed",
                                   help='Number of Extra Bed')
    child_bfpax = fields.Integer("Child BF-Pax", help='Child Breakfast Pax')
    child_bf = fields.Float("Child Breakfast",
                            related="ratecode_id.child_bf",
                            help='Child Breakfast')
    extra_addon = fields.Float("Extra Addon", help='Extra Addon')

    pickup = fields.Datetime("Pick Up Time", help='Pick Up Time')
    dropoff = fields.Datetime("Drop Off Time", help='Drop off Time')
    arrival_trp = fields.Char("Arrive Transport", help='Arrive Transport')
    arrival_from = fields.Char("Arrive From", help='Arrive From')
    departure_trp = fields.Char("Departure Transport",
                                help='Departure Transport')
    departure_from = fields.Char("Departure From", help='Departure From')
    visa_type = fields.Char("Visa Type", help='Visa Type')
    visa_issue = fields.Date("Visa Issue Date", help='Visa Issue Date')
    visa_expire = fields.Date("Visa Expired Date", help='Visa Expired Date')
    arrive_reason_id = fields.Char("Arrive Reason", help='Arrive Reason')

    # New Fields
    cancel_user_id = fields.Many2one('res.users',
                                     string='Salesperson',
                                     default=lambda self: self.env.user.id,
                                     help='Salesperson')
    cancel_datetime = fields.Datetime('Date Ordered',
                                      readonly=True,
                                      index=True,
                                      default=(lambda *a: time.strftime(dt)),
                                      help='Date Ordered')


# Room Reservation Summary
class RoomReservationSummary(models.Model):
    _name = 'hms.room.reservation.summary'
    _description = 'Room reservation summary'

    # property_id = fields.Many2one(
    #     'hms.property',
    #     string="Property",
    #     default=lambda self: self.env.user.property_id.id)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.uid)
    property_ids = fields.Many2many('hms.property',
                                    related="user_id.property_id")
    property_id = fields.Many2one('hms.property',
                                  string="Property",
                                  domain="[('id', '=?', property_ids)]")
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
        room_obj = self.env['hms.property.room'].search([
            ('property_id', '=', self.property_id.id),
            ('roomtype_id.code', '!=', 'HFO')
        ])
        reservation_line_obj = self.env['hms.reservation.line'].search([
            ('property_id', '=', self.property_id.id)
        ])
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
                if not room.room_reservation_line_ids:
                    for chk_date in date_range_list:
                        room_list_stats.append({
                            'state': 'Free',
                            'date': chk_date,
                            'room_id': room.id
                        })
                else:
                    for chk_date in date_range_list:
                        ch_dt = chk_date[:10] + ' 23:59:59'
                        ttime = datetime.strptime(ch_dt, dt)
                        c = ttime.replace(tzinfo=timezone).\
                            astimezone(pytz.timezone('UTC'))
                        chk_date = c.strftime(dt)
                        reserline_ids = room.room_reservation_line_ids.ids
                        reservline_ids = reservation_line_obj.search([
                            ('id', 'in', reserline_ids),
                            ('arrival', '<=', chk_date),
                            ('departure', '>', chk_date),
                            ('state', '=', 'confirm')
                        ])
                        if reservline_ids:
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


class QuickRoomReservation(models.TransientModel):
    _name = 'hms.quick.room.reservation'
    _description = 'Quick Room Reservation'

    property_id = fields.Many2one('hms.property',
                                  'Hotel',
                                  required=True,
                                  help='Hotel')
    check_in = fields.Date('Check In', required=True, help='Check In')
    check_out = fields.Date('Check Out', required=True, help='Check Out')
    rooms = fields.Integer('Rooms', required=True, help='Rooms')
    market_ids = fields.Many2many('hms.marketsegment',
                                  related="property_id.market_ids")
    market = fields.Many2one('hms.marketsegment',
                             string="Market",
                             domain="[('id', '=?', market_ids)]",
                             required=True,
                             help='Market')
    source = fields.Many2one('hms.marketsource',
                             string="Source",
                             required=True,
                             help='Source')
    # roomtype_id = fields.Many2one('hms.roomtype', 'Room Type', required=True)
    # room_id = fields.Many2one('hms.property.room', 'Room', required=True)
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
        This method create a new record for hms.reservation
        -----------------------------------------------------
        @param self: The object pointer
        @return: new record set for hotel reservation.
        """
        hotel_res_obj = self.env['hms.reservation']
        for res in self:
            rec = hotel_res_obj.create({
                'arrival': res.check_in,
                'departure': res.check_out,
                'property_id': res.property_id.id,
                'rooms': res.rooms,
                'market': res.market.id,
                'source': res.source.id,
            })
        return rec


class OverBooking(models.Model):
    _name = "hms.overbooking"
    _description = "Over Booking"

    reservation_line_id = fields.Many2one("hms.reservation.line", store=True)
    rt_avail_id = fields.Many2one('hms.roomtype.available',
                                  string="Room Type Available",
                                  help='Room Type Available')
    property_id = fields.Many2one("hms.property", 'Property', help='Property')
    overbook_date = fields.Date(string="Date", help='Date')
    overbook_rooms = fields.Integer(string="Rooms", help='Rooms')
