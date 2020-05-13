# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PMSCalculationMethod(models.Model):
    _name = "pms.calculation.method"
    _description = "Calculation Method"
    _order = 'ordinal_no,name'

    ordinal_no = fields.Integer("Order No")
    name = fields.Char("Name")
    active = fields.Boolean("Active")
