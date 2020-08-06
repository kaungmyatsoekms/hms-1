import base64
import logging

from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules import get_module_resource
from odoo.tools import *
from datetime import datetime, date, timedelta

RATE_ATTRIBUTE = [
    ('INR', 'Include in Rate'),
    ('ARS', 'Add Rate Separate Line'),
    ('ARC', 'Add Rate Combined Line'),
    ('SS', 'Sell Separate'),
]


class HMSTransactionChargeLine(models.Model):
    _name = 'hms.room.transaction.charge.line'
    _description = "Room Charges Type"
    _order = 'transaction_date'
    _inherit = ['mail.thread']

    def get_reservation_line_id(self):
        reservation_line = self.env['hms.reservation.line'].browse(
            self._context.get('reservation_line_id', []))
        if reservation_line:
            return reservation_line

    property_id = fields.Many2one('hms.property', string="Property")
    transaction_id = fields.Many2one(
        'hms.transaction',
        string='Transaction',
        domain="[('property_id', '=?', property_id)]")
    reservation_line_id = fields.Many2one("hms.reservation.line",
                                          "Reservation",
                                          default=get_reservation_line_id)
    rate = fields.Float("Rate", store=True)
    total_amount = fields.Float("Total")
    price_subtotal = fields.Monetary(string='Subtotal', store=True, readonly=True,
        currency_field='always_set_currency_id')
    active = fields.Boolean(default=True)
    delete = fields.Boolean(default=False)
    package_ids = fields.Many2many(
        'hms.package.header',
        related="reservation_line_id.package_id.package_ids")
    package_id = fields.Many2one('hms.package.header', string='Package')
    total_room = fields.Integer('Rooms', related="reservation_line_id.rooms")
    transaction_date = fields.Date("Date")
    rate_attribute = fields.Selection(RATE_ATTRIBUTE,
                                      string="Attribute",
                                      index=True,
                                      default=RATE_ATTRIBUTE[0][0])
    ref = fields.Char(string="Reference")
    currency_id = fields.Many2one("res.currency",
                                  "Currency",
                                  required=True,
                                  track_visibility=True)
    always_set_currency_id = fields.Many2one('res.currency', string='Foreign Currency',
        compute='_compute_always_set_currency_id',
        help="Technical field used to compute the monetary field. As currency_id is not a required field, we need to use either the foreign currency, either the company one.")


    def name_get(self):
        result = []
        for record in self:
            result.append((record.id,
                           "{} ({})".format(record.transaction_date,
                                            record.transaction_id.trans_name)))
        return result
        
    # Compute Currency
    @api.depends('currency_id')
    def _compute_always_set_currency_id(self):
        for line in self:
            line.always_set_currency_id = line.currency_id or line.company_currency_id

    @api.onchange('package_id')
    def onchange_rate(self):
        for rec in self:
            package_id = rec.package_id
            reservation_line_id = rec.reservation_line_id
            rec.rate = reservation_line_id.rate_calculate(
                package_id, reservation_line_id)
            rec.total_amount = reservation_line_id.total_amount_calculate(
                rec.rate, package_id, reservation_line_id)
