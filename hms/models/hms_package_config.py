import base64
import logging

from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules import get_module_resource
from odoo.tools import *
from datetime import datetime, date, timedelta

POSTING_RYTHMS = [
    ('1', 'Post Every Night'),
    ('2', 'Post on Arrival Night'),
    ('3', 'Post on Last Night'),
    ('4', 'Post Every Night Except Arrival Night'),
    ('5', 'Post Every Night Except Last Night'),
    ('6', 'Post on Certain Nights of the Week'),
    ('7', 'Do Not Post on First and Last Night'),
]

CALCUATION_METHODS = [
    ('FIX', 'Fix Rate'),
    ('PP', 'Per Person'),
    ('PA', 'Per Adult'),
]

RATE_ATTRIBUTE = [
    ('INR', 'Include in Rate'),
    ('ARS', 'Add Rate Separate Line'),
    ('ARC', 'Add Rate Combined Line'),
]


class Package(models.Model):
    _name = "package.header"
    _rec_name = 'package_name'
    _description = "Package"

    active = fields.Boolean(string="Active",
                            default=True,
                            track_visibility=True)
    sequence = fields.Integer(default=1)
    property_id = fields.Many2one('property.property',
                                  string="Property",
                                  readonly=True,
                                  required=True)
    package_code = fields.Char(string="Package Code", size=4, required=True)
    shortcut = fields.Char(string="ShortCut")
    package_name = fields.Char(string="Package Name", required=True)
    start_date = fields.Date(string="Start Date",
                             required=True,
                             help="Start of Package")
    end_date = fields.Date(string="End Date",
                           required=True,
                           help="End of Package")
    forecast_next_day = fields.Boolean(string="Forecast Next Day",
                                       default=False,
                                       track_visibility=True)
    post_next_day = fields.Boolean(string="Post Next Day",
                                   default=False,
                                   track_visibility=True)
    catering = fields.Boolean(string="Catering",
                              default=False,
                              track_visibility=True)
    transaction_id = fields.Many2one(
        'transaction.transaction',
        string='Transaction',
        domain="[('property_id', '=?', property_id)]")
    package_profit = fields.Many2one(
        'transaction.transaction',
        string='Profit',
        domain="[('property_id', '=?', property_id)]")
    package_loss = fields.Many2one(
        'transaction.transaction',
        string='Loss',
        domain="[('property_id', '=?', property_id)]")
    product_item = fields.Char('Product Item')
    include_service = fields.Boolean('Include Service',
                                     track_visibility=True,
                                     related='transaction_id.trans_svc')
    include_tax = fields.Boolean('Include Tax',
                                 track_visibility=True,
                                 related='transaction_id.trans_tax')
    allowance = fields.Boolean(string="Catering",
                               default=False,
                               track_visibility=True)
    valid_eod = fields.Boolean(string="Valid C/O EOD",
                               default=False,
                               track_visibility=True)
    currency_id = fields.Char(string="Currency")
    sell_separate = fields.Boolean(string="Sell Separate",
                                   default=False,
                                   track_visibility=True)
    posting_rythms = fields.Selection(POSTING_RYTHMS,
                                      string='Rating',
                                      index=True,
                                      default=POSTING_RYTHMS[0][0])
    Calculation_method = fields.Selection(CALCUATION_METHODS,
                                          string='Rating',
                                          index=True,
                                          default=CALCUATION_METHODS[0][0])
    Fix_price = fields.Float('Price')
    rate_attribute = fields.Selection(RATE_ATTRIBUTE,
                                      string="Attribute",
                                      index=True,
                                      default=RATE_ATTRIBUTE[0][0])
    package_group_id = fields.Many2one('package.group', string="Package Group")

    _sql_constraints = [(
        'package_code_unique', 'UNIQUE(property_id, package_code)',
        'Package code already exists with this name! Package code must be unique!'
    )]


class PackageGroup(models.Model):
    _name = "package.group"
    _rec_name = 'pkg_group_name'
    _description = "Package Group"

    active = fields.Boolean(string="Active",
                            default=True,
                            track_visibility=True)
    sequence = fields.Integer(default=1)
    property_id = fields.Many2one('property.property',
                                  string="Property",
                                  readonly=True,
                                  required=True)
    pkg_group_code = fields.Char(string="Group Code", size=4, required=True)
    shortcut = fields.Char(string="ShortCut")
    pkg_group_name = fields.Char(string="Group Name", required=True)
    package_id = fields.One2many('package.header',
                                 'package_group_id',
                                 string="Packages")
    transaction_id = fields.Many2one(
        'transaction.transaction',
        string='Transaction',
        domain="[('property_id', '=?', property_id)]")
    include_service = fields.Boolean('Include Service',
                                     track_visibility=True,
                                     related='transaction_id.trans_svc')
    include_tax = fields.Boolean('Include Tax',
                                 track_visibility=True,
                                 related='transaction_id.trans_tax')

    _sql_constraints = [(
        'pkg_group_code_unique', 'UNIQUE(property_id, pkg_group_code)',
        'Package group code already exists with this name! Package group code must be unique!'
    )]
