from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError


# Cashier Transaction
class HMSCashierFolio(models.Model):
    _name = "hms.cashier.folio"
    _description = "Cashier Transaction"
    _order = 'sequence, name'

    sequence = fields.Integer("Sequence")
    active = fields.Boolean("Active", default=True)
    reservation_line_id = fields.Many2one("hms.reservation.line", store=True)
    # room_no = fields.Many2one('Room No')
    transaction_date = fields.Date("Date")
    transaction_time = fields.Datetime("Time", help='Transaction Time')
    transaction_id = fields.Char("Transaction")


# Cashier Transaction
class HMSCashierFolioLine(models.Model):
    _name = "hms.cashier.folio.line"
    _description = "Cashier Transaction"
    _order = 'sequence, name'

    sequence = fields.Integer("Sequence")
    name = fields.Char("Name")
    active = fields.Boolean("Active", default=True)
    reservation_line_id = fields.Many2one("hms.reservation.line", store=True)
    transaction_date = fields.Date("Date")
    transaction_time = fields.Datetime("Time", help='Transaction Time')
    transaction_id = fields.Char("Transaction")
