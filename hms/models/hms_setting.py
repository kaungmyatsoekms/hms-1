from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules import get_module_resource
#from odoo.tools import image_colorize, image_resize_image_big
from odoo.tools import *
import base64
import datetime


class Bank(models.Model):
    _inherit = 'res.bank'

    property_id = fields.Many2one('property.property', string="Property", required=True, readonly=True)
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

