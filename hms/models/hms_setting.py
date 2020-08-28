from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules import get_module_resource
#from odoo.tools import image_colorize, image_resize_image_big
from odoo.tools import *
import base64
from datetime import datetime
from odoo.osv import expression
import logging
_logger = logging.getLogger(__name__)


class Country(models.Model):
    _inherit = "res.country"

    code = fields.Char(
        string='Country Code',
        size=3,
        help=
        'The ISO country code in three chars. \nYou can use this field for quick search.'
    )

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.name,
                                                       record.code)))
        return result


class Bank(models.Model):
    _inherit = 'res.bank'

    property_id = fields.Many2one('hms.property',
                                  string="Property",
                                  required=True,
                                  readonly=True)
    logo = fields.Binary(string='Logo', attachment=True, store=True)
    bic = fields.Char('Switch Code',
                      index=True,
                      track_visibility=True,
                      help="Sometimes called BIC or Swift.")
    branch = fields.Char("Branch Name",
                         index=True,
                         help="Sometimes called BIC or Swift.")

    _sql_constraints = [('name_unique', 'unique(name)',
                         'Your name is exiting in the database.')]

    def name_get(self):
        result = []
        for record in self:
            result.append(
                (record.id, "{} ({})({})".format(record.name, record.branch,
                                                 record.bic)))
        return result


class HMSCity(models.Model):
    _name = "hms.city"
    _description = "City"
    _order = "code,name"

    state_id = fields.Many2one("res.country.state",
                               "State Name",
                               required=True,
                               track_visibility=True)
    name = fields.Char("City Name", required=True, track_visibility=True)
    code = fields.Char("City Code", required=True, track_visibility=True)

    _sql_constraints = [('code_unique', 'unique(code)',
                         'City Code is already existed.')]

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.name,
                                                       record.code)))
        return result


class HMSTownship(models.Model):
    _name = "hms.township"
    _description = "Township"
    _order = "code,name"

    name = fields.Char("Name", required=True, track_visibility=True)
    code = fields.Char("Code", required=True, track_visibility=True)
    city_id = fields.Many2one("hms.city",
                              "City",
                              ondelete='cascade',
                              required=True,
                              track_visibility=True)
    _sql_constraints = [('code_unique', 'unique(code)',
                         'Township Code is already existed.')]

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{}".format(record.name)))
        return result


class HMSCountry(models.Model):
    _name = "hms.country"
    _description = "Country"

    name = fields.Char("Country Name", required=True, track_visibility=True)
    code = fields.Char("Country Code",
                       size=3,
                       required=True,
                       track_visibility=True)
    _sql_constraints = [('code_unique', 'unique(code)',
                         'Country Code is already existed.')]

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.name,
                                                       record.code)))
        return result


class Nationality(models.Model):
    _description = "Country state"
    _name = 'hms.nationality'
    _order = 'code'

    name = fields.Char(
        string='Nationality Name',
        required=True,
        help=
        'Administrative divisions of a country. E.g. Fed. State, Departement, Canton'
    )
    code = fields.Char(string='Nationality Code',
                       help='The nationality code.',
                       required=True,
                       size=3)

    _sql_constraints = [('name_code_uniq', 'unique(code)',
                         'The code of the state must be unique by country !')]

    @api.model
    def _name_search(self,
                     name,
                     args=None,
                     operator='ilike',
                     limit=100,
                     name_get_uid=None):
        args = args or []

        if operator == 'ilike' and not (name or '').strip():
            first_domain = []
            domain = []
        else:
            first_domain = [('code', '=ilike', name)]
            domain = [('name', operator, name)]

        first_state_ids = self._search(
            expression.AND([first_domain, args]),
            limit=limit,
            access_rights_uid=name_get_uid) if first_domain else []
        state_ids = first_state_ids + [
            state_id
            for state_id in self._search(expression.AND([domain, args]),
                                         limit=limit,
                                         access_rights_uid=name_get_uid)
            if not state_id in first_state_ids
        ]
        return models.lazy_name_get(
            self.browse(state_ids).with_user(name_get_uid))

        def name_get(self):
            result = []
            for record in self:
                result.append(
                    (record.id, "{} ({})".format(record.name, record.code)))
            return result


class Passport(models.Model):
    _name = "hms.passport"
    _description = "PassPort"

    profile_id = fields.Many2one('res.partner',
                                 string="Profile",
                                 required=True)
    passport = fields.Char(string="Passport", required=True)
    issue_date = fields.Date(string="Issue Date", required=True)
    expire_date = fields.Date(string="Expired Date")
    country_id = fields.Many2one('res.country', string="Country")
    nationality = fields.Many2one('hms.nationality', string="Nationality")
    #image1 = fields.Many2many('ir.attachment', string="Image")
    image1 = fields.Binary(string="Photo 1", attachemtn=True, store=True)
    image2 = fields.Binary(string="Photo 2", attachemtn=True, store=True)
    image3 = fields.Binary(string="Photo 3", attachemtn=True, store=True)
    image4 = fields.Binary(string="Photo 4", attachemtn=True, store=True)
    note = fields.Text(string="Internal Note")
    active = fields.Boolean(string="Active",
                            default=True,
                            track_visibility=True)

    _sql_constraints = [('passport_unique', 'UNIQUE(passport)',
                         'Your passport is exiting in the database.')]

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.profile_id.name,
                                                       record.passport)))
        return result

    # Activate the latest passport
    @api.constrains('active')
    def _change_active_status(self):
        for record in self:
            if record.active:
                record_list = self.env['hms.passport'].search([('id', '!=',
                                                                self.id)])
                record.profile_id.image_1920 = record.image1
                for rec in record_list:
                    rec.active = False

    @api.onchange('issue_date', 'expire_date')
    @api.constrains('issue_date', 'expire_date')
    def get_two_date_comp(self):
        issue_date = self.issue_date
        expire_date = self.expire_date
        if issue_date and expire_date and issue_date > expire_date:
            raise ValidationError("End Date cannot be set before Start Date.")

    @api.onchange('country_id')
    def _change_default_nationality(self):
        for record in self:
            if record.country_id:
                _logger.info(record.country_id)
                record.nationality = self.env['hms.nationality'].search([
                    ('code', '=', record.country_id.code)
                ]).id


class Contract(models.Model):
    _name = "hms.contract"
    _description = "Contract"

    profile_id = fields.Many2one('res.partner',
                                 string="Profile",
                                 required=True)
    name = fields.Char(string="Name", required=True)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    note = fields.Text(string="Internal Note")
    file = fields.Binary(string="File")

    def name_get(self):
        result = []
        for record in self:
            result.append(
                (record.id, "{} ({}-{})".format(record.name, record.start_date,
                                                record.end_date)))
        return result

    @api.onchange('start_date', 'end_date')
    @api.constrains('start_date', 'end_date')
    def get_two_date_comp(self):
        start_date = self.start_date
        end_date = self.end_date
        if start_date and end_date and start_date > end_date:
            raise ValidationError("End Date cannot be set before Start Date.")


class HMSCompanyCategory(models.Model):
    _name = "hms.company.category"
    _description = "Company Category"
    _order = 'ordinal_no,code,name'

    is_csv = fields.Boolean(default=False)
    name = fields.Char("Description", required=True, track_visibility=True)
    # type = fields.Selection(
    #     string = 'Type',
    #     selection=[('guest', 'Guest'), ('company', 'Company'),('group','Group')],
    #      compute='_compute_type',
    #     inverse='_write_type',
    # )
    type = fields.Selection(
        string='Type',
        selection=[('agent', 'Travel Agent'), ('other', 'Other')],
        required=True,
    )
    code = fields.Char("Code", track_visibility=True, size=3)
    ordinal_no = fields.Integer("Ordinal No", track_visibility=True)
    active = fields.Boolean(default=True, track_visibility=True)

    def toggle_active(self):
        for ct in self:
            if not ct.active:
                ct.active = self.active
        super(HMSCompanyCategory, self).toggle_active()

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.name,
                                                       record.code)))
        return result

    # Create Function
    @api.model
    def create(self, values):
        # _logger.info(values)
        res = super(HMSCompanyCategory, self).create(values)
        padding = self.env.user.company_id.cprofile_id_format.format_line_id.filtered(
            lambda x: x.value_type == "digit")
        self.env['ir.sequence'].create({
            'name': res.code,
            'code': res.code,
            'padding': padding.digit_value,
            'company_id': False,
            'use_date_range': True,
        })
        return res

    def unlink(self):
        sequence_objs = self.env['ir.sequence']
        for rec in self:
            sequence_objs += self.env['ir.sequence'].search([('code', '=',
                                                              rec.code)])
        sequence_objs.unlink()
        res = super(HMSCompanyCategory, self).unlink()
        return res


class HMSGuestCategory(models.Model):
    _name = "hms.guest.category"
    _description = "Guest Categorys"
    _order = 'ordinal_no,code,name'

    is_csv = fields.Boolean(default=False)
    name = fields.Char("Description", required=True, track_visibility=True)
    code = fields.Char("Code", track_visibility=True, size=3)
    ordinal_no = fields.Integer("Ordinal No", track_visibility=True)
    active = fields.Boolean(default=True, track_visibility=True)

    def toggle_active(self):
        for ct in self:
            if not ct.active:
                ct.active = self.active
        super(HMSGuestCategory, self).toggle_active()

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.name,
                                                       record.code)))
        return result


class Company(models.Model):
    _inherit = "res.company"
    _description = 'Companies'
    _order = 'sequence, name'

    code = fields.Char(string="Company Code", size=3, required=True)
    city = fields.Many2one("hms.city",
                           "City Name",
                           compute='_compute_address',
                           inverse='_inverse_city',
                           track_visibility=True,
                           ondelete='cascade')
    township = fields.Many2one("hms.township",
                               "Township Name",
                               inverse='_inverse_township',
                               track_visibility=True,
                               ondelete='cascade')
    company_channel_type = fields.Many2one(
        'hms.company.category',
        string="CRM Type",
        track_visibility=True,
    )

    _sql_constraints = [('name_unique', 'unique(name)',
                         'Your name is exiting in the database.')]

    def _get_company_address_fields(self, partner):
        return {
            'street': partner.street,
            'street2': partner.street2,
            'township': partner.township,
            'city': partner.city,
            'zip': partner.zip,
            'state_id': partner.state_id,
            'country_id': partner.country_id,
        }

    def _inverse_township(self):
        for company in self:
            company.partner_id.township = company.township

    @api.model
    def create(self, vals):
        crm_type = vals.get('company_channel_type')
        # crm_type = self.env['hms.company.category'].search([('id','=',crm_type)])
        if not vals.get('favicon'):
            vals['favicon'] = self._get_default_favicon()
        if not vals.get('name') or vals.get('partner_id'):
            self.clear_caches()
            return super(Company, self).create(vals)
        partner = self.env['res.partner'].create({
            'name': vals['name'],
            'is_company': True,
            'image_1920': vals.get('logo'),
            'email': vals.get('email'),
            'phone': vals.get('phone'),
            'website': vals.get('website'),
            'vat': vals.get('vat'),
            'company_channel_type': crm_type,
            'company_type': 'company',
        })
        # compute stored fields, for example address dependent fields
        partner.flush()
        vals['partner_id'] = partner.id
        self.clear_caches()
        company = super(Company, self).create(vals)
        # The write is made on the user to set it automatically in the multi company group.
        self.env.user.write({'company_ids': [(4, company.id)]})

        # Make sure that the selected currency is enabled
        if vals.get('currency_id'):
            currency = self.env['res.currency'].browse(vals['currency_id'])
            if not currency.active:
                currency.write({'active': True})
        return company


# Create Partner Title
class PartnerTitle(models.Model):
    _inherit = 'res.partner.title'
    _order = 'name'
    _description = 'Partner Title'

    gender = fields.Selection(string='Gender',
                              selection=[('male', 'Male'),
                                         ('female', 'Female'),
                                         ('other', 'Other')],
                              track_visibility=True)


# Create Partner
class Partner(models.Model):
    _inherit = "res.partner"

    # def get_property_id(self):
    #     if not self.property_id:
    #         property_id = None
    #         if self.env.user.property_id:
    #             # raise UserError(_("Please set property in user setting."))

    #             property_id = self.env.user.property_id[0]
    #         return property_id or 1

    city = fields.Many2one("hms.city", "City Name", track_visibility=True)
    company_type = fields.Selection(string='Company Type',
                                    selection=[('guest', 'Guest'),
                                               ('person', 'Contact'),
                                               ('group', 'Group'),
                                               ('company', 'Company')],
                                    compute='_compute_company_type',
                                    inverse='_write_company_type',
                                    track_visibility=True)
    # New Field
    dob = fields.Date('Date of Birth')
    child_ids = fields.One2many('res.partner',
                                'parent_id',
                                string='Contacts',
                                track_visibility=True,
                                domain=[('is_company', '!=', True)])
    company_channel_type = fields.Many2one('hms.company.category',
                                           string="CRM Type",
                                           track_visibility=True)
    guest_channel_type = fields.Many2one('hms.guest.category',
                                         string="Guest Type",
                                         track_visibility=True)
    township = fields.Many2one('hms.township',
                               "Township",
                               track_visibility=True)
    property_id = fields.Many2one(
        "hms.property", track_visibility=True)  #default=get_property_id,
    property_ids = fields.Many2many("hms.property", track_visibility=True)
    is_from_hms = fields.Boolean(string="Is from HMS",
                                 default=False,
                                 help="Check if creation is from HMS System")
    is_guest = fields.Boolean(string='Is a Guest',
                              default=False,
                              help="Check if the company type is a Guest")
    is_group = fields.Boolean(string='Is a Group',
                              default=False,
                              help="Check if the company type is a Group")
    is_guest_exists = fields.Boolean(string="Is Guest Exists",
                                     compute='_compute_is_guest_exists')
    first_name = fields.Char(string="First Name",
                             track_visibility=True,
                             store=True)
    middle_name = fields.Char(string="Middle Name", track_visibility=True)
    last_name = fields.Char(string="Last Name", track_visibility=True)
    dob = fields.Date(string="Date of Birth", track_visibility=True)
    nationality_id = fields.Many2one('hms.nationality',
                                     string="Nationality",
                                     track_visibility=True)
    gender = fields.Selection(
        string='Gender',
        selection=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        default='male',
        track_visibility=True,
    )
    nrc_card = fields.Char(string="NRC", track_visibility=True)
    father = fields.Char(string="Father", track_visibility=True)
    passport_id = fields.One2many('hms.passport',
                                  'profile_id',
                                  string="Passport",
                                  track_visibility=True,
                                  context={'active_test': False})
    country_id = fields.Many2one('res.country',
                                 string="Country",
                                 track_visibility=True)
    ratecode_id = fields.Many2one('hms.ratecode.header',
                                  "Rate Code",
                                  track_visibility=True)
    blacklist = fields.Boolean(default=False, track_visibility=True)
    message = fields.Text(string="Message", track_visibility=True)
    group_code = fields.Char(string="Group Code", track_visibility=True)
    group_name = fields.Char(string="Group Name", track_visibility=True)
    contract_ids = fields.One2many('hms.contract',
                                   'profile_id',
                                   string="Contract",
                                   readonly=False,
                                   track_visibility=True)
    ar_no = fields.Char(string="AR NO.")
    profile_no = fields.Char(string="Profile NO.")  # compute="get_profile_no"
    no_of_visit = fields.Integer(string="Number of Visit")
    total_nights = fields.Integer(string="Total Nights")
    room_revenue = fields.Float(string="Room Revenue")
    fb_revenue = fields.Float(string="F&B Revenue")
    ms_revenue = fields.Float(string="MS Revenue")
    allotment_id = fields.Char(striing="Allotment")
    image_1920 = fields.Binary(attachment=True)
    passport_image = fields.Binary(store=True,
                                   attachment=True,
                                   compute='_compute_passport_image')

    def _compute_is_guest_exists(self):
        self.is_guest_exists = True

    # Company Type Radion Button Action
    @api.depends('is_company', 'is_guest', 'is_group')
    def _compute_company_type(self):
        for partner in self:
            if partner.is_company or self._context.get(
                    'default_company_type') == 'company':
                partner.company_type = 'company'
                partner.is_company = True
            elif partner.is_guest or self._context.get(
                    'default_company_type') == 'guest':
                partner.company_type = 'guest'
                partner.is_guest = True
            elif partner.is_group or self._context.get(
                    'default_company_type') == 'group':
                partner.company_type = 'group'
                partner.is_group = True
            else:
                partner.company_type = 'person'

    def _write_company_type(self):
        for partner in self:
            partner.is_company = partner.company_type == 'company'
            partner.is_guest = partner.company_type == 'guest'
            partner.is_group = partner.company_type == 'group'

    @api.onchange('company_type')
    def onchange_company_type(self):
        if self.company_type == 'company':
            self.is_company = True
            self.is_guest = False
            self.is_group = False
        elif self.company_type == 'guest':
            self.is_company = False
            self.is_guest = True
            self.is_group = False
        elif self.company_type == 'group':
            self.is_company = False
            self.is_guest = False
            self.is_group = True
        elif self.company_type == 'person':
            self.is_company = False
            self.is_guest = False
            self.is_group = False

    @api.onchange('first_name', 'middle_name', 'last_name', 'group_code')
    def onchange_name(self):
        firstname = ""
        middlename = ""
        lastname = ""
        group_code = ""
        for record in self:
            if record.first_name:
                firstname = record.first_name + ' '
            if record.middle_name:
                middlename = record.middle_name + ' '
            if record.last_name:
                lastname = record.last_name
            if record.group_code:
                group_code = record.group_code
            record.name = firstname + middlename + lastname + group_code

    @api.onchange('title')
    def onchange_title_gender(self):
        for partner in self:
            if partner.title.gender:
                partner.gender = partner.title.gender
            else:
                partner.gender = 'male'

    # @api.onchange('group_code')
    # def onchange_name(self):
    #     group_code = ""
    #     for record in self:
    #         if record.group_code:
    #             group_code = record.group_code
    #         record.name=group_code

    # Profile No Generated
    def generate_profile_no(self, company_type, property_id, crm_type):
        pf_no = ''

        if company_type == 'guest':
            if self.env.user.company_id.profile_id_format:
                format_ids = self.env['hms.format.detail'].search(
                    [('format_id', '=',
                      self.env.user.company_id.profile_id_format.id)],
                    order='position_order asc')
            val = []
            for ft in format_ids:
                if ft.value_type == 'fix':
                    val.append(ft.fix_value)
                if ft.value_type == 'digit':
                    sequent_ids = self.env['ir.sequence'].search([
                        ('code', '=',
                         self.env.user.company_id.profile_id_format.code)
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
                    next_by_code('guest.format') or 'New'
            # next_by_code(self.env.user.company_id.profile_id_format.code) or 'New'
            pf_no = p_no_pre + p_no

        elif company_type == 'company':
            if self.env.user.company_id.cprofile_id_format:
                format_ids = self.env['hms.format.detail'].search(
                    [('format_id', '=',
                      self.env.user.company_id.cprofile_id_format.id)],
                    order='position_order asc')
            val = []
            for ft in format_ids:
                if ft.value_type == 'dynamic':
                    if crm_type.code and ft.dynamic_value == 'company type code':
                        val.append(crm_type.code)
                if ft.value_type == 'fix':
                    val.append(ft.fix_value)
                if ft.value_type == 'digit':
                    sequent_ids = self.env['ir.sequence'].search([
                        ('code', '=', crm_type.code)
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
                    next_by_code(crm_type.code) or 'New'
            pf_no = p_no_pre + p_no

        elif company_type == 'group':
            if property_id:
                if property_id.gprofile_id_format:
                    format_ids = self.env['hms.format.detail'].search(
                        [('format_id', '=', property_id.gprofile_id_format.id)
                         ],
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
                             property_id.gprofile_id_format.code)
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
                        next_by_code(property_id.code+property_id.gprofile_id_format.code) or 'New'
                pf_no = p_no_pre + p_no
            else:
                raise ValidationError(
                    "Select Property or Create Property First!")

        return pf_no

    # Create Function
    @api.model
    def create(self, values):

        values['is_from_hms'] = True
        company_type = values.get('company_type')
        property_id = values.get('property_id')
        property_id = self.env['hms.property'].search([('id', '=', property_id)
                                                       ])
        crm_type = values.get('company_channel_type')
        crm_type = self.env['hms.company.category'].search([('id', '=',
                                                             crm_type)])

        if company_type == 'company' or company_type == 'guest' or company_type == "group":
            pf_no = self.generate_profile_no(company_type, property_id,
                                             crm_type)

            values.update({'profile_no': pf_no})

        company_objs = self.env['res.company']
        res = super(Partner, self).create(values)
        _logger.info(res)
        if crm_type.type == 'agent':
            company_objs = self.env['res.company'].create({
                'name': res.name,
                'street': res.street,
                'street2': res.street2,
                'zip': res.zip,
                'city': res.city,
                'state_id': res.state_id,
                'bank_ids': res.bank_ids,
                'email': res.email,
                'phone': res.phone,
            })

            company_objs.partner_id.active = False

        user_objs = self.env['res.users']
        if company_type == 'person':

            self.env['res.users'].create({
                'login': res.name,
                'name': res.name,
                'email': res.email,
                # 'company_id' : res.company_id,
                'partner_id': res.id,
            })
            # user_objs.partner_id.active=False

        return res

    # write function
    def write(self, values):
        res = super(Partner, self).write(values)

        if 'company_type' in values.keys(
        ) or 'company_channel_type' in values.keys():
            crm_type = self.company_channel_type
            # company_type = values.get('company_type')
            company_type = self.company_type
            property_id = self.property_id
            pf_no = self.generate_profile_no(company_type, property_id,
                                             crm_type)
            if pf_no:
                #values.update({'profile_no':pf_no})
                self.profile_no = pf_no
        return res


# Crete Currency
class HMSCurrency(models.Model):
    _name = "hms.currency"
    _description = "Currency"

    name = fields.Char("Name", required=True, track_visibility=True)
    symbol = fields.Char("Symbol", required=True, track_visibility=True)
    status = fields.Boolean("Active", track_visibility=True)

    def action_status(self):
        for record in self:
            if record.status is True:
                record.status = False
            else:
                record.status = True


class HMSExcelExtended(models.Model):
    _name = 'hms.excel.extended'
    _description = "Excel Extended"

    excel_file = fields.Binary('Download Report :- ')
    file_name = fields.Char('Excel File', size=64)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    reservation_line_id = fields.Many2one('hms.reservation.line')
    property_id = fields.Many2one('hms.property', string="Property")
    group_id = fields.Many2one('res.partner',
                               string="Group",
                               domain="[('is_group','=',True)]",
                               help='Group')
    service_charge = fields.Monetary(string="Service Charges",
                                     compute='_compute_service_charges',
                                     readonly=True)
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            # seq_date = None
            # if 'date_order' in vals:
            #     seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            # if 'company_id' in vals:
            #     vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
            #         'sale.order', sequence_date=seq_date) or _('New')
            # else:
            #     vals['name'] = self.env['ir.sequence'].next_by_code('sale.order', sequence_date=seq_date) or _('New')

            property_id = vals['property_id']
            property_id = self.env['hms.property'].search([('id', '=', property_id)])

            if self.env.user.company_id.soprofile_id_format:
                format_ids = self.env['hms.format.detail'].search(
                    [('format_id', '=',
                      self.env.user.company_id.soprofile_id_format.id)],
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
                        ('code', '=',
                         self.env.user.company_id.soprofile_id_format.code)
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
            p_no_pre = ''
            if len(val) > 0:
                for l in range(len(val)):
                    p_no_pre += str(val[l])
            p_no = ''
            p_no += self.env['ir.sequence'].\
                    next_by_code(property_id.code + property_id.soprofile_id_format.code) or 'New'
            pf_no = p_no_pre + p_no

            vals['name'] = pf_no

        # Makes sure partner_invoice_id', 'partner_shipping_id' and 'pricelist_id' are defined
        if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id']):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            addr = partner.address_get(['delivery', 'invoice'])
            vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
            vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
            vals['pricelist_id'] = vals.setdefault('pricelist_id', partner.property_product_pricelist and partner.property_product_pricelist.id)
        result = super(SaleOrder, self).create(vals)
        return result

    @api.depends('order_line.svc_amount')
    def _compute_service_charges(self):
        svc = 0.0
        for rec in self.order_line:
            svc += rec.svc_amount
        self.service_charge = svc

    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        # ensure a correct context for the _get_default_journal method and company-dependent fields
        self = self.with_context(default_company_id=self.company_id.id,
                                 force_company=self.company_id.id)
        journal = self.env['account.move'].with_context(
            default_type='out_invoice')._get_default_journal()
        if not journal:
            raise UserError(
                _('Please define an accounting sales journal for the company %s (%s).'
                  ) % (self.company_id.name, self.company_id.id))

        invoice_vals = {
            'property_id':
            self.property_id.id,
            'group_id':
            self.group_id.id,
            'ref':
            self.client_order_ref or '',
            'type':
            'out_invoice',
            'narration':
            self.note,
            'currency_id':
            self.pricelist_id.currency_id.id,
            'campaign_id':
            self.campaign_id.id,
            'medium_id':
            self.medium_id.id,
            'source_id':
            self.source_id.id,
            'invoice_user_id':
            self.user_id and self.user_id.id,
            'team_id':
            self.team_id.id,
            'partner_id':
            self.partner_invoice_id.id,
            'partner_shipping_id':
            self.partner_shipping_id.id,
            'invoice_partner_bank_id':
            self.company_id.partner_id.bank_ids[:1].id,
            'fiscal_position_id':
            self.fiscal_position_id.id
            or self.partner_invoice_id.property_account_position_id.id,
            'journal_id':
            journal.id,  # company comes from the journal
            'invoice_origin':
            self.name,
            'invoice_payment_term_id':
            self.payment_term_id.id,
            'invoice_payment_ref':
            self.reference,
            'transaction_ids': [(6, 0, self.transaction_ids.ids)],
            'invoice_line_ids': [],
        }
        return invoice_vals


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    reservation_line_id = fields.Many2one('hms.reservation.line')
    property_id = fields.Many2one('hms.property', string="Property")
    transaction_id = fields.Many2one(
        'hms.transaction',
        string='Transaction',
        domain="[('property_id', '=?', property_id)]")
    package_id = fields.Many2one('hms.package.header', string='Package')
    transaction_date = fields.Date("Date")
    ref = fields.Char("Reference")
    svc_amount = fields.Monetary(string='Service Charge',
                                 store=True,
                                 readonly=True)
    subtotal_wo_svc = fields.Monetary(string='Subtotal Without SVC',
                                      store=True,
                                      readonly=True)
    price_unit = fields.Float('Unit Price',
                              required=True,
                              digits='Product Price',
                              default=0.0)
    price_subtotal = fields.Monetary(string='Subtotal',
                                     compute='_compute_amount',
                                     readonly=True,
                                     store=True)
    price_tax = fields.Float(string='Total Tax',
                             compute='_compute_amount',
                             readonly=True,
                             store=True)
    price_total = fields.Monetary(string='Total',
                                  compute='_compute_amount',
                                  readonly=True,
                                  store=True)

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        # for line in self:
        # price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
        # taxes = line.tax_id.compute_all(
        #     price,
        #     line.order_id.currency_id,
        #     line.product_uom_qty,
        #     product=line.product_id,
        #     partner=line.order_id.partner_shipping_id)
        # line.update({
        #     'price_tax':
        #     sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
        #     'price_total':
        #     taxes['total_included'],
        #     'price_subtotal':
        #     taxes['total_excluded'],
        # })

    def _prepare_invoice_line(self):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'discount': self.discount,
            'price_unit': self.price_unit,
            'tax_ids': [(6, 0, self.tax_id.ids)],
            'analytic_account_id': self.order_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'sale_line_ids': [(4, self.id)],
            # start custom adding new field create
            'property_id': self.property_id.id,
            'partner_id': self.order_partner_id.id,
            'transaction_date': self.transaction_date,
            'transaction_id': self.transaction_id.id,
            'package_id': self.package_id.id,
            'currency_id': self.currency_id.id,
            'tax_amount': self.price_tax,
            'svc_amount': self.svc_amount,
            'subtotal_wo_svc': self.subtotal_wo_svc,
            'price_subtotal': self.price_subtotal,
            'price_total': self.price_total,
        }
        if self.display_type:
            res['account_id'] = False
        return res


class AccountMove(models.Model):
    _inherit = "account.move"
    _description = "Journal Entries"

    property_id = fields.Many2one('hms.property', "Property", readonly=True)
    invoice_sequence_number_next = fields.Char(string='Next Number')
    group_id = fields.Many2one('res.partner',
                               string="Group",
                               domain="[('is_group','=',True)]",
                               help='Group')

    @api.model_create_multi
    def create(self, vals_list):
        # OVERRIDE
        if any('state' in vals and vals.get('state') == 'posted'
               for vals in vals_list):
            raise UserError(
                _('You cannot create a move already in the posted state. Please create a draft move and post it after.'
                  ))

        for v in vals_list:
            property_id = v.get('property_id')
            property_id = self.env['hms.property'].search([('id', '=',
                                                            property_id)])

            if self.env.user.company_id.ivprofile_id_format:
                format_ids = self.env['hms.format.detail'].search(
                    [('format_id', '=',
                      self.env.user.company_id.ivprofile_id_format.id)],
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
                        ('code', '=',
                         self.env.user.company_id.ivprofile_id_format.code)
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
            p_no_pre = ''
            if len(val) > 0:
                for l in range(len(val)):
                    p_no_pre += str(val[l])
            p_no = ''
            p_no += self.env['ir.sequence'].\
                    next_by_code(property_id.code + property_id.ivprofile_id_format.code) or 'New'
            pf_no = p_no_pre + p_no

            v['name'] = pf_no

        vals_list = self._move_autocomplete_invoice_lines_create(vals_list)
        return super(AccountMove, self).create(vals_list)

    @api.depends('state', 'journal_id', 'date', 'invoice_date')
    def _compute_invoice_sequence_number_next(self):
        """ computes the prefix of the number that will be assigned to the first invoice/bill/refund of a journal, in order to
        let the user manually change it.
        """
        #Check user group.
        system_user = self.env.is_system()
        if not system_user:
            self.invoice_sequence_number_next_prefix = False
            self.invoice_sequence_number_next = False
            return

        # Check moves being candidates to set a custom number next.
        moves = self.filtered(
            lambda move: move.is_invoice() and move.name == '/')
        if not moves:
            self.invoice_sequence_number_next_prefix = False
            self.invoice_sequence_number_next = False
            return

        treated = self.browse()
        for key, group in groupby(moves,
                                  key=lambda move:
                                  (move.journal_id, move._get_sequence())):
            journal, sequence = key
            domain = [('journal_id', '=', journal.id),
                      ('state', '=', 'posted')]
            if self.ids:
                domain.append(('id', 'not in', self.ids))
            if journal.type == 'sale':
                domain.append(('type', 'in', ('out_invoice', 'out_refund')))
            elif journal.type == 'purchase':
                domain.append(('type', 'in', ('in_invoice', 'in_refund')))
            else:
                continue
            if self.search_count(domain):
                continue

            # for move in group:
            #     sequence_date = move.date or move.invoice_date
            #     prefix, dummy = sequence._get_prefix_suffix(date=sequence_date, date_range=sequence_date)
            #     number_next = sequence._get_current_sequence(sequence_date=sequence_date).number_next_actual
            #     move.invoice_sequence_number_next_prefix = prefix
            #     move.invoice_sequence_number_next = '%%0%sd' % sequence.padding % number_next
            #     treated |= move
        remaining = (self - treated)
        remaining.invoice_sequence_number_next_prefix = False
        remaining.invoice_sequence_number_next = False

    @api.constrains('name', 'journal_id', 'state')
    def _check_unique_sequence_number(self):
        moves = self.filtered(lambda move: move.state == 'posted')
        if not moves:
            return

        self.flush()

        # /!\ Computed stored fields are not yet inside the database.
        self._cr.execute('''
            SELECT move2.id
            FROM account_move move
            INNER JOIN account_move move2 ON
                move2.name = move.name
                AND move2.journal_id = move.journal_id
                AND move2.type = move.type
                AND move2.id != move.id
            WHERE move.id IN %s AND move2.state = 'posted'
        ''', [tuple(moves.ids)])
        res = self._cr.fetchone()
        # if res:
        #     raise ValidationError(_('Posted journal entry must have an unique sequence number per company.'))


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    property_id = fields.Many2one('hms.property', "Property", readonly=True)
    transaction_id = fields.Many2one(
        'hms.transaction',
        string='Transaction',
        domain="[('property_id', '=?', property_id)]")
    package_id = fields.Many2one('hms.package.header', string='Package')
    transaction_date = fields.Date("Date")
    tax_amount = fields.Monetary(string='Total Tax', store=True, readonly=True)
    svc_amount = fields.Monetary(string='Service Charge',
                                 store=True,
                                 readonly=True)
    subtotal_wo_svc = fields.Monetary(string='Subtotal Without SVC',
                                      store=True,
                                      readonly=True)

class account_payment(models.Model):
    _inherit = "account.payment"

    def post(self):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconcilable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconcilable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        AccountMove = self.env['account.move'].with_context(default_type='entry')
        for rec in self:

            if rec.state != 'draft':
                raise UserError(_("Only a draft payment can be posted."))

            if any(inv.state != 'posted' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # keep the name in case of a payment reset to draft
            if not rec.name:
                # Use the right sequence to set the name
                if rec.payment_type == 'transfer':
                    sequence_code = 'account.payment.transfer'
                else:
                    if rec.partner_type == 'customer':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.customer.invoice'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.customer.refund'
                    if rec.partner_type == 'supplier':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.supplier.refund'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.supplier.invoice'
                rec.name = self.env['ir.sequence'].next_by_code(sequence_code, sequence_date=rec.payment_date)
                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

            moves = AccountMove.create(rec._prepare_payment_moves())
            moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()

            # Update the state / move before performing any reconciliation.
            move_name = self._get_move_name_transfer_separator().join(moves.mapped('name'))
            rec.write({'state': 'posted', 'move_name': move_name})

            if rec.payment_type in ('inbound', 'outbound'):
                # ==== 'inbound' / 'outbound' ====
                if rec.invoice_ids:
                    (moves[0] + rec.invoice_ids).line_ids \
                        .filtered(lambda line: not line.reconciled and line.account_id == rec.destination_account_id)\
                        .reconcile()
            elif rec.payment_type == 'transfer':
                # ==== 'transfer' ====
                moves.mapped('line_ids')\
                    .filtered(lambda line: line.account_id == rec.company_id.transfer_account_id)\
                    .reconcile()

        return True

    def _prepare_payment_moves(self):
        ''' Prepare the creation of journal entries (account.move) by creating a list of python dictionary to be passed
        to the 'create' method.

        Example 1: outbound with write-off:

        Account             | Debit     | Credit
        ---------------------------------------------------------
        BANK                |   900.0   |
        RECEIVABLE          |           |   1000.0
        WRITE-OFF ACCOUNT   |   100.0   |

        Example 2: internal transfer from BANK to CASH:

        Account             | Debit     | Credit
        ---------------------------------------------------------
        BANK                |           |   1000.0
        TRANSFER            |   1000.0  |
        CASH                |   1000.0  |
        TRANSFER            |           |   1000.0

        :return: A list of Python dictionary to be passed to env['account.move'].create.
        '''
        all_move_vals = []
        for payment in self:
            company_currency = payment.company_id.currency_id
            move_names = payment.move_name.split(payment._get_move_name_transfer_separator()) if payment.move_name else None

            # Compute amounts.
            write_off_amount = payment.payment_difference_handling == 'reconcile' and -payment.payment_difference or 0.0
            if payment.payment_type in ('outbound', 'transfer'):
                counterpart_amount = payment.amount
                liquidity_line_account = payment.journal_id.default_debit_account_id
            else:
                counterpart_amount = -payment.amount
                liquidity_line_account = payment.journal_id.default_credit_account_id

            # Manage currency.
            if payment.currency_id == company_currency:
                # Single-currency.
                balance = counterpart_amount
                write_off_balance = write_off_amount
                counterpart_amount = write_off_amount = 0.0
                currency_id = False
            else:
                # Multi-currencies.
                balance = payment.currency_id._convert(counterpart_amount, company_currency, payment.company_id, payment.payment_date)
                write_off_balance = payment.currency_id._convert(write_off_amount, company_currency, payment.company_id, payment.payment_date)
                currency_id = payment.currency_id.id

            # Manage custom currency on journal for liquidity line.
            if payment.journal_id.currency_id and payment.currency_id != payment.journal_id.currency_id:
                # Custom currency on journal.
                if payment.journal_id.currency_id == company_currency:
                    # Single-currency
                    liquidity_line_currency_id = False
                else:
                    liquidity_line_currency_id = payment.journal_id.currency_id.id
                liquidity_amount = company_currency._convert(
                    balance, payment.journal_id.currency_id, payment.company_id, payment.payment_date)
            else:
                # Use the payment currency.
                liquidity_line_currency_id = currency_id
                liquidity_amount = counterpart_amount

            # Compute 'name' to be used in receivable/payable line.
            rec_pay_line_name = ''
            if payment.payment_type == 'transfer':
                rec_pay_line_name = payment.name
            else:
                if payment.partner_type == 'customer':
                    if payment.payment_type == 'inbound':
                        rec_pay_line_name += _("Customer Payment")
                    elif payment.payment_type == 'outbound':
                        rec_pay_line_name += _("Customer Credit Note")
                elif payment.partner_type == 'supplier':
                    if payment.payment_type == 'inbound':
                        rec_pay_line_name += _("Vendor Credit Note")
                    elif payment.payment_type == 'outbound':
                        rec_pay_line_name += _("Vendor Payment")
                if payment.invoice_ids:
                    rec_pay_line_name += ': %s' % ', '.join(payment.invoice_ids.mapped('name'))

            # Compute 'name' to be used in liquidity line.
            if payment.payment_type == 'transfer':
                liquidity_line_name = _('Transfer to %s') % payment.destination_journal_id.name
            else:
                liquidity_line_name = payment.name

            # ==== 'inbound' / 'outbound' ====

            move_vals = {
                'date': payment.payment_date,
                'ref': payment.communication,
                'journal_id': payment.journal_id.id,
                'currency_id': payment.journal_id.currency_id.id or payment.company_id.currency_id.id,
                'partner_id': payment.partner_id.id,
                'line_ids': [
                    # Receivable / Payable / Transfer line.
                    (0, 0, {
                        'name': rec_pay_line_name,
                        'amount_currency': counterpart_amount + write_off_amount if currency_id else 0.0,
                        'currency_id': currency_id,
                        'debit': balance + write_off_balance > 0.0 and balance + write_off_balance or 0.0,
                        'credit': balance + write_off_balance < 0.0 and -balance - write_off_balance or 0.0,
                        'date_maturity': payment.payment_date,
                        'partner_id': payment.partner_id.commercial_partner_id.id,
                        'account_id': payment.destination_account_id.id,
                        'payment_id': payment.id,
                    }),
                    # Liquidity line.
                    (0, 0, {
                        'name': liquidity_line_name,
                        'amount_currency': -liquidity_amount if liquidity_line_currency_id else 0.0,
                        'currency_id': liquidity_line_currency_id,
                        'debit': balance < 0.0 and -balance or 0.0,
                        'credit': balance > 0.0 and balance or 0.0,
                        'date_maturity': payment.payment_date,
                        'partner_id': payment.partner_id.commercial_partner_id.id,
                        'account_id': liquidity_line_account.id,
                        'payment_id': payment.id,
                    }),
                ],
            }
            if write_off_balance:
                # Write-off line.
                move_vals['line_ids'].append((0, 0, {
                    'name': payment.writeoff_label,
                    'amount_currency': -write_off_amount,
                    'currency_id': currency_id,
                    'debit': write_off_balance < 0.0 and -write_off_balance or 0.0,
                    'credit': write_off_balance > 0.0 and write_off_balance or 0.0,
                    'date_maturity': payment.payment_date,
                    'partner_id': payment.partner_id.commercial_partner_id.id,
                    'account_id': payment.writeoff_account_id.id,
                    'payment_id': payment.id,
                }))

            if move_names:
                move_vals['name'] = move_names[0]

            all_move_vals.append(move_vals)

            # ==== 'transfer' ====
            if payment.payment_type == 'transfer':
                journal = payment.destination_journal_id

                # Manage custom currency on journal for liquidity line.
                if journal.currency_id and payment.currency_id != journal.currency_id:
                    # Custom currency on journal.
                    liquidity_line_currency_id = journal.currency_id.id
                    transfer_amount = company_currency._convert(balance, journal.currency_id, payment.company_id, payment.payment_date)
                else:
                    # Use the payment currency.
                    liquidity_line_currency_id = currency_id
                    transfer_amount = counterpart_amount

                transfer_move_vals = {
                    'date': payment.payment_date,
                    'ref': payment.communication,
                    'partner_id': payment.partner_id.id,
                    'journal_id': payment.destination_journal_id.id,
                    'line_ids': [
                        # Transfer debit line.
                        (0, 0, {
                            'name': payment.name,
                            'amount_currency': -counterpart_amount if currency_id else 0.0,
                            'currency_id': currency_id,
                            'debit': balance < 0.0 and -balance or 0.0,
                            'credit': balance > 0.0 and balance or 0.0,
                            'date_maturity': payment.payment_date,
                            'partner_id': payment.partner_id.commercial_partner_id.id,
                            'account_id': payment.company_id.transfer_account_id.id,
                            'payment_id': payment.id,
                        }),
                        # Liquidity credit line.
                        (0, 0, {
                            'name': _('Transfer from %s') % payment.journal_id.name,
                            'amount_currency': transfer_amount if liquidity_line_currency_id else 0.0,
                            'currency_id': liquidity_line_currency_id,
                            'debit': balance > 0.0 and balance or 0.0,
                            'credit': balance < 0.0 and -balance or 0.0,
                            'date_maturity': payment.payment_date,
                            'partner_id': payment.partner_id.commercial_partner_id.id,
                            'account_id': payment.destination_journal_id.default_credit_account_id.id,
                            'payment_id': payment.id,
                        }),
                    ],
                }

                if move_names and len(move_names) == 2:
                    transfer_move_vals['name'] = move_names[1]

                all_move_vals.append(transfer_move_vals)
        return all_move_vals
