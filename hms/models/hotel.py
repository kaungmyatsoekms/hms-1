import base64
import logging
import pytz
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules import get_module_resource
#from odoo.tools import image_colorize, image_resize_image_big
from odoo.tools import *
from datetime import datetime, date, timedelta
_logger = logging.getLogger(__name__)
import math

_tzs = [
    (tz, tz)
    for tz in sorted(pytz.all_timezones,
                     key=lambda tz: tz if not tz.startswith('Etc/') else '_')
]


def _tz_get(self):
    return _tzs


AVAILABLE_STARS = [
    ('0', 'Low'),
    ('1', 'One Star'),
    ('2', 'Two Star'),
    ('3', 'Three Star'),
    ('4', 'Four Star'),
    ('5', 'Five Star'),
]

AVAILABLE_REV = [
    ('R', 'Room Revenue'),
    ('F', 'F&B Revenue'),
    ('M', 'Miscellaneous'),
    ('N', 'Non Revenue'),
    ('P', 'Payment'),
]

AVAILABLE_RATETYPE = [
    ('D', 'Daily'),
    ('M', 'Monthly'),
]

AVAILABLE_PAY = [
    ('CA', 'Cash'),
    ('CL', 'City Ledger'),
    ('AX', 'American Express'),
    ('DC', 'Diner Club'),
    ('MC', 'Master Card'),
    ('VS', 'Visa Card'),
    ('JC', 'JCB Card'),
    ('LC', 'Local Card'),
    ('UP', 'Union Pay Card'),
    ('OT', 'Others'),
]

AVAILABLE_PERCENTAGE = [
    ('10', '10 %'),
    ('20', '20 %'),
    ('30', '30 %'),
    ('40', '40 %'),
    ('50', '50 %'),
    ('60', '60 %'),
    ('70', '70 %'),
    ('80', '80 %'),
    ('90', '90 %'),
    ('100', '100 %'),
]


class Property(models.Model):
    _name = "hms.property"
    _inherit = ['mail.thread']
    _rec_name = "code"
    _description = "Property"

    # # Default Get Currency
    def default_get_curency(self):
        mmk_currency_id = self.env['res.currency'].search([('name', '=', 'MMK')
                                                           ])
        usd_currency_id = self.env['res.currency'].search([('name', '=', 'USD')
                                                           ])
        if mmk_currency_id.active is False:
            return usd_currency_id
        else:
            return mmk_currency_id

    # Default Get Country
    def default_get_country(self):
        country_id = None
        if self.currency_id:
            country_id = self.env['res.country'].search([
                ('currency_id', '=', self.currency_id.id)
            ])
        else:
            country_id = self.env['res.country'].search([('code', '=', "MMR")])
        return country_id

        # Default Get Building

    def default_get_building(self):
        return self.env['hms.building'].search([('building_name', '=', 'ZZZ')
                                                ]).ids

    def default_get_roomtype(self):
        return self.env['hms.roomtype'].search([('code', '=', 'HFO')]).ids

    is_property = fields.Boolean(string='Is Property',
                                 compute='_compute_is_property',
                                 help='Is Property')
    hotelgroup_id = fields.Many2one('res.company',
                                    string='Parent Company',
                                    required=True,
                                    help='Parent Company')
    company_id = fields.Many2one('res.company',
                                 string='Hotel Company',
                                 help='Hotel Company')
    active = fields.Boolean(string="Active",
                            default=True,
                            track_visibility=True)
    name = fields.Char(required=True,
                       string='Hotel Name',
                       index=True,
                       help='Hotel Name')
    code = fields.Char(string='Property ID', required=True, help="Property ID")
    address1 = fields.Char(string='Address 1', help='Address 1')
    address2 = fields.Char(string='Address 2', help='Address 2')
    township = fields.Many2one("hms.township",
                               string='Township',
                               ondelete='restrict',
                               track_visibility=True,
                               domain="[('city_id', '=?', city_id)]",
                               help='Township')
    city_id = fields.Many2one("hms.city",
                              string='City',
                              ondelete='restrict',
                              track_visibility=True,
                              domain="[('state_id', '=?', state_id)]",
                              help='City')
    state_id = fields.Many2one('res.country.state',
                               string='State',
                               help="State")
    zip = fields.Char(change_default=True)
    currency_id = fields.Many2one("res.currency",
                                  "Main Currency",
                                  related="company_id.currency_id",
                                  readonly=False,
                                  help='Currency')
    scurrency_id = fields.Many2one("res.currency",
                                   "Second Currency",
                                   related="company_id.scurrency_id",
                                   readonly=False,
                                   track_visibility=True,
                                   help='Second Currency')
    country_id = fields.Many2one('res.country',
                                 string='Country',
                                 readonly=False,
                                 requried=True,
                                 track_visibility=True,
                                 ondelete='restrict',
                                 help='Country')
    phone = fields.Char(string='Phone', help='Phone')
    fax = fields.Char(string='Fax', help='Fax')
    email = fields.Char(string='Email', help='Email')
    website = fields.Char(string='Website', help='Website')
    sociallink = fields.Char(string='Social Link', help='Social Link')
    roomqty = fields.Integer(string='Total Rooms',
                             default=0,
                             required=True,
                             help='Total Rooms')
    dummy_rooms = fields.Integer(string="Dummy Room",
                                 readonly=True,
                                 store=True,
                                 help='Dummy Room')
    property_license = fields.Char(string='Property License',
                                   help='Property License')
    rating = fields.Selection(AVAILABLE_STARS,
                              string='Rating',
                              index=True,
                              default=AVAILABLE_STARS[0][0])
    logo = fields.Binary(string='Logo',
                         attachment=True,
                         store=True,
                         help='Logo')
    image = fields.Binary(string='Image',
                          attachment=True,
                          store=True,
                          help='Image')
    timezone = fields.Selection(
        _tz_get,
        string='Timezone',
        default=lambda self: self._context.get('tz'),
        track_visibility=True,
        help=
        "The partner's timezone, used to output proper date and time values "
        "inside printed reports. It is important to set a value for this field. "
        "You should use the same timezone that is otherwise used to pick and "
        "render date and time values: your computer's timezone.")
    system_date = fields.Date(string="System Date",
                              default=date.today(),
                              track_visibility=True)
    ci_time = fields.Float(string="Check-In", help='Check-In')
    co_time = fields.Float(string="Check-Out", help='Check-Out')
    night_audit = fields.Selection([('auto', "Auto"), ('manual', "Manual")],
                                   string="Night Audit",
                                   compute='_compute_night_audit',
                                   inverse='_write_night_audit',
                                   help='Night Audit')
    is_manual = fields.Boolean(default=False)
    is_night_audit = fields.Boolean(default=False,
                                    compute="_compute_is_night_audit")

    # state for property onboarding panel
    hms_onboarding_property_state = fields.Selection(
        [('not_done', "Not done"), ('just_done', "Just done"),
         ('done', "Done")],
        string="State of the onboarding property step",
        default='not_done')
    hms_onboarding_building_state = fields.Selection(
        [('not_done', "Not done"), ('just_done', "Just done"),
         ('done', "Done")],
        string="State of the onboarding building step",
        default='not_done')
    property_onboarding_state = fields.Selection(
        [('not_done', "Not done"), ('just_done', "Just done"),
         ('done', "Done"), ('closed', "Closed")],
        string="State of the property onboarding panel",
        default='not_done')

    contact_ids = fields.Many2many(
        'res.partner',
        'hms_property_contact_rel',
        'property_id',
        'partner_id',
        string='Contacts',
        track_visibility=True,
        domain=
        "[('is_company', '=', False), ('is_group', '=', False), ('is_guest', '=', False)]",
        help='Contact')
    bankinfo_ids = fields.One2many('res.bank',
                                   'property_id',
                                   string="Bank Info",
                                   help='Bank Info')
    comments = fields.Text(string='Notes')
    roomtype_ids = fields.Many2many('hms.roomtype',
                                    default=default_get_roomtype,
                                    help='Room Type')
    building_ids = fields.Many2many('hms.building',
                                    default=default_get_building,
                                    help='Building')
    market_ids = fields.Many2many('hms.marketsegment',
                                  string="Market Segment",
                                  help='Matket Segment')
    propertyroom_ids = fields.One2many('hms.property.room',
                                       'property_id',
                                       string="Property Room",
                                       help='Property Room')
    building_count = fields.Integer("Building",
                                    compute='_compute_building_count',
                                    help='Building')
    room_count = fields.Integer("Room",
                                compute='_compute_room_count',
                                store=True,
                                help='Room')
    roomtype_count = fields.Integer("Room Type",
                                    compute='_compute_roomtype_count',
                                    help='Room Type')
    package_ids = fields.One2many('hms.package',
                                  'property_id',
                                  string="Package",
                                  help='Package')
    packageheader_ids = fields.One2many('hms.package.header',
                                        'property_id',
                                        string="Package",
                                        help='Package Header')
    packagegroup_ids = fields.One2many('hms.package.group',
                                       'property_id',
                                       string="Package Group",
                                       help='Package Group')
    subgroup_ids = fields.One2many('hms.subgroup',
                                   'property_id',
                                   string="Sub Group",
                                   help='Sub Group')
    transaction_ids = fields.One2many('hms.transaction',
                                      'property_id',
                                      string="Transaction",
                                      help='Transaction')
    creditlimit_ids = fields.One2many('hms.creditlimit',
                                      'property_id',
                                      string="Credit Limit",
                                      help='Creadit Limit')
    specialday_ids = fields.One2many('hms.specialday',
                                     'property_id',
                                     string="Special Days",
                                     help='Special Days')
    weekend_id = fields.One2many('hms.weekend',
                                 'property_id',
                                 string="Weekends",
                                 help='Weekends')
    ratecodeheader_ids = fields.One2many('hms.ratecode.header',
                                         'property_id',
                                         string="Rate Code",
                                         help='Rate Code')
    allotment_ids = fields.One2many('hms.allotment.line',
                                    'property_id',
                                    string="Allotment",
                                    help='Allotment')
    proomtype_ids = fields.One2many('hms.property.roomtype',
                                    'property_id',
                                    string="Property Room Type",
                                    help='Property Room Type')
    package_line_ids = fields.One2many('hms.package.charge.line',
                                       'property_id',
                                       string="Packages_line",
                                       help='Package Line')
    check_in_time = fields.Float(string="Check-In Time", help="Check-In Time")
    check_out_time = fields.Float(string="Check-Out Time",
                                  help='Check-Out Time')
    availability = fields.Integer(default=365,
                                  string="Availability",
                                  help='Avaliability')
    reservation_line_ids = fields.One2many('hms.reservation.line',
                                           'property_id',
                                           string="Reservation lines",
                                           help='Reseravtion Line')
    high_occupancy = fields.Selection(AVAILABLE_PERCENTAGE,
                                      string="High Occupancy",
                                      default='70',
                                      help='High Occupancy')
    low_occupancy = fields.Selection(AVAILABLE_PERCENTAGE,
                                     string="Low Occupancy",
                                     default='20',
                                     help='High Ocupancy')

    property_code_len = fields.Integer(
        "Property Code Length",
        track_visibility=True,
        default=lambda self: self.env.user.company_id.property_code_len)
    building_code_len = fields.Integer(
        "Building Code Length",
        track_visibility=True,
        default=lambda self: self.env.user.company_id.building_code_len)
    location_code_len = fields.Integer(
        "Floor Code Length",
        track_visibility=True,
        default=lambda self: self.env.user.company_id.location_code_len)
    roomtype_code_len = fields.Integer(
        "Room Type Code Length",
        track_visibility=True,
        default=lambda self: self.env.user.company_id.roomtype_code_len)

    profile_id_format = fields.Many2one(
        "hms.format",
        "Guest Profile ID Format",
        track_visibility=True,
        default=lambda self: self.env.user.company_id.profile_id_format.id)
    confirm_id_format = fields.Many2one(
        "hms.format",
        "Confirm ID Format",
        track_visibility=True,
        default=lambda self: self.env.user.company_id.confirm_id_format.id)
    cprofile_id_format = fields.Many2one(
        "hms.format",
        "Company Profile ID Format",
        track_visibility=True,
        default=lambda self: self.env.user.company_id.cprofile_id_format.id)
    gprofile_id_format = fields.Many2one(
        "hms.format",
        "Group Profile ID Format",
        track_visibility=True,
        default=lambda self: self.env.user.company_id.gprofile_id_format.id)
    soprofile_id_format = fields.Many2one(
        'hms.format',
        "Sale Order No Format",
        track_visibility=True,
        default=lambda self: self.env.user.company_id.soprofile_id_format.id)
    ivprofile_id_format = fields.Many2one(
        'hms.format',
        "Invoice No Format",
        track_visibility=True,
        default=lambda self: self.env.user.company_id.ivprofile_id_format.id)

    # Tax
    sale_tax_id = fields.Many2one(
        'account.tax',
        string="Default Sale Tax",
        required=True,
        track_visibility=True,
        default=lambda self: self.env.user.company_id.sale_tax_id.id)
    # group_show_line_subtotals_tax_excluded and group_show_line_subtotals_tax_included are opposite,
    # so we can assume exactly one of them will be set, and not the other.
    # We need both of them to coexist so we can take advantage of automatic group assignation.
    group_show_line_subtotals_tax_excluded = fields.Boolean(
        "Show line subtotals without taxes (B2B)",
        implied_group='account.group_show_line_subtotals_tax_excluded',
        group='base.group_portal,base.group_user,base.group_public')
    group_show_line_subtotals_tax_included = fields.Boolean(
        "Show line subtotals with taxes (B2C)",
        implied_group='account.group_show_line_subtotals_tax_included',
        group='base.group_portal,base.group_user,base.group_public')
    show_line_subtotals_tax_selection = fields.Selection(
        [('tax_excluded', 'Tax-Excluded'), ('tax_included', 'Tax-Included')],
        string="Line Subtotals Tax Display",
        default=lambda self: self.env.user.company_id.
        show_line_subtotals_tax_selection,
        config_parameter='account.show_line_subtotals_tax_selection')
    # Service Charges
    enable_service_charge = fields.Boolean(
        string='Service Charges',
        default=lambda self: self.env.user.company_id.enable_service_charge)
    service_charge_type = fields.Selection(
        [('amount', 'Amount'), ('percentage', 'Percentage')],
        string='Type',
        default=lambda self: self.env.user.company_id.service_charge_type)
    service_product_id = fields.Many2one(
        'product.product',
        string='Service Product',
        domain="[('sale_ok', '=', True),"
        "('type', '=', 'service')]",
        default=lambda self: self.env.user.company_id.service_product_id.id)
    service_charge = fields.Float(
        string='Service Charge',
        default=lambda self: self.env.user.company_id.service_charge)
    svc_include_tax = fields.Boolean(string='Include Tax')
    svc_as_line = fields.Boolean(string='Service Charge as Invoice Line')
    disable_popup = fields.Boolean(string='Disable Popup')
    svc_inc_exc = fields.Selection(string='Service Charges Included/Excluded',
                                   selection=[('included', 'Svc-Included'),
                                              ('excluded', 'Svc-Excluded')],
                                   compute='_compute_svc_include_exclude',
                                   inverse='_write_svc_include_exclude',
                                   track_visibility=True,
                                   help='Service Charges Included or Excluded')
    is_include = fields.Boolean(string="Is Included", default=False)

    _sql_constraints = [('code_unique', 'UNIQUE(code)',
                         'Hotel ID already exists! Hotel ID must be unique!')]

    # Radio Button for Service Charge Include/Exclude
    @api.depends('is_include')
    def _compute_svc_include_exclude(self):
        for rec in self:
            if rec.is_include or self._context.get(
                    'default_svc_inc_exc') == 'included':
                rec.svc_inc_exc = 'included'
                rec.is_include = True
            else:
                rec.svc_inc_exc = 'excluded'

    def _write_svc_include_exclude(self):
        for rec in self:
            rec.is_include = rec.svc_inc_exc == 'included'

    @api.onchange('svc_inc_exc')
    def onchange_svc_inc_exc(self):
        self.is_include = (self.svc_inc_exc == 'included')

    @api.onchange('show_line_subtotals_tax_selection')
    def _onchange_sale_tax(self):
        if self.show_line_subtotals_tax_selection == "tax_excluded":
            self.update({
                'group_show_line_subtotals_tax_included': False,
                'group_show_line_subtotals_tax_excluded': True,
            })
        else:
            self.update({
                'group_show_line_subtotals_tax_included': True,
                'group_show_line_subtotals_tax_excluded': False,
            })

    @api.onchange('enable_service_charge')
    def set_config_service_charge(self):
        if self.enable_service_charge:
            if not self.service_product_id:
                domain = [('sale_ok', '=', True), ('type', '=', 'service')]
                self.service_product_id = self.env['product.product'].search(
                    domain, limit=1)
            self.service_charge = 10.0
        else:
            self.service_product_id = False
            self.service_charge = 0.0

    @api.depends('system_date')
    def _compute_is_night_audit(self):
        for rec in self:
            if rec.system_date > date.today():
                rec.is_night_audit = True
            else:
                rec.is_night_audit = False

    @api.depends('is_manual')
    def _compute_night_audit(self):
        for property in self:
            if property.is_manual or self._context.get(
                    'default_night_audit') == 'manual':
                property.night_audit = 'manual'
                property.is_manual = True
            else:
                property.night_audit = 'auto'

    def _write_night_audit(self):
        for property in self:
            property.is_manual = property.night_audit == 'manual'

    @api.onchange('night_audit')
    def onchange_night_audit(self):
        if self.night_audit == 'manual':
            self.is_manual = True
        elif self.night_audit == 'auto':
            self.is_manual = False

    # Night Audit Manual Action
    def action_night_audit(self):

        # For Forecast Update
        avail_objs = self.env['hms.availability'].search([
            ('property_id', '=', self.id),
            ('avail_date', '<', self.system_date)
        ])

        for avail_obj in avail_objs:
            avail_obj.update({'active': False})
            rt_avail_objs = self.env['hms.roomtype.available'].search([
                ('property_id', '=', self.id),
                ('ravail_date', '<=', self.system_date),
                ('availability_id', '=', avail_obj.id)
            ])

            new_avail_obj = self.env['hms.availability'].create({
                'property_id':
                avail_obj.property_id.id,
                'avail_date':
                avail_obj.avail_date + timedelta(days=self.availability),
                'total_room':
                self.room_count
            })

            for rt_avail_obj in rt_avail_objs:
                rt_avail_obj.update({'active': False})
                vals = []
                vals.append((0, 0, {
                    'availability_id': new_avail_obj.id,
                    'property_id': new_avail_obj.property_id.id,
                    'ravail_date': new_avail_obj.avail_date,
                    'ravail_rmty': rt_avail_obj.ravail_rmty.id,
                    'color': rt_avail_obj.color,
                }))
                new_avail_obj.update({'avail_roomtype_ids': vals})

        # For Removing Reservation and Reservation Line Update
        out_date_rsvn_lines = self.env['hms.reservation.line'].search([
            ('property_id', '=', self.id), ('arrival', '<', self.system_date),
            ('active', '=', True), '|', ('state', '=', 'booking'),
            ('state', '=', 'reservation')
        ])
        for rsvn_line in out_date_rsvn_lines:
            rsvn_line.update({'active': False})

        out_date_reservations = self.env['hms.reservation'].search([
            ('property_id', '=', self.id), ('arrival', '<', self.system_date),
            '|', ('state', '=', 'reservation'), ('state', '=', 'booking')
        ])
        for rsvn in out_date_reservations:
            if len(rsvn.reservation_line_ids) == 0:
                rsvn.update({'active': False})

        # For No Show Reservation and Reservation Line Update
        # Reservation Line
        no_show_rsvn_lines = self.env['hms.reservation.line'].search([
            ('property_id', '=', self.id), ('arrival', '<', self.system_date),
            ('state', '=', 'confirm')
        ])
        for no_show_rsvn_line in no_show_rsvn_lines:
            no_show_rsvn_line.update({'is_no_show': True})
            # Reservation
        no_show_rsvns = self.env['hms.reservation'].search([
            ('property_id', '=', self.id), ('arrival', '<', self.system_date),
            ('state', '=', 'confirm')
        ])
        for no_show_rsvn in no_show_rsvns:
            no_show_line_count = 0
            for line in no_show_rsvn.reservation_line_ids:
                if line.is_no_show is True:
                    no_show_line_count += 1
            if len(no_show_rsvn.reservation_line_ids) == no_show_line_count:
                no_show_rsvn.update({'is_no_show': True})

        # For removing No Show Reservation and Reservatin Line
        # Reservation Lines
        ex_noshow_rsvn_lines = self.env['hms.reservation.line'].search([
            ('property_id', '=', self.id), ('is_no_show', '=', True),
            ('departure', '<', self.system_date)
        ])
        for ex_noshow_rsvn_line in ex_noshow_rsvn_lines:
            ex_noshow_rsvn_line.update({'active': False})
            # Reservation
        ex_noshow_rsvns = self.env['hms.reservation'].search([
            ('property_id', '=', self.id), ('is_no_show', '=', True),
            ('departure', '<', self.system_date)
        ])
        for ex_noshow_rsvn in ex_noshow_rsvns:
            if len(ex_noshow_rsvn.reservation_line_ids) == 0:
                ex_noshow_rsvn.update({'active': False})

        # For removing Ratecode Details
        ex_rc_details = self.env['hms.ratecode.details'].search([
            ('property_id', '=', self.id), ('end_date', '<', self.system_date)
        ])
        for ex_rc_detail in ex_rc_details:
            ex_rc_detail.update({'active': False})

        # For System Date Update

        self.system_date = self.system_date + timedelta(days=1)

        return

    @api.model
    def action_night_audit_auto(self):

        # For Forecast Update
        property_objs = self.env['hms.property'].search([])
        for record in property_objs:
            if record.is_manual is False:
                avail_objs = self.env['hms.availability'].search([
                    ('property_id', '=', record.id),
                    ('avail_date', '<=', self.system_date)
                ])

                for avail_obj in avail_objs:
                    avail_obj.update({'active': False})
                    rt_avail_objs = self.env['hms.roomtype.available'].search([
                        ('property_id', '=', record.id),
                        ('ravail_date', '<=', self.system_date),
                        ('availability_id', '=', avail_obj.id)
                    ])

                    new_avail_objs = self.env['hms.availability'].create({
                        'property_id':
                        avail_obj.property_id.id,
                        'avail_date':
                        avail_obj.avail_date +
                        timedelta(days=record.availability),
                        'total_room':
                        record.room_count
                    })

                    for new_avail_obj in new_avail_objs:

                        for rt_avail_obj in rt_avail_objs:
                            rt_avail_obj.update({'active': False})
                            vals = []
                            vals.append((0, 0, {
                                'availability_id':
                                new_avail_obj.id,
                                'property_id':
                                new_avail_obj.property_id.id,
                                'ravail_date':
                                new_avail_obj.avail_date,
                                'ravail_rmty':
                                rt_avail_obj.ravail_rmty.id,
                                'color':
                                rt_avail_obj.color,
                            }))
                            new_avail_obj.update({'avail_roomtype_ids': vals})

        # For Removing Reservation and Reservation Line
        out_date_rsvn_lines = self.env['hms.reservation.line'].search([
            ('arrival', '<', self.system_date), ('active', '=', True), '|',
            ('state', '=', 'booking'), ('state', '=', 'reservation')
        ])
        for rsvn_line in out_date_rsvn_lines:
            if rsvn_line.property_id.is_manual is False:
                rsvn_line.update({'active': False})

        out_date_reservations = self.env['hms.reservation'].search([
            ('arrival', '<', self.system_date), '|', ('state', '=', 'booking'),
            ('state', '=', 'reservation')
        ])
        for rsvn in out_date_reservations:
            if rsvn.property_id.is_manual is False:
                if len(rsvn.reservation_line_ids) == 0:
                    rsvn.update({'active': False})

        # For No Show Reservation and Reservation Line Update
        no_show_rsvn_lines = self.env['hms.reservation.line'].search([
            ('arrival', '<', self.system_date), ('state', '=', 'confirm')
        ])
        for no_show_rsvn_line in no_show_rsvn_lines:
            if no_show_rsvn_line.property_id.is_manual is False:
                no_show_rsvn_line.update({'is_no_show': True})
        no_show_rsvns = self.env['hms.reservation'].search([
            ('arrival', '<', self.system_date), ('state', '=', 'confirm')
        ])
        for no_show_rsvn in no_show_rsvns:
            if no_show_rsvn.property_id.is_manual is False:
                no_show_line_count = 0
                for line in no_show_rsvn.reservation_line_ids:
                    if line.is_no_show is True:
                        no_show_line_count += 1
                if len(no_show_rsvn.reservation_line_ids
                       ) == no_show_line_count:
                    no_show_rsvn.update({'is_no_show': True})

        # For removing No Show Reservation and Reservatin Line
        ex_noshow_rsvn_lines = self.env['hms.reservation.line'].search([
            ('is_no_show', '=', True), ('departure', '<', self.system_date)
        ])
        for ex_noshow_rsvn_line in ex_noshow_rsvn_lines:
            if ex_noshow_rsvn_line.property_id.is_manual is False:
                ex_noshow_rsvn_line.update({'active': False})

        ex_noshow_rsvns = self.env['hms.reservation'].search([
            ('is_no_show', '=', True), ('departure', '<', self.system_date)
        ])
        for ex_noshow_rsvn in ex_noshow_rsvns:
            if ex_noshow_rsvn.property_id.is_manual is False:
                if len(ex_noshow_rsvn.reservation_line_ids) == 0:
                    ex_noshow_rsvn.update({'active': False})

        # For removing Ratecode Details
        ex_rc_details = self.env['hms.ratecode.details'].search([
            ('end_date', '<', self.system_date)
        ])
        for ex_rc_detail in ex_rc_details:
            if ex_rc_detail.is_manual is False:
                ex_rc_detail.update({'active': False})

        # For System Date Update
        property_objs = self.env['hms.property'].search([])
        for record in property_objs:
            if record.is_manual is False:
                record.system_date = record.system_date + timedelta(days=1)

    def set_onboarding_step_done(self, step_name):
        if self[step_name] == 'not_done':
            self[step_name] = 'just_done'

    def action_save_onboarding_property_step(self):
        if bool(self.street):
            self.set_onboarding_step_done('hms_onboarding_property_state')

    def action_save_onboarding_building_step(self):
        self.set_onboarding_step_done('hms_onboarding_building_state')

    @api.model
    def action_close_property_onboarding(self):
        """ Mark the property onboarding panel as closed. """
        self.env.hotel.property_onboarding_state = 'closed'

    @api.onchange('currency_id')
    def onchange_currency_id(self):
        for record in self:
            country_id = None
            if record.currency_id:
                country_ids = self.env['res.country'].search([
                    ('currency_id', '=', record.currency_id.id)
                ])
                if len(country_ids) > 1:
                    country_id = country_ids[0]
                else:
                    country_id = country_ids
            record.country_id = country_id

    @api.onchange('code')
    def onchange_code(self):
        for record in self:
            length = 0
            if record.code:
                length = len(record.code)
            if record.property_code_len:
                if length > record.property_code_len:
                    raise UserError(
                        _("Property Code Length must not exceed %s characters."
                          % (record.property_code_len)))

    def _compute_is_property(self):
        self.is_property = True

    def action_weekend(self):
        weekend = self.mapped('weekend_id')
        action = self.env.ref('hms.weekend_action_window').read()[0]
        if (len(weekend)) == 1:
            # action['domain'] = [('id', '=', weekend.id)]
            form_view = [(self.env.ref('hms.weekend_view_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = weekend.id
        elif len(weekend) == 0:
            form_view = [(self.env.ref('hms.weekend_view_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = weekend.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        context = {
            'default_type': 'out_weekend',
        }
        return action

    def action_specialday(self):
        specialdays = self.mapped('specialday_ids')
        action = self.env.ref('hms.special_day_action_window').read()[0]
        if len(specialdays) >= 1:
            action['domain'] = [('id', 'in', specialdays.ids)]
        elif len(specialdays) == 0:
            form_view = [(self.env.ref('hms.special_day_view_form').id, 'form')
                         ]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = specialdays.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        context = {
            'default_type': 'out_specialday',
        }
        return action

    def action_allotment(self):
        allotments = self.mapped('allotment_ids')
        action = self.env.ref('hms.action_allotment_detail_all').read()[0]
        if len(allotments) >= 1:
            action['domain'] = [('id', 'in', allotments.ids)]
        elif len(allotments) == 0:
            form_view = [(self.env.ref('hms.view_allotment_line_form').id,
                          'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = allotments.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        context = {
            'default_type': 'out_allotment',
        }
        return action

    def action_package(self):
        packages = self.mapped('package_ids')
        action = self.env.ref('hms.package_action_window').read()[0]
        if len(packages) >= 1:
            action['domain'] = [('id', 'in', packages.ids)]
        elif len(packages) == 0:
            form_view = [(self.env.ref('hms.package_view_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = packages.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        context = {
            'default_type': 'out_package',
        }
        return action

    def action_transaction(self):
        transactions = self.mapped('transaction_ids')
        action = self.env.ref('hms.transaction_action_window').read()[0]
        if len(transactions) >= 1:
            action['domain'] = [('id', 'in', transactions.ids)]
        elif len(transactions) == 0:
            form_view = [(self.env.ref('hms.transaction_view_form').id, 'form')
                         ]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = transactions.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        context = {
            'default_type': 'out_transaction',
        }
        return action

    def action_creditlimit(self):
        credit_limit = self.mapped('creditlimit_ids')
        action = self.env.ref('hms.credit_limit_action_window').read()[0]
        if len(credit_limit) >= 1:
            action['domain'] = [('id', 'in', credit_limit.ids)]
        elif len(credit_limit) == 0:
            form_view = [(self.env.ref('hms.credit_limit_view_form').id,
                          'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = credit_limit.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        context = {
            'default_type': 'out_creditlimit',
        }
        return action

    def action_newratecode(self):
        rate_code = self.mapped('ratecodeheader_ids')
        action = self.env.ref('hms.rate_code_header_action_window').read()[0]
        if len(rate_code) >= 1:
            action['domain'] = [('id', 'in', rate_code.ids)]
        elif len(rate_code) == 0:
            form_view = [(self.env.ref('hms.rate_code_header_view_form').id,
                          'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = rate_code.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        context = {
            'default_type': 'out_ratecode',
        }
        return action

    def action_newpackage(self):
        packages = self.mapped('packageheader_ids')
        action = self.env.ref('hms.package_header_action_window').read()[0]
        if len(packages) >= 1:
            action['domain'] = [('id', 'in', packages.ids)]
        elif len(packages) == 0:
            form_view = [(self.env.ref('hms.package_header_view_form').id,
                          'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = packages.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        context = {
            'default_type': 'out_package',
        }
        return action

    def action_package_group(self):
        package_groups = self.mapped('packagegroup_ids')
        action = self.env.ref('hms.package_group_action_window').read()[0]
        if len(package_groups) >= 1:
            action['domain'] = [('id', 'in', package_groups.ids)]
        elif len(package_groups) == 0:
            form_view = [(self.env.ref('hms.package_group_view_form').id,
                          'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = package_groups.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        context = {
            'default_type': 'out_package_group',
        }
        return action

    def action_building_count(self):
        # buildings = self.mapped('building_ids')
        buildings = self.building_ids.filtered(
            lambda x: x.building_name != "ZZZ")
        action = self.env.ref('hms.building_action_window').read()[0]
        if len(buildings) > 1:
            action['domain'] = [('id', 'in', buildings.ids)]
        elif len(buildings) == 1:
            form_view = [(self.env.ref('hms.building_view_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = buildings.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_type': 'out_building',
        }
        return action

    def _compute_building_count(self):
        building_ids = self.building_ids.filtered(
            lambda x: x.building_name != "ZZZ")
        self.building_count = len(building_ids)

    # Room Count
    def action_room_count(self):
        # rooms = self.mapped('propertyroom_ids')
        rooms = self.propertyroom_ids.filtered(
            lambda x: x.roomtype_id.code[0] != 'H')
        action = self.env.ref('hms.property_room_action_window').read()[0]
        if len(rooms) > 1:
            action['domain'] = [('id', 'in', rooms.ids)]
        elif len(rooms) == 1:
            form_view = [(self.env.ref('hms.property_room_view_form').id,
                          'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = rooms.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_type': 'out_room',
        }
        return action

    @api.depends('propertyroom_ids')
    def _compute_room_count(self):
        property_rooms = self.env['hms.property.room'].search([('property_id',
                                                                '=', self.id)])
        room_count = 0
        for rec in property_rooms:
            if rec.roomtype_id.code[0] != 'H':
                room_count += 1
        self.room_count = room_count

    # Room Type Count
    def action_room_type_count(self):
        # room_types = self.mapped('roomtype_ids')
        room_types = self.roomtype_ids.filtered(lambda x: x.code[0] != 'H')
        action = self.env.ref('hms.room_type_action_window').read()[0]
        if len(room_types) > 1:
            action['domain'] = [('id', 'in', room_types.ids)]
        elif len(room_types) == 1:
            form_view = [(self.env.ref('hms.room_type_view_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = room_types.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_type': 'out_room_type',
        }
        return action

    def _compute_roomtype_count(self):
        roomtype_ids = self.roomtype_ids.filtered(lambda x: x.code[0] != 'H')
        self.roomtype_count = len(roomtype_ids)

    # Create Property Room Type
    def _create_property_roomtype(self, roomtype_id, property_rooms,
                                  property_id):
        if property_rooms:
            total_rooms = len(property_rooms)
            self.env['hms.property.roomtype'].create({
                'property_id':
                property_id,
                'roomtype_id':
                roomtype_id,
                'total_rooms':
                total_rooms,
            })
        else:
            self.env['hms.property.roomtype'].create({
                'property_id': property_id,
                'roomtype_id': roomtype_id,
                'total_rooms': 0,
            })

        #Dummy Room

    @api.onchange('roomqty')
    def _compute_dummy_room_count(self):
        self.dummy_rooms = math.ceil(self.roomqty * 0.03) * 10

    # Limit total rooms
    @api.constrains('roomqty', 'propertyroom_ids')
    def limit_total_room(self):
        total_rooms = self.propertyroom_ids.filtered(
            lambda x: x.roomtype_id.code[0] != 'H')
        if len(total_rooms) > self.roomqty:
            raise ValidationError(
                _("Number of rooms must not exceed Total Rooms."))

    @api.constrains('roomqty')
    def check_total_room(self):
        if self.roomqty <= 0:
            raise ValidationError(
                _("Total Room cannot be zero or smaller than zero"))

    #Create Sequence for each Property
    def create_sequence(self, property):
        if property.gprofile_id_format:
            if property.gprofile_id_format.format_line_id.filtered(
                    lambda x: x.value_type == "dynamic"
            ).dynamic_value == "property code":
                padding = property.gprofile_id_format.format_line_id.filtered(
                    lambda x: x.value_type == "digit")
                self.env['ir.sequence'].create({
                    'name':
                    property.code + property.gprofile_id_format.code,
                    'code':
                    property.code + property.gprofile_id_format.code,
                    'padding':
                    padding.digit_value,
                    'company_id':
                    False,
                    'use_date_range':
                    True,
                })
        if property.confirm_id_format:
            if property.confirm_id_format.format_line_id.filtered(
                    lambda x: x.value_type == "dynamic"
            ).dynamic_value == "property code":
                padding = property.confirm_id_format.format_line_id.filtered(
                    lambda x: x.value_type == "digit")
                self.env['ir.sequence'].create({
                    'name':
                    property.code + property.confirm_id_format.code,
                    'code':
                    property.code + property.confirm_id_format.code,
                    'padding':
                    padding.digit_value,
                    'company_id':
                    False,
                    'use_date_range':
                    True,
                })
        if property.soprofile_id_format:
            if property.soprofile_id_format.format_line_id.filtered(
                    lambda x: x.value_type == "dynamic"
            ).dynamic_value == "property code":
                padding = property.soprofile_id_format.format_line_id.filtered(
                    lambda x: x.value_type == "digit")
                self.env['ir.sequence'].create({
                    'name':
                    property.code + property.soprofile_id_format.code,
                    'code':
                    property.code + property.soprofile_id_format.code,
                    'padding':
                    padding.digit_value,
                    'company_id':
                    False,
                    'use_date_range':
                    True,
                })
        if property.ivprofile_id_format:
            if property.ivprofile_id_format.format_line_id.filtered(
                    lambda x: x.value_type == "dynamic"
            ).dynamic_value == "property code":
                padding = property.ivprofile_id_format.format_line_id.filtered(
                    lambda x: x.value_type == "digit")
                self.env['ir.sequence'].create({
                    'name':
                    property.code + property.ivprofile_id_format.code,
                    'code':
                    property.code + property.ivprofile_id_format.code,
                    'padding':
                    padding.digit_value,
                    'company_id':
                    False,
                    'use_date_range':
                    True,
                })

    # Create function
    @api.model
    def create(self, values):
        # _logger.info(values)
        res = super(Property, self).create(values)
        res.create_sequence(res)
        if res.roomtype_ids:
            for rec in res.roomtype_ids:
                property_rooms = self.env['hms.property.room'].search([
                    ('property_id', '=', res.id), ('roomtype_id', '=', rec.id)
                ])
                roomtype_id = rec.id
                property_id = res.id
                self._create_property_roomtype(roomtype_id, property_rooms,
                                               property_id)

        if res.availability:

            avail_date = datetime.today() - timedelta(days=1)
            for rec in range(res.availability):
                avail_date1 = avail_date + timedelta(days=rec + 1)
                self.env['hms.availability'].create({
                    'property_id':
                    res.id,
                    'avail_date':
                    avail_date1,
                    'total_room':
                    res.room_count,
                })

            if res.propertyroom_ids or res.roomtype_ids:
                if res.roomtype_ids:
                    hfo_roomtype = self.env['hms.roomtype'].search([
                        ('code', '=ilike', 'H%')
                    ])
                    room_types = list(
                        set(res.roomtype_ids) - set(hfo_roomtype))
                    avail_objs = self.env['hms.availability'].search([
                        ('property_id', '=', res.id)
                    ])
                    for avail_obj in avail_objs:
                        for roomtype in room_types:
                            vals = []
                            property_rooms = self.env[
                                'hms.property.room'].search([
                                    ('property_id', '=', res.id),
                                    ('roomtype_id', '=', roomtype.id)
                                ])
                            total_rooms = len(property_rooms)
                            vals.append((0, 0, {
                                'ravail_rmty': roomtype.id,
                                'property_id': res.id,
                                'ravail_date': avail_obj.avail_date,
                                'total_room': total_rooms,
                                'color': roomtype.color,
                            }))
                            avail_obj.update({'avail_roomtype_ids': vals})

        if res.dummy_rooms:
            room_no = 9001
            for record in range(res.dummy_rooms):
                roomtype_id = self.env['hms.roomtype'].search([
                    ('code', '=ilike', 'H%')
                ])
                building_id = self.env['hms.building'].search([('id', '=', 1)])
                location_id = self.env['hms.roomlocation'].search([('id', '=',
                                                                    1)])
                self.env['hms.property.room'].create({
                    'room_no':
                    room_no,
                    'property_id':
                    res.id,
                    'roomtype_id':
                    roomtype_id.id,
                    'building_id':
                    building_id.id,
                    'roomlocation_id':
                    location_id.id,
                    'room_bedqty':
                    1,
                    'is_hfo':
                    True,
                })
                room_no += 1

        if res.name:
            company = self.env['res.company'].search([('name', '=', res.name)])
            company_obj = self.env['res.company']
            crm = self.env['hms.company.category'].search([('code', '=', 'HTL')
                                                           ]).id

            if not company:
                company_obj = self.env['res.company'].create({
                    'name':
                    res.name,
                    'street':
                    res.address1,
                    'street2':
                    res.address2,
                    'zip':
                    res.zip,
                    'city':
                    res.city_id.id,
                    'state_id':
                    res.state_id.id,
                    'country_id':
                    res.country_id.id,
                    'email':
                    res.email,
                    'phone':
                    res.phone,
                    'website':
                    res.website,
                    'currency_id':
                    res.currency_id.id,
                    'scurrency_id':
                    res.scurrency_id.id,
                    'company_channel_type':
                    crm,
                })
                res.company_id = company_obj.id

            else:
                res.company_id = company.id
                res.currency_id = company.currency_id.id
                res.scurrency_id = company.scurrency_id.id

            pos_admin = self.env['ir.model.data'].xmlid_to_res_id(
                'point_of_sale.group_pos_manager')
            sale_admin = self.env['ir.model.data'].xmlid_to_res_id(
                'sales_team.group_sale_manager')
            contact = self.env['ir.model.data'].xmlid_to_res_id(
                'base.group_partner_manager')
            setting = self.env['ir.model.data'].xmlid_to_res_id(
                'base.group_system')
            internal_user = self.env['ir.model.data'].xmlid_to_res_id(
                'base.group_user')
            property = self.env['ir.model.data'].xmlid_to_res_id(
                'hms.group_property_manager')
            reservation = self.env['ir.model.data'].xmlid_to_res_id(
                'hms.group_reservation_manager')

            user_obj = self.env['res.users'].create({
                'name':
                res.code + " Administrator",
                'login':
                res.code.lower() + "admin",
                'company_ids': [(4, company.id or company_obj.id),
                                (4, res.hotelgroup_id.id)],
                'company_id':
                company.id or company_obj.id,
                'property_id': [(4, res.id)],
                'groups_id': [(4, property), (4, reservation),
                              (4, internal_user), (4, setting), (4, contact),
                              (4, pos_admin), (4, sale_admin)]
            })

        if not res.show_line_subtotals_tax_selection:
            raise UserError(
                _("Please choose Line Subtotal Tax Display in Configuration" +
                  "\n" + "(Tax-Excluded or Tax-Included)"))

        return res

    # Write Function
    def write(self, values):
        res = super(Property, self).write(values)

        if 'code' in values.keys():
            same_code_objs = self.env['ir.sequence'].search([
                ('code', '=', self.code + self.gprofile_id_format.code)
            ])
            if not same_code_objs:
                self.create_sequence(self)

        if 'roomtype_ids' in values.keys(
        ) or 'propertyroom_ids' in values.keys():
            hfo_roomtype = self.env['hms.roomtype'].search([('code', '=ilike',
                                                             'H%')])
            roomtypes = list(set(self.roomtype_ids) - set(hfo_roomtype))

            for rec in roomtypes:
                property_roomtype = self.env['hms.property.roomtype'].search([
                    ('property_id', '=', self.id), ('roomtype_id', '=', rec.id)
                ])
                if property_roomtype:
                    property_rooms = self.env['hms.property.room'].search([
                        ('property_id', '=', self.id),
                        ('roomtype_id', '=', rec.id)
                    ])
                    total_rooms = len(property_rooms)
                    property_roomtype.total_rooms = total_rooms
                else:
                    property_rooms = self.env['hms.property.room'].search([
                        ('property_id', '=', self.id),
                        ('roomtype_id', '=', rec.id)
                    ])
                    property_id = self.id
                    roomtype_id = rec.id
                    self._create_property_roomtype(roomtype_id, property_rooms,
                                                   property_id)

                # Update Total Rooms for Room Type Available
                ravail_obj = self.env['hms.roomtype.available'].search([
                    ('property_id', '=', self.id), ('ravail_rmty', '=', rec.id)
                ])
                if ravail_obj:
                    for ravail in ravail_obj:
                        ravail.total_room = total_rooms
                    # Update Total Rooms for Availability
                    ptotal_rooms = self.room_count
                    avail_objs = self.env['hms.availability'].search([
                        ('property_id', '=', self.id)
                    ])
                    for avail_obj in avail_objs:
                        avail_obj.update({'total_room': ptotal_rooms})

                # Create & Update Total rooms for all availability
                else:
                    ptotal_rooms = self.room_count
                    avail_objs = self.env['hms.availability'].search([
                        ('property_id', '=', self.id)
                    ])
                    property_rooms = self.env['hms.property.room'].search([
                        ('property_id', '=', self.id),
                        ('roomtype_id', '=', rec.id)
                    ])
                    total_rooms = len(property_rooms)
                    for avail_obj in avail_objs:
                        vals = []
                        vals.append((0, 0, {
                            'ravail_rmty': rec.id,
                            'property_id': avail_obj.property_id.id,
                            'ravail_date': avail_obj.avail_date,
                            'total_room': total_rooms,
                            'color': rec.color,
                        }))
                        avail_obj.update({
                            'avail_roomtype_ids': vals,
                            'total_room': ptotal_rooms
                        })
        return res

    # Unlink Function
    def unlink(self):
        sequence_objs = self.env['ir.sequence']
        forecast_objs = self.env['hms.availability']
        roomavailable_objs = self.env['hms.roomtype.available']
        property_roomtypeobjs = self.env['hms.property.roomtype']
        reservation_objs = self.env['hms.reservation']
        reservation_line_objs = self.env['hms.reservation.line']
        property_room_objs = self.env['hms.property.room']
        special_day_objs = self.env['hms.specialday']
        weekend_objs = self.env['hms.weekend']
        package_objs = self.env['hms.package']
        subgroup_objs = self.env['hms.subgroup']
        transaction_objs = self.env['hms.transaction']
        creditlimit_objs = self.env['hms.creditlimit']
        ratecode_header_objs = self.env['hms.ratecode.header']
        ratecode_detail_objs = self.env['hms.ratecode.details']

        for rec in self:
            if rec.gprofile_id_format:
                sequence_objs += self.env['ir.sequence'].search([
                    ('code', '=', rec.code + rec.gprofile_id_format.code)
                ])
            if rec.confirm_id_format:
                sequence_objs += self.env['ir.sequence'].search([
                    ('code', '=', rec.code + rec.confirm_id_format.code)
                ])
            sequence_objs.unlink()
            forecast_objs += self.env['hms.availability'].search([
                ('property_id', '=', rec.id)
            ])
            forecast_objs.unlink()
            roomavailable_objs += self.env['hms.roomtype.available'].search([
                ('property_id', '=', rec.id)
            ])
            roomavailable_objs.unlink()
            property_roomtypeobjs += self.env['hms.property.roomtype'].search([
                ('property_id', '=', rec.id)
            ])
            property_roomtypeobjs.unlink()
            reservation_objs += self.env['hms.reservation'].search([
                ('property_id', '=', rec.id)
            ])
            reservation_objs.unlink()
            reservation_line_objs += self.env['hms.reservation.line'].search([
                ('property_id', '=', rec.id)
            ])
            property_room_objs += self.env['hms.property.room'].search([
                ('property_id', '=', rec.id)
            ])
            property_room_objs.unlink()
            special_day_objs += self.env['hms.specialday'].search([
                ('property_id', '=', rec.id)
            ])
            special_day_objs.unlink()
            weekend_objs += self.env['hms.weekend'].search([('property_id',
                                                             '=', rec.id)])
            weekend_objs.unlink()
            package_objs += self.env['hms.package'].search([('property_id',
                                                             '=', rec.id)])
            package_objs.unlink()
            subgroup_objs += self.env['hms.subgroup'].search([('property_id',
                                                               '=', rec.id)])
            subgroup_objs.unlink()
            transaction_objs += self.env['hms.transaction'].search([
                ('property_id', '=', rec.id)
            ])
            transaction_objs.unlink()
            creditlimit_objs += self.env['hms.creditlimit'].search([
                ('property_id', '=', rec.id)
            ])
            creditlimit_objs.unlink()
            ratecode_header_objs += self.env['hms.ratecode.header'].search([
                ('property_id', '=', rec.id)
            ])
            ratecode_header_objs.unlink()
            ratecode_detail_objs += self.env['hms.ratecode.details'].search([
                ('property_id', '=', rec.id)
            ])
            ratecode_detail_objs.unlink()

        res = super(Property, self).unlink()
        return res


class Property_roomtype(models.Model):
    _name = "hms.property.roomtype"
    _description = "Property_Roomtype"

    def get_property_id(self):
        property_id = self.env['hms.property'].browse(
            self._context.get('active_id', []))
        if property_id:
            return property_id

    property_id = fields.Many2one("hms.property",
                                  default=get_property_id,
                                  store=True,
                                  help='Property')
    roomtype_ids = fields.Many2many("hms.roomtype",
                                    related="property_id.roomtype_ids",
                                    help='Room Type')
    roomtype_id = fields.Many2one('hms.roomtype',
                                  string="Room Type",
                                  domain="[('id', '=?', roomtype_ids)]",
                                  required=True,
                                  help='Room Type')
    total_rooms = fields.Integer(string='Total Rooms', help='Total Rooms')

    _sql_constraints = [(
        'property_room_type_unique', 'UNIQUE(property_id,roomtype_id)',
        'Property Room Type already exists! Property Room Type name must be unique!'
    )]

    def name_get(self):
        result = []
        for record in self:
            result.append(
                (record.id, "{} ({})".format(record.property_id.code,
                                             record.roomtype_id.code)))
        return result


class Building(models.Model):
    _name = "hms.building"
    _description = "Building"
    _rec_name = 'building_name'

    sequence = fields.Integer(default=1)
    building_name = fields.Char(string='Building Name',
                                required=True,
                                help='Building Name')
    building_type = fields.Many2one('hms.buildingtype',
                                    string='Building Type',
                                    required=True,
                                    help='Building Type')
    building_location = fields.Char(string='Location', help='Location')
    building_img = fields.Binary(string='Building Image',
                                 attachment=True,
                                 store=True,
                                 help='Building Image')
    building_desc = fields.Text(string='Description', help='Description')
    building_capacity = fields.Integer(string='Capacity',
                                       default=1,
                                       required=True,
                                       help='Capacity')
    location_ids = fields.Many2many('hms.roomlocation',
                                    string="Room Location",
                                    required=True,
                                    help='Room Location')
    # location_number = fields.Integer("Location Number", compute="_room_location_count", readonly=True)

    _sql_constraints = [
        ('building_name_unique', 'UNIQUE(building_name)',
         'Building name already exists! Building name must be unique!')
    ]

    @api.constrains('location_ids', 'building_capacity')
    def _check_capacity(self):
        for record in self:
            if len(record.location_ids) > record.building_capacity:
                raise UserError(
                    _("Location number must not larger than building capacity."
                      ))


class BuildingType(models.Model):
    _name = "hms.buildingtype"
    _description = "Building Type"

    is_csv = fields.Boolean(default=False)
    building_type = fields.Char(string='Building Type',
                                required=True,
                                help='Building Type')
    buildingtype_desc = fields.Char(string='Description',
                                    required=True,
                                    help='Description')

    _sql_constraints = [(
        'building_type_unique', 'UNIQUE(building_type)',
        'Building type already exists with this name! Building type name must be unique!'
    )]

    def name_get(self):
        result = []
        for record in self:
            result.append(
                (record.id, "{} ({})".format(record.buildingtype_desc,
                                             record.building_type)))
        return result

    @api.onchange('building_type')
    def onchange_code(self):
        for record in self:
            length = 0
            if record.building_type:
                length = len(record.building_type)
            if record.env.user.company_id.building_code_len:
                if length > record.env.user.company_id.building_code_len:
                    raise UserError(
                        _("Building Type Code Length must not exceed %s characters."
                          % (record.env.user.company_id.building_code_len)))


class RoomLocation(models.Model):
    _name = "hms.roomlocation"
    _description = "Room Location"

    sequence = fields.Integer(default=1)
    location_code = fields.Char(string='Code',
                                size=3,
                                required=True,
                                help='Code')
    location_name = fields.Char(string='Name', required=True, help='Name')

    _sql_constraints = [(
        'location_code_unique', 'UNIQUE(location_code)',
        'Location code already exists with this name! Location code must be unique!'
    )]

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.location_code,
                                                       record.location_name)))
        return result

    @api.onchange('location_code')
    def onchange_code(self):
        for record in self:
            length = 0
            if record.location_code:
                length = len(record.location_code)
            if record.env.user.company_id.location_code_len:
                if length > record.env.user.company_id.location_code_len:
                    raise UserError(
                        _("Location Code Length must not exceed %s characters."
                          % (record.env.user.company_id.location_code_len)))


class BedType(models.Model):
    _name = "hms.bedtype"
    _description = "Bed Type"

    is_csv = fields.Boolean(default=False)
    name = fields.Char(string="Bed Type Name", help='Bed Type Name')
    no_of_bed = fields.Integer(string="No.of Beds", help='No. of Beds')


class RoomType(models.Model):
    _name = "hms.roomtype"
    _description = "Room Type"
    _rec_name = "code"

    is_used = fields.Boolean(default=False,
                             string="Is Used?",
                             compute='check_is_used')
    sequence = fields.Integer(default=1)
    active = fields.Boolean(string="Active",
                            default=True,
                            track_visibility=True)
    code = fields.Char(string='Code', size=50, required=True, help='Code')
    name = fields.Char(string='Room Type', required=True, help='Room Type')
    color = fields.Integer('Color Index',
                           default=0,
                           size=1,
                           help='Colour Index')
    fix_type = fields.Boolean(string="Fix Type", default=True, help='Fix Type')
    bed_type = fields.Many2many('hms.bedtype',
                                string="Bed Type",
                                help='Bed Type')
    totalroom = fields.Integer(string='Total Rooms',
                               compute='compute_totalroom',
                               help='Total Rooms')
    image = fields.Binary(string='Image',
                          attachment=True,
                          store=True,
                          help='Image')
    roomtype_desc = fields.Text(string='Description', help='Description')
    rate_id = fields.Many2one('hms.ratecode.details',
                              'Rate Details',
                              help='Rate Detials')

    _sql_constraints = [(
        'code_unique', 'UNIQUE(code)',
        'Room code already exists with this name! Room code name must be unique!'
    )]

    @api.depends('code')
    def check_is_used(self):
        for rec in self:
            used_property = self.env['hms.property'].search([('roomtype_ids',
                                                              '=?', rec.id)])
            if used_property:
                rec.is_used = True
            else:
                rec.is_used = False

    @api.onchange('code')
    def onchange_code(self):
        for record in self:
            length = 0
            if record.code:
                length = len(record.code)
            if record.env.user.company_id.roomtype_code_len:
                if length > record.env.user.company_id.roomtype_code_len:
                    raise UserError(
                        _("Room Type Code Length must not exceed %s characters."
                          % (record.env.user.company_id.roomtype_code_len)))

    # Compute Total Room with Room Type
    def compute_totalroom(self):
        for rec in self:
            property_id = self._context.get('property_id')
            if property_id:
                property_obj = self.env['hms.property'].search([('id', '=',
                                                                 property_id)])
                room_objs_per_type = property_obj.propertyroom_ids.filtered(
                    lambda x: x.roomtype_id.id == rec.id)
                room_count = len(room_objs_per_type)
            else:
                room_count = 0
            rec.totalroom = room_count

    @api.constrains('color')
    def limit_color_code(self):
        if self.color < 0 or self.color > 11:
            raise ValidationError(_("Color can only be 0 to 11"))

    #Write Function
    def write(self, values):
        res = super(RoomType, self).write(values)

        if 'color' in values.keys():
            rt_avail_objs = self.env['hms.roomtype.available'].search([
                ('ravail_rmty', '=', self.id)
            ])
            for rt_avail in rt_avail_objs:
                rt_avail.update({'color': values.get('color')})
        return res

    # @api.onchange('bed_type')
    # def onchange_beds(self):
    #     if self.bed_type == 'single' or self.bed_type == 'double' or self.bed_type == 'queen':
    #         self.beds = 1
    #     else :
    #         self.beds = 2


class RoomView(models.Model):
    _name = "hms.roomview"
    _description = "Room View"

    is_csv = fields.Boolean(default=False)
    name = fields.Char(string='Room View', required=True, help='Room View')
    roomview_desc = fields.Text(string='Description', help='Description')

    _sql_constraints = [(
        'name_unique', 'UNIQUE(name)',
        'Room view already exists with this name! Room view name must be unique!'
    )]

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.name,
                                                       record.roomview_desc)))
        return result


class RoomFacility(models.Model):
    _name = "hms.room.facility"
    _description = "Room Facility"
    _rec_name = "facilitytype_id"
    _order = 'facilitytype_id'

    propertyroom_id = fields.Many2one("hms.property.room",
                                      string="Property Room",
                                      readonly=True,
                                      help='Property Room')
    sequence = fields.Integer(default=1)
    amenity_ids = fields.Many2many(
        'hms.room.amenity',
        string="Room Facility",
        domain="[('facilitytype_id.id', '=?', facilitytype_id)]",
        required=True)
    facilitytype_id = fields.Many2one('hms.room.facility.type',
                                      string='Facility Type',
                                      required=True,
                                      help='Room Facility Type')
    facility_desc = fields.Text(string="Description", help='Description')


class RoomAmenitiy(models.Model):
    _name = "hms.room.amenity"
    _description = "Room Amenity"

    is_csv = fields.Boolean(default=False)
    facilitytype_id = fields.Many2one('hms.room.facility.type',
                                      string="Facility Type",
                                      required=True,
                                      help='Facility Type')
    name = fields.Char(string="Amenity Name",
                       required=True,
                       help='Amenity Name')
    amenity_desc = fields.Text(string="Descripton", help='Description')


class RoomFacilityType(models.Model):
    _name = "hms.room.facility.type"
    _description = "Room Facility Type"

    is_csv = fields.Boolean(default=False)
    sequence = fields.Integer(default=1)
    facility_type = fields.Char(string="Room Facility Type ",
                                help='Eg. Entertainments.....',
                                required=True,
                                size=3)
    facilitytype_desc = fields.Char(string="Description",
                                    help='Eg.Room Equipment.....',
                                    required=True)

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, "{} ({})".format(record.facilitytype_desc,
                                                    record.facility_type)))
        return res


class PropertyRoom(models.Model):
    _name = "hms.property.room"
    _rec_name = "room_no"
    _description = "Property Room"
    _group = 'roomlocation_id'

    is_hfo = fields.Boolean(default=False)
    is_used = fields.Boolean(default=False,
                             string="Is Used?",
                             compute='check_is_used')
    sequence = fields.Integer(default=1)
    zip_type = fields.Boolean(string="Zip?", default=False)
    is_roomtype_fix = fields.Boolean(string="Fixed Type?",
                                     readonly=False,
                                     related="roomtype_id.fix_type")
    is_propertyroom = fields.Boolean(string='Is Property Room',
                                     compute='_compute_is_propertyroom')
    room_no = fields.Char(string="Room No", required=True, help='Room No')
    property_id = fields.Many2one('hms.property',
                                  string="Property",
                                  readonly=True,
                                  help='Property')
    roomtype_ids = fields.Many2many("hms.roomtype",
                                    related="property_id.roomtype_ids")
    roomtype_id = fields.Many2one('hms.roomtype',
                                  string="Room Type",
                                  domain="[('id', '=?', roomtype_ids)]",
                                  required=True,
                                  help='Room Type')
    roomview_ids = fields.Many2many('hms.roomview',
                                    string="Room View Code",
                                    help='Room View Code')
    building_ids = fields.Many2many("hms.building",
                                    related="property_id.building_ids")
    building_id = fields.Many2one('hms.building',
                                  string="Room Building",
                                  domain="[('id', '=?', building_ids)]",
                                  required=True,
                                  help='Room Building')
    location_ids = fields.Many2many('hms.roomlocation',
                                    related="building_id.location_ids")
    roomlocation_id = fields.Many2one('hms.roomlocation',
                                      string="Location",
                                      required=True,
                                      domain="[('id', '=?', location_ids)]",
                                      help='Location')
    facility_ids = fields.One2many('hms.room.facility',
                                   'propertyroom_id',
                                   string="Room Facility",
                                   required=True,
                                   help='Room Facility')
    room_bedqty = fields.Integer(string="Number of Beds",
                                 required=True,
                                 size=2,
                                 default=1,
                                 help='Number of Beds')
    room_size = fields.Char(string="Room Size", help='Room Size')
    room_extension = fields.Char(string="Room Extension",
                                 help='Room Extension')
    room_img = fields.Binary(string="Image",
                             attachment=True,
                             store=True,
                             help='Image')
    room_desc = fields.Text(string="Description", help='Desription')
    room_connect = fields.Char(string="Connecting Room",
                               help='Connecting Room')
    room_fostatus = fields.Char(string="FO Room Status",
                                size=2,
                                default='VC',
                                invisible=True,
                                help='FO Room Status')
    room_hkstatus = fields.Char(string="HK Room Status",
                                size=2,
                                default='VC',
                                invisible=True,
                                help='HK Room Status')
    room_status = fields.Char(string="Room Status",
                              size=2,
                              default='CL',
                              invisible=True,
                              help='Room Status')
    bedtype_ids = fields.Many2many('hms.bedtype',
                                   related="roomtype_id.bed_type")
    bedtype_id = fields.Many2one('hms.bedtype',
                                 domain="[('id', '=?', bedtype_ids)]",
                                 help='Bed Type')
    no_of_pax = fields.Integer(string="Allow Pax", default=2, help='Allow Pax')
    room_reservation_line_ids = fields.One2many('hms.reservation.line',
                                                'room_no',
                                                help='Room No')

    _sql_constraints = [
        ('room_no_unique', 'UNIQUE(property_id, room_no)',
         'Room number already exists! Room number must be unique!')
    ]

    @api.depends('room_no')
    def check_is_used(self):
        for rec in self:
            used_in_reservation = self.env['hms.reservation.line'].search([
                ('property_id', '=', rec.property_id.id),
                ('room_no', '=', rec.id)
            ])
            if used_in_reservation:
                rec.is_used = True
            else:
                rec.is_used = False

    # Check HFO Room
    @api.onchange('roomtype_id', 'room_no')
    @api.constrains('roomtype_id', 'room_no')
    def _check_hfo_roomno(self):
        for record in self:
            if record.roomtype_id and record.room_no and record.roomtype_id.code[
                    0] == 'H':
                if record.room_no and not str(record.room_no).isdigit():
                    raise UserError(_("Room Number must be digit"))
                else:
                    if int(record.room_no) < 9000:
                        raise ValidationError(
                            _("Room number with HFO room type must be greather than 9000 "
                              ))

    def _compute_is_propertyroom(self):
        self.is_propertyroom = True

    # def name_get(self):
    #     result = []
    #     for record in self:
    #         result.append(
    #             (record.id, "{} ({})".format(record.room_no,
    #                                          record.roomtype_id.code)))
    #     return result

    # Room location link with Building
    @api.onchange('building_id')
    def onchange_room_location_id(self):
        location = self.env['hms.roomlocation']
        for rec in self:
            rec.roomlocation_id = location

    @api.onchange('roomtype_id')
    def check_is_hfo(self):
        for record in self:
            if record.roomtype_id:
                if record.roomtype_id.code[0] == 'H':
                    record.is_hfo = True

    @api.onchange('roomtype_id')
    def clear_bed_type(self):
        bedtype = self.env['hms.bedtype']
        if self.roomtype_id.fix_type is True:
            self.bedtype_id = bedtype


class MarketSegment(models.Model):
    _name = "hms.marketsegment"
    _description = "Maret Segment"
    _order = 'group_id'

    is_csv = fields.Boolean(default=False)
    sequence = fields.Integer(default=1)
    market_code = fields.Char(string="Market Code",
                              size=3,
                              required=True,
                              help='Market Code')
    market_name = fields.Char(string="Market Name",
                              required=True,
                              help='Market Name')
    group_id = fields.Many2one('hms.marketgroup',
                               string="Group Code",
                               required=True,
                               help='Group Code')
    options = fields.Selection([
        ('W', 'Walk In'),
        ('H', 'House Use'),
        ('C', 'Complimentary'),
        ('O', 'Others'),
    ],
                               string="Options")

    _sql_constraints = [(
        'market_code_unique', 'UNIQUE(market_code)',
        'Market code already exists with this name! Market code must be unique!'
    )]

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.market_name,
                                                       record.market_code)))
        return result


class MarketGroup(models.Model):
    _name = "hms.marketgroup"
    _description = "Market Group"

    is_csv = fields.Boolean(default=False)
    group_code = fields.Char(string="Group Code",
                             help='Eg. COR.....',
                             size=3,
                             required=True)
    group_name = fields.Char(string="Group Name",
                             help='Eg. Corporate.....',
                             required=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.group_name,
                                                       record.group_code)))
        return result


class MarketSource(models.Model):
    _name = "hms.marketsource"
    _description = "Market Source"

    is_csv = fields.Boolean(default=False)
    sequence = fields.Integer(default=1)
    source_code = fields.Char(string="Source Code",
                              size=3,
                              required=True,
                              help='Source Code')
    source_desc = fields.Char(string="Description", help='Description')

    _sql_constraints = [(
        'source_code_unique', 'UNIQUE(source_code)',
        'Source code already exists with this name! Source code must be unique!'
    )]

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.source_desc,
                                                       record.source_code)))
        return result


class SpecialDay(models.Model):
    _name = "hms.specialday"
    _description = "Special Day"

    property_id = fields.Many2one('hms.property',
                                  string="Property",
                                  required=True,
                                  readonly=True,
                                  help='Property')
    special_date = fields.Date(string="Special Date",
                               required=True,
                               help='Special Date')
    special_desc = fields.Char(string="Description", help='Description')

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.special_date,
                                                       record.special_desc)))
        return result

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.special_date,
                                                       record.special_desc)))
        return result


class Weekend(models.Model):
    _name = "hms.weekend"
    _description = "Weekend"

    property_id = fields.Many2one('hms.property',
                                  string="Property",
                                  required=True,
                                  readonly=True)
    monday = fields.Boolean(string="Monday")
    tuesday = fields.Boolean(string="Tuesday")
    wednesday = fields.Boolean(string="Wednesday")
    thursday = fields.Boolean(string="Thursday")
    friday = fields.Boolean(string="Friday", default=True)
    saturday = fields.Boolean(string="Saturday", default=True)
    sunday = fields.Boolean(string="Sunday")

    def name_get(self):
        result = []
        for record in self:
            result.append(
                (record.id, "{} Weekend".format(record.property_id.code)))
        return result


class Package(models.Model):

    _name = "hms.package"
    _rec_name = 'package_name'
    _description = "Package"

    property_id = fields.Many2one('hms.property',
                                  string="Property",
                                  readonly=True,
                                  required=True,
                                  help='Property')
    package_code = fields.Char(string="Package Code",
                               size=4,
                               required=True,
                               help='Package Code')
    package_name = fields.Char(string="Package Name",
                               required=True,
                               help='Package Name')
    package_line_ids = fields.One2many('hms.package.charge.line',
                                       'package_id',
                                       string='Package Charge Lines',
                                       help='Package Charge Lines')

    _sql_constraints = [(
        'package_code_unique', 'UNIQUE(property_id, package_code)',
        'Package code already exists with this name! Package code must be unique!'
    )]

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.package_code,
                                                       record.package_name)))
        return result


class RevenueType(models.Model):
    _name = "hms.revenuetype"
    _description = "Revenue Type"
    _order = "rev_code"

    rev_code = fields.Char(string="Group Code",
                           size=1,
                           required=True,
                           help='Group Code')
    rev_type = fields.Selection(AVAILABLE_REV,
                                string="Revenue Type",
                                required=True,
                                help='Revenue Type')
    revtype_name = fields.Char(string="Revenue", help='Revenue')
    rev_subgroup = fields.Boolean(string="Sub Group", help='Sub Group')
    subgroup_ids = fields.One2many('hms.subgroup',
                                   'revtype_id',
                                   string="Sub Group",
                                   help='Sub Group')
    transaction_id = fields.Many2one('hms.transaction',
                                     'trans_revtype',
                                     help='Transaction Type')

    _sql_constraints = [(
        'rev_code_unique', 'UNIQUE(rev_code)',
        'This code already exists with this name! This Group code must be unique!'
    )]

    # def _compute_revtype_name(self):
    #     # self.revtype_name = dict(AVAILABLE_REV)[self.rev_type]
    #     # self.revtype_name = dict(self._fields['rev_type']._description_selection(self.env))
    #     self.revtype_name = dict(self.fields_get(allfields=['rev_type'])['rev_type']['selection'])['1']

    # dict(self._fields['rev_type']._description_selection(self.env)) --> get description
    # @api.onchange('rev_type')
    # def onchange_revtype_name(self):
    #     for record in self:
    #         for item in VALUES:
    #             if item[0] == self.rev_type:
    #             record.revtype_name = item[1]
    # self.revtype_name= dict(AVAILABLE_REV)[self.rev_type]

    def name_get(self):
        result = []
        for record in self:
            result.append(
                (record.id, "({} {}) {}".format(record.rev_code,
                                                record.rev_type,
                                                record.revtype_name)))
        return result

    @api.onchange('rev_type')
    def onchange_rev_code(self):
        for record in self:
            rev_type = record.rev_type
            if record.rev_type != False:
                record.revtype_name = dict(AVAILABLE_REV)[record.rev_type]
            if rev_type == 'P':
                record.rev_code = '9'
            elif rev_type == 'N':
                record.rev_code = '8'

    @api.constrains('rev_code', 'rev_type')
    def _check_rev_code(self):
        for record in self:
            rev_code = record.rev_code
            rev_type = record.rev_type
            if rev_code and not str(rev_code).isdigit():
                raise UserError(_("Transaction code must be digit"))
            else:
                if rev_code == '0':
                    raise UserError(_("This code not start with '0'"))
                else:
                    if rev_type == 'P':
                        if int(rev_code) != 9:
                            raise UserError(_("Payment code must be 9 "))
                    elif rev_type == 'N':
                        if int(rev_code) != 8:
                            raise UserError(_("Non Revenue code must be 8"))
                    elif rev_type != 'P' and rev_type != 'N':
                        if int(rev_code) == 8 or int(rev_code) == 9:
                            raise UserError(_("Revenue code must be 1 ~ 7 "))


# Revenue Sub Group
class SubGroup(models.Model):
    _name = "hms.subgroup"
    _description = "Revenue Sub Group"
    _order = "property_id, sub_group"

    property_ids = fields.Many2many('hms.property',
                                    related="user_id.property_id")
    property_id = fields.Many2one('hms.property',
                                  string="Property",
                                  domain="[('id', '=?', property_ids)]")
    user_id = fields.Many2one('res.users',
                              string='Salesperson',
                              default=lambda self: self.env.uid)
    revtype_id = fields.Many2one('hms.revenuetype',
                                 string="Revenue Type",
                                 domain="[('rev_subgroup', '=?', True)]",
                                 required=True)
    sub_group = fields.Char(string="Sub Group Code", size=1, required=True)
    sub_desc = fields.Char(string="Description", required=True)
    transsub_id = fields.Many2one('hms.transaction', 'subgroup_id')

    _sql_constraints = [(
        'sub_group_unique', 'UNIQUE(property_id, revtype_id, sub_group)',
        'This Sub Group code already exists with this name! This code must be unique!'
    )]

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "({}) {}".format(record.sub_group,
                                                       record.sub_desc)))
        return result

    # @api.onchange('property_ids')
    # def default_get_property_id(self):
    #     if self.property_ids:
    #         if len(self.property_ids) >= 1:
    #             self.property_id = self.property_ids[0]._origin.id
    #     else:
    #         return {
    #             'warning': {
    #                 'title': _('No Property Permission'),
    #                 'message':
    #                 _("Please Select Property in User Setting First!")
    #             }
    #         }

    @api.constrains('sub_group')
    def _check_sub_group(self):
        for record in self:
            sub_code = record.sub_group
            if sub_code and not str(sub_code).isdigit():
                raise UserError(_("Transaction code must be digit"))


# Transaction
class Transaction(models.Model):
    _name = "hms.transaction"
    _description = "Transaction"
    _order = 'trans_code'

    property_id = fields.Many2one('hms.property',
                                  string="Property",
                                  required=True,
                                  readonly=True,
                                  help='Property')
    revtype_id = fields.Many2one('hms.revenuetype',
                                 string="Revenue Type",
                                 required=True)
    revtype_name = fields.Char(String="Revenue Type", help='Revenue Type')
    revsub_active = fields.Boolean(string="SubGroup")
    trans_ptype = fields.Selection(AVAILABLE_PAY,
                                   string="Pay Type",
                                   help='Pay Type')
    subgroup_ids = fields.One2many('hms.subgroup',
                                   related="property_id.subgroup_ids")
    subgroup_id = fields.Many2one(
        'hms.subgroup',
        domain="[('id', '=?', subgroup_ids), ('revtype_id', '=', revtype_id)]",
        string="Sub Group",
        help='Sub Group')
    subgroup_name = fields.Char(string="Group Name",
                                readonly=True,
                                store=True,
                                help='Group Name')
    trans_code = fields.Char(string="Transaction Code",
                             size=4,
                             required=True,
                             index=True,
                             help='Transaction Code')
    trans_name = fields.Char(string="Transaction Name",
                             required=True,
                             help='Transaction Name')
    trans_unitprice = fields.Float(string="Unit Price",
                                   required=True,
                                   help='Unit Price')
    trans_utilities = fields.Selection([
        ('Y', 'Yes'),
        ('N', 'No'),
    ],
                                       string="Utilities")
    trans_svc = fields.Boolean(string="Service Charge")
    trans_tax = fields.Boolean(string="Tax")
    trans_internal = fields.Boolean(string="Internal Use")
    trans_minus = fields.Boolean(string="Minus Nature")
    trans_type = fields.Selection([
        ('R', 'Revenue'),
        ('S', 'Service'),
        ('V', 'Tax'),
    ],
                                  string="Transaction Type")
    root_id = fields.Many2one('hms.transaction.root',
                              compute='_compute_transaction_root',
                              store=True)
    allowed_pkg = fields.Boolean(string="Allow Package?")
    product_id = fields.Many2one('product.product',
                                 string="Product",
                                 readonly=True)

    _sql_constraints = [(
        'trans_code_unique', 'UNIQUE(property_id, trans_code)',
        'Transaction code already exists with this name! Transaction code must be unique!'
    )]

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "({}) {}".format(record.trans_code,
                                                       record.trans_name)))
        return result

    def create_product_template(self, transaction_id):
        res = transaction_id
        prodcut_name = product_id = prod_ids = prod_id = product_tmp_id = None
        ref_code = ''
        prodcut_name = res.subgroup_name
        if res.subgroup_id:
            ref_code = res.revtype_id.rev_code + res.subgroup_id.sub_group
        else:
            ref_code = res.revtype_id.rev_code
        prod_ids = self.env['product.template'].search([
            ('name', '=', prodcut_name),
            ('company_id', '=', res.property_id.company_id.id)
        ])
        prod_id = self.env['product.product'].search([('product_tmpl_id', '=',
                                                       prod_ids.id)])
        if not prod_ids:
            val = {
                'name': prodcut_name,
                'sale_ok': True,
                'taxes_id': [(4, res.property_id.sale_tax_id.id)],
                'company_id': res.property_id.company_id.id,
                'default_code': ref_code,
            }
            product_tmp_id = self.env['product.template'].create(val)
            product_tmp_ids = self.env['product.product'].search([
                ('product_tmpl_id', '=', product_tmp_id.id)
            ])
            if not product_tmp_ids:
                product_id = self.env['product.product'].create(
                    {'product_tmpl_id': product_tmp_id.id})
            product_id = product_tmp_ids or product_id
        else:
            product_id = prod_id
        return product_id

    @api.model
    def create(self, values):
        res = super(Transaction, self).create(values)
        product_id = None
        product_id = res.create_product_template(res)
        res.product_id = product_id.id
        return res

    # Write Function
    def write(self, values):
        product_id = None
        res = super(Transaction, self).write(values)
        if 'revtype_id' in values.keys() or 'subgroup_id' in values.keys():
            product_id = self.create_product_template(self)
            self.product_id = product_id.id
        return res

    @api.onchange('revtype_id')
    def onchange_revtype_name(self):
        for record in self:
            subgroup_list = []
            domain = {}
            revtype_id = record.revtype_id
            record.revtype_name = revtype_id.revtype_name
            record.revsub_active = revtype_id.rev_subgroup
            if (record.revsub_active is False):
                record.subgroup_name = revtype_id.revtype_name
            else:
                if (record.revtype_id.subgroup_ids):
                    for subgroup in record.revtype_id.subgroup_ids:
                        if (subgroup.property_id == record.property_id):
                            subgroup_list.append(subgroup.id)
                    domain = {'subgroup_id': [('id', 'in', subgroup_list)]}
                    return {'domain': domain}

    # @api.onchange('revtype_id', 'subgroup_id')
    # def onchange_sub_name(self):
    #     for record in self:
    #         subgroup_list = []
    #         domain = {}
    #         revtype_id = record.revtype_id
    #         record.revtype_name  = revtype_id.revtype_name
    #         record.revsub_active = revtype_id.rev_subgroup
    #         if (record.revsub_active is False):
    #             record.subgroup_name= revtype_id.revtype_name
    #         else:
    #             if (record.revtype_id.subgroup_ids):
    #                 for subgroup in record.revtype_id.subgroup_ids:
    #                     if(subgroup.property_id == record.property_id):
    #                         subgroup_list.append(subgroup.id)
    #                 domain = {'subgroup_id': [('id', 'in', subgroup_list)]}
    #                 return {'domain': domain}

    @api.onchange('subgroup_id')
    def onchange_sub_name(self):
        for record in self:
            subgroup_id = record.subgroup_id
            record.subgroup_name = subgroup_id.sub_desc

    # @api.depends('revtype_id','subgroup_id','revsub_active')
    # def _compute_get_subgroup_name(self):
    #     for record in self:
    #         revsub_active = record.revsub_active
    #         if revsub_active is True:
    #             record.subgroup_name = record.subgroup_id.sub_desc
    #         else:
    #             record.subgroup_name = record.revtype_id.revtype_name

    @api.constrains('trans_code')
    def _check_trans_code(self):
        for record in self:
            trans_revtype = record.revtype_id.rev_type
            trans_code = record.trans_code
            rev_code = record.revtype_id.rev_code
            sub_code = record.subgroup_id.sub_group
            if trans_revtype == 'P':
                if trans_code and not str(trans_code).isdigit():
                    raise UserError(_("Transaction code must be digit"))
                else:
                    if int(record.trans_code) < 9000:
                        raise UserError(
                            _("Payment Code must be greather than 9000 "))
            elif trans_revtype != 'P':
                if trans_code and not str(trans_code).isdigit():
                    raise UserError(_("Transaction code must be digit"))
                else:
                    if int(record.trans_code) > 9000:
                        raise UserError(
                            _("Revenue code must be less than 9000 "))
                    else:
                        if int(record.trans_code) < 1000:
                            raise UserError(_("Revenue code must be 4 digits"))
                        else:
                            if record.trans_code[0:1] != rev_code:
                                raise UserError(
                                    _("Transaction code must be started with Revenue Code"
                                      ))
                            else:
                                if sub_code != False:
                                    if record.trans_code[1:2] != sub_code:
                                        raise UserError(
                                            _("Transaction code must be started with Revenue Code + Sub Group Code. Eg. F&B Revenu (2) and BF Revenue (0)-> Transaction code must started with '20'"
                                              ))

    @api.depends('trans_code')
    def _compute_transaction_root(self):
        # this computes the first 2 digits of the transaction.
        # This field should have been a char, but the aim is to use it in a side panel view with hierarchy, and it's only supported by many2one fields so far.
        # So instead, we make it a many2one to a psql view with what we need as records.
        for record in self:
            record.root_id = record.trans_code and (
                ord(record.trans_code[0]) * 1000 +
                ord(record.trans_code[1])) or False


# Transaction Root
class TransactionRoot(models.Model):
    _name = 'hms.transaction.root'
    _description = 'Transaction codes first 2 digits'
    _auto = False

    property_id = fields.Many2one('hms.property',
                                  string="Property",
                                  readonly=True)
    name = fields.Char()
    revname = fields.Char()
    parent_id = fields.Many2one('hms.transaction.root',
                                string="Superior Level",
                                help='Superior Level')
    group = fields.Many2one('hms.subgroup')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
            SELECT DISTINCT ASCII(trans_code) * 1000 + ASCII(SUBSTRING(trans_code,2,1)) AS id,
                   property_id As property_id,
                   LEFT(trans_code,2) AS name,
                   subgroup_name as revname,
                   ASCII(trans_code) AS parent_id,
                   subgroup_id as group
            FROM hms_transaction WHERE trans_code IS NOT NULL
            UNION ALL
            SELECT DISTINCT ASCII(trans_code) AS id,
                   property_id As property_id,
                   LEFT(trans_code,1) AS name,
                   revtype_name as revname,
                   NULL::int AS parent_id,
                   subgroup_id as group
            FROM hms_transaction WHERE trans_code IS NOT NULL
            )''' % (self._table, ))

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "({}) {}".format(record.name,
                                                       record.revname)))
        return result


# Reservation Type
class RsvnType(models.Model):
    _name = "hms.rsvntype"
    _description = "Reservation Type"
    _rec_name = "rsvn_name"

    is_csv = fields.Boolean(default=False)
    rsvn_name = fields.Char(string="Reservation Type", size=30, required=True)
    rsvn_options = fields.Selection([
        ('CF', 'Confirmed'),
        ('UC', 'Unconfirmed'),
    ],
                                    string="Options",
                                    required=True)


#Reservation Status
class RsvnStatus(models.Model):
    _name = "hms.rsvnstatus"
    _description = "Reservation Status"

    is_csv = fields.Boolean(default=False)
    rsvn_code = fields.Char(string="Reservation Status", size=3, required=True)
    rsvn_status = fields.Char(string="Description", required=True)
    rsvntype_id = fields.Many2one('hms.rsvntype',
                                  string="Reservation Type",
                                  required=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "({}) {}".format(record.rsvn_code,
                                                       record.rsvn_status)))
        return result


#Credit Limit
class CreditLimit(models.Model):
    _name = "hms.creditlimit"
    _description = "Credit Limit"
    _group = 'payment_type'

    property_id = fields.Many2one('hms.property',
                                  string="Property",
                                  required=True,
                                  readonly=True,
                                  help='Property')
    payment_type = fields.Selection(AVAILABLE_PAY,
                                    string="Payment Type",
                                    required=True,
                                    help='Payment Type')
    crd_startdate = fields.Date(string="Start Date",
                                required=True,
                                help='Start Date')
    crd_enddate = fields.Date(string="End Date",
                              required=True,
                              help='End Date')  #compute="get_end_date",
    crd_limit = fields.Float(string="Credit Limit", help='Credit Limit')

    def name_get(self):
        result = []
        for record in self:
            result.append(
                (record.id, "{} ({}-{})".format(record.crd_limit,
                                                record.crd_startdate,
                                                record.crd_enddate)))
        return result

    def name_get(self):
        result = []
        for record in self:
            result.append(
                (record.id, "{} ({}-{})".format(record.crd_limit,
                                                record.crd_startdate,
                                                record.crd_enddate)))
        return result

    @api.onchange('crd_startdate', 'crd_enddate')
    @api.constrains('crd_startdate', 'crd_enddate')
    def get_two_date_comp(self):
        start_date = self.crd_startdate
        end_date = self.crd_enddate
        if start_date and end_date and start_date > end_date:
            raise ValidationError("End Date cannot be set before Start Date.")

    @api.onchange('payment_type', 'crd_enddate')
    def get_end_date(self):
        same_payment_objs = self.env['hms.creditlimit'].search([
            ('payment_type', '=', self.payment_type),
            ('property_id.id', '=', self.property_id.id)
        ])
        tmp_end_date = date(1000, 1, 11)
        same_payment = self.env[
            'hms.creditlimit']  # This is Null Object assignment
        for rec in same_payment_objs:
            if rec.crd_enddate > tmp_end_date:
                tmp_end_date = rec.crd_enddate
                same_payment = rec
            if same_payment:
                self.crd_startdate = same_payment.crd_enddate + timedelta(
                    days=1)

    # @api.onchange('payment_type','crd_enddate')
    # def get_end_date(self):
    #     same_payment_objs = self.env['hms.creditlimit'].search([('payment_type','=',self.payment_type)])
    #     tmp_end_date = datetime.date(1000, 1, 11)
    #     same_payment = self.env['hms.creditlimit'] # This is Null Object assignment
    #     for rec in same_payment_objs:
    #         if rec.crd_enddate > tmp_end_date:
    #             tmp_end_date = rec.crd_enddate
    #             same_payment = rec
    #         if same_payment:
    #             self.crd_startdate = same_payment.crd_enddate + timedelta(days = 1)
