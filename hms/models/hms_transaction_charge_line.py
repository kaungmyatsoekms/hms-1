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

    property_id = fields.Many2one('property.property', string="Property")
    transaction_id = fields.Many2one(
        'transaction.transaction',
        string='Transaction',
        domain="[('property_id', '=?', property_id)]")
    reservation_line_id = fields.Many2one("hms.reservation.line",
                                          "Reservation",
                                          default=get_reservation_line_id)
    rate = fields.Float("Rate", store=True)
    total_amount = fields.Float("Total")
    active = fields.Boolean(default=True)
    delete = fields.Boolean(default=False)
    package_ids = fields.Many2many(
        'package.header', related="reservation_line_id.package_id.package_ids")
    package_id = fields.Many2one('package.header', string='Package')
    total_room = fields.Integer('Rooms', related="reservation_line_id.rooms")
    transaction_date = fields.Date("Date")
    rate_attribute = fields.Selection(RATE_ATTRIBUTE,
                                      string="Attribute",
                                      index=True,
                                      default=RATE_ATTRIBUTE[0][0])
    ref = fields.Char(string="Reference")

    @api.onchange('package_id')
    def onchange_rate(self):
        for rec in self:
            package_id = rec.package_id
            reservation_line_id = rec.reservation_line_id
            rec.rate = reservation_line_id.rate_calculate(
                package_id, reservation_line_id)
            rec.total_amount = reservation_line_id.total_amount_calculate(
                rec.rate, package_id, reservation_line_id)
