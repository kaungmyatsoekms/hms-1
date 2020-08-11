from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules import get_module_resource
#from odoo.tools import image_colorize, image_resize_image_big
from odoo.tools import *
import base64
import datetime


class HmsFormat(models.Model):
    _name = "hms.format"
    _description = "Property Formats"
    _order = "name"

    name = fields.Char("Name", required=True)
    code = fields.Char("Code")
    sample = fields.Char("Sample",
                         compute='get_sample_format',
                         store=True,
                         readonly=True)
    active = fields.Boolean(default=True)
    format_line_id = fields.One2many("hms.format.detail", "format_id",
                                     "Format Line")

    def name_get(self):
        result = []
        for record in self:
            sample = record.sample
            result.append((record.id, sample))
        return result

    @api.model
    def create(self, values):
        return super(HmsFormat, self).create(values)

    @api.depends('format_line_id')
    def get_sample_format(self):
        for record in self:
            f_val = []
            record.sample = ''
            if record.format_line_id:
                for fl in record.mapped('format_line_id'):
                    if fl.value_type == 'fix' and fl.fix_value:
                        f_val.append(fl.fix_value)
                    if fl.value_type == 'digit' and fl.digit_value:
                        for d in range(fl.digit_value):
                            f_val.append(str('x'))
                    if fl.value_type == 'dynamic' and fl.dynamic_value:
                        f_val.append(fl.dynamic_value)
                    if fl.value_type == 'datetime' and fl.datetime_value:
                        f_val.append(fl.datetime_value)
                if f_val:
                    for sm in range(len(f_val)):
                        record.sample += f_val[sm]

    def toggle_active(self):
        for pt in self:
            if not pt.active:
                pt.active = self.active
        super(HmsFormat, self).toggle_active()

    # @api.model
    # def create(self, values):
    #     # _logger.info(values)
    #     format_id = self.search([('name', '=', values['name'])])
    #     if format_id:
    #         raise UserError(_("%s is already existed" % values['name']))
    #     res = super(HmsFormat, self).create(values)
    #     padding = res.format_line_id.filtered(lambda x: x.value_type=="digit")
    #     self.env['ir.sequence'].create({
    #         'name':res.code,
    #         'code':res.code,
    #         'padding':padding.digit_value,
    #         'company_id':False,
    #         'use_date_range': True,
    #         })
    #     return res

    # @api.model
    # def create(self, values):
    #     format_id = self.search([('name', '=', values['name'])])
    #     if format_id:
    #         raise UserError(_("%s is already existed" % values['name']))
    #     return super(HmsFormat, self).create(values)

    # if 'name' in values:
    #     sample_id = self.search([('name', '=', values['name'])])
    #     if sample_id:
    #         raise UserError(_("%s is already existed" % values['name']))
    # return super(HmsFormat, self).create(values)
    # format_ids = self.search([('name', '=', values['name'])])
    # for format_id in format_ids:
    #     if format_id:
    #         raise UserError(_("%s is already existed" % values['name']))
    # return super(HmsFormat, self).create(values)

    # def write(self, vals):
    #     sample_id = None
    #     if 'name' in vals:
    #         sample_id = self.search([('name', '=', vals['name'])])
    #         if sample_id:
    #             raise UserError(_("%s is already existed" % vals['name']))
    #     return super(HmsFormat, self).write(vals)

    # def unlink(self):
    #     sequence_objs = self.env['ir.sequence']
    #     for rec in self:
    #         sequence_objs += self.env['ir.sequence'].search([('code', '=', rec.code)])
    #     sequence_objs.unlink()
    #     res = super(HmsFormat,self).unlink()
    #     return res


class HmsFormatDetail(models.Model):
    _name = "hms.format.detail"
    _description = "Property Formats Details"
    _order = "position_order"

    @api.depends(
        'fix_value',
        'digit_value',
        'dynamic_value',
        'datetime_value',
    )
    def get_value_type(self):
        for record in self:
            if record.value_type:
                if record.value_type == 'fix':
                    record.value = record.fix_value
                if record.value_type == 'dynamic':
                    record.value = record.dynamic_value
                if record.value_type == 'digit':
                    record.value = record.digit_value
                if record.value_type == 'datetime':
                    record.value = record.datetime_value

    name = fields.Char("Name", default="New")
    format_id = fields.Many2one("hms.format", "Format")
    position_order = fields.Integer("Position Order",
                                    compute='_get_line_numbers',
                                    store=True,
                                    readonly=False)
    value_type = fields.Selection([('fix', "Fix"), ('dynamic', 'Dynamic'),
                                   ('digit', 'Digit'),
                                   ('datetime', 'Datetime')],
                                  string="Type",
                                  default="")
    fix_value = fields.Char("Fixed Value", store=True)
    digit_value = fields.Integer("Digit Value", store=True)
    dynamic_value = fields.Selection(
        [('unit code', 'unit code'), ('property code', 'property code'),
         ('company type code', 'company type code'), ('pos code', 'pos code'),
         ('floor code', 'floor code'), ('floor ref code', 'floor ref code')],
        string="Dynamic Value",
        store=True)
    datetime_value = fields.Selection([('MM', 'MM'), ('MMM', 'MMM'),
                                       ('YY', 'YY'), ('YYYY', 'YYYY')],
                                      string="Date Value",
                                      store=True)
    value = fields.Char("Value", compute='get_value_type')

    def _get_line_numbers(self):
        for record in self:
            for fmt in record.mapped('format_id'):
                line_no = 1
                for line in fmt.format_line_id:
                    line.position_order = line_no
                    line_no += 1

    @api.model
    def default_get(self, fields_list):
        res = super(HmsFormatDetail, self).default_get(fields_list)
        res.update({
            'position_order':
            len(self._context.get('format_line_id', [])) + 1
        })
        return res


class Company(models.Model):
    _inherit = "res.company"

    #Guest Profile ID format
    def _default_profile_id_format(self):
        if not self.profile_id_format:
            return self.env.ref('base.main_company').profile_id_format

    #Company Profile ID Format
    def _default_cprofile_id_format(self):
        if not self.cprofile_id_format:
            return self.env.ref('base.main_company').cprofile_id_format

    #Group Profile ID Format
    def _default_gprofile_id_format(self):
        if not self.gprofile_id_format:
            return self.env.ref('base.main_company').gprofile_id_format

    # Confirm ID Format
    def _default_confirm_id_format(self):
        if not self.confirm_id_format:
            return self.env.ref('base.main_company').confirm_id_format
    
    # Sales Tax ID
    def _default_sale_tax_id(self):
        if not self.sale_tax_id:
            return self.env.ref('base.main_company').sale_tax_id

    def _default_show_line_subtotals_tax_selection(self):
        if not self.show_line_subtotals_tax_selection:
            return self.env.ref('base.main_company').show_line_subtotals_tax_selection

    def _default_service_charge_type(self):
        if not self.service_charge_type:
            return self.env.ref('base.main_company').service_charge_type

    def _default_service_product_id(self):
        if not self.service_product_id:
            return self.env.ref('base.main_company').service_product_id
            

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
    
    scurrency_id = fields.Many2one("res.currency",
                                  "Second Currency",
                                  default=default_get_curency,
                                  readonly=False,
                                  track_visibility=True,
                                  help='Second Currency')

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

    scurrency_id = fields.Many2one("res.currency",
                                   "Second Currency",
                                   default=default_get_curency,
                                   readonly=False,
                                   track_visibility=True,
                                   help='Second Currency')

    property_code_len = fields.Integer("Property Code Length",
                                       default=8,
                                       track_visibility=True)
    location_code_len = fields.Integer('Floor Code Length',
                                       track_visibility=True,
                                       default=2)
    building_code_len = fields.Integer('Building Code Length',
                                       track_visibility=True,
                                       default=3)
    roomtype_code_len = fields.Integer('Room Type Code Length',
                                       track_visibility=True,
                                       default=3)
    confirm_id_format = fields.Many2one('hms.format',
                                        'Confirm No Format',
                                        default=_default_confirm_id_format,
                                        track_visibility=True)
    profile_id_format = fields.Many2one('hms.format',
                                        'Profile ID Format',
                                        default=_default_profile_id_format,
                                        track_visibility=True)
    cprofile_id_format = fields.Many2one('hms.format',
                                         'Company Profile ID Format',
                                         default=_default_cprofile_id_format,
                                         track_visibility=True)
    gprofile_id_format = fields.Many2one('hms.format',
                                         'Group Profile ID Format',
                                         default=_default_gprofile_id_format,
                                         track_visibility=True)

    # Tax
    sale_tax_id = fields.Many2one('account.tax', string="Default Sale Tax", default=_default_sale_tax_id)
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
    show_line_subtotals_tax_selection = fields.Selection([
        ('tax_excluded', 'Tax-Excluded'),
        ('tax_included', 'Tax-Included')], string="Line Subtotals Tax Display",
        required=True, default=_default_show_line_subtotals_tax_selection,
        config_parameter='account.show_line_subtotals_tax_selection')
    # Service Charges
    enable_service_charge = fields.Boolean(string='Service Charges')
    service_charge_type = fields.Selection([('amount', 'Amount'),
                                            ('percentage', 'Percentage')],
                                           string='Type', default=_default_service_charge_type)
    service_charge = fields.Float(string='Service Charge')
    service_product_id = fields.Many2one('product.product', string='Service Product',
                                         domain="[('sale_ok', '=', True),"
                                                "('type', '=', 'service')]", default=_default_service_product_id)

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
                domain = [('sale_ok', '=', True),  ('type', '=', 'service')]
                self.service_product_id = self.env['product.product'].search(domain, limit=1)
            self.service_charge = 10.0
        else:
            self.service_product_id = False
            self.service_charge = 0.0


class ColorAttribute(models.Model):
    _name = "hms.color.attribute"
    _description = "Color Attribute"
    _order = 'sequence, id'

    is_csv = fields.Boolean(default=False)
    name = fields.Char('Attribute', required=True)
    value_ids = fields.One2many('hms.color.attribute.value',
                                'attribute_id',
                                'Values',
                                copy=True)
    sequence = fields.Integer('Sequence',
                              help="Determine the display order",
                              index=True)
    create_variant = fields.Selection(
        [('always', 'Instantly'), ('dynamic', 'Dynamically'),
         ('no_variant', 'Never')],
        default='always',
        string="Variants Creation Mode",
        help=
        """- Instantly: All possible variants are created as soon as the attribute and its values are added to a product.
        - Dynamically: Each variant is created only when its corresponding attributes and values are added to a sales order.
        - Never: Variants are never created for the attribute.
        Note: the variants creation mode cannot be changed once the attribute is used on at least one product.""",
        required=True)


class ColorAttributeValue(models.Model):
    _name = "hms.color.attribute.value"
    _order = 'attribute_id, sequence, id'
    _description = 'Color Attribute Value'

    is_csv = fields.Boolean(default=False)
    name = fields.Char(string='Value', required=True)
    sequence = fields.Integer(string='Sequence',
                              help="Determine the display order",
                              index=True)
    html_color = fields.Char(string="Color")
    attribute_id = fields.Many2one('hms.color.attribute',
                                   string="Attribute",
                                   ondelete='cascade',
                                   index=True)

    _sql_constraints = [(
        'value_company_uniq', 'unique (name, attribute_id)',
        "You cannot create two values with the same name for the same attribute."
    )]


class ReservationFields(models.Model):
    _name = "hms.reservation.fields"
    _description = "Reservation Fields"

    is_csv = fields.Boolean(default=False)
    name = fields.Char("Name", required=True)
    code = fields.Char("Code")
    active = fields.Boolean(default=True)
    sequence = fields.Integer('Sequence',
                              help="Determine the display order",
                              index=True)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def get_company_id(self):
        if not self.company_id:
            return self.env.user.company_id
    
    company_id = fields.Many2one('res.company', default=get_company_id)
    property_code_len = fields.Integer("Property Code Length",
                                       related="company_id.property_code_len",
                                       readonly=False)
    location_code_len = fields.Integer('Floor Code Length',
                                       related="company_id.location_code_len",
                                       readonly=False)
    building_code_len = fields.Integer('Building Code Length',
                                       related="company_id.building_code_len",
                                       readonly=False)
    roomtype_code_len = fields.Integer('Room Type Code Length',
                                       related="company_id.roomtype_code_len",
                                       readonly=False)
    confirm_id_format = fields.Many2one('hms.format',
                                        'Confirm No Format',
                                        related="company_id.confirm_id_format",
                                        track_visibility=True)
    profile_id_format = fields.Many2one('hms.format',
                                        'Guest Profile ID Format',
                                        related="company_id.profile_id_format",
                                        track_visibility=True)
    cprofile_id_format = fields.Many2one(
        'hms.format',
        'Company Profile ID Format',
        related="company_id.cprofile_id_format",
        track_visibility=True)
    gprofile_id_format = fields.Many2one(
        'hms.format',
        'Group Profile ID Format',
        related="company_id.gprofile_id_format",
        track_visibility=True)
    # Tax
    sale_tax_id = fields.Many2one('account.tax', string="Default Sale Tax", related='company_id.account_sale_tax_id', readonly=False)
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
    show_line_subtotals_tax_selection = fields.Selection([
        ('tax_excluded', 'Tax-Excluded'),
        ('tax_included', 'Tax-Included')], string="Line Subtotals Tax Display",
        required=True,  related="company_id.show_line_subtotals_tax_selection",
        config_parameter='account.show_line_subtotals_tax_selection')
    # Service Charges
    enable_service_charge = fields.Boolean(string='Service Charges')
    service_charge_type = fields.Selection([('amount', 'Amount'),
                                            ('percentage', 'Percentage')],
                                           string='Type', related="company_id.service_charge_type")
    service_charge = fields.Float(string='Service Charge')
    service_product_id = fields.Many2one('product.product', string='Service Product',
                                         domain="[('sale_ok', '=', True),"
                                                "('type', '=', 'service')]", related="company_id.service_product_id")
    
    @api.onchange('property_code_len')
    def onchange_property_code_len(self):
        if self.property_code_len:
            self.company_id.property_code_len = self.property_code_len

    @api.onchange('location_code_len')
    def onchange_location_code_len(self):
        if self.location_code_len:
            self.company_id.location_code_len = self.location_code_len

    @api.onchange('building_code_len')
    def onchange_building_code_len(self):
        if self.building_code_len:
            self.company_id.building_code_len = self.building_code_len

    @api.onchange('roomtype_code_len')
    def onchange_roomtype_code_len(self):
        if self.roomtype_code_len:
            self.company_id.roomtype_code_len = self.roomtype_code_len

    @api.onchange('confirm_id_format')
    def onchange_confirm_id_format(self):
        if self.confirm_id_format:
            self.company_id.confirm_id_format = self.confirm_id_format

    @api.onchange('profile_id_format')
    def onchange_profile_id_format(self):
        if self.profile_id_format:
            self.company_id.profile_id_format = self.profile_id_format

    @api.onchange('cprofile_id_format')
    def onchange_cprofile_id_format(self):
        if self.cprofile_id_format:
            self.company_id.cprofile_id_format = self.cprofile_id_format

    @api.onchange('gprofile_id_format')
    def onchange_gprofile_id_format(self):
        if self.gprofile_id_format:
            self.company_id.gprofile_id_format = self.gprofile_id_format

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
                domain = [('sale_ok', '=', True),  ('type', '=', 'service')]
                self.service_product_id = self.env['product.product'].search(domain, limit=1)
            self.service_charge = 10.0
        else:
            self.service_product_id = False
            self.service_charge = 0.0
