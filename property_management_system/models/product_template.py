from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_unit = fields.Boolean("Unit", track_visibility=True)
