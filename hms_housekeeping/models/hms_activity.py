# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HMSActivity(models.Model):
    _name = 'hms.activity'
    _description = 'Housekeeping Activity'

    name = fields.Char(string="Name")
    h_id = fields.Many2one(
        'product.product',
        'Product',
        required=True,
        delegate=True,
        ondelete='cascade',
        index=True
    )
    categ_id = fields.Many2one(
        'hms.housekeeping.activity.type',
        string='Category'
    )
