from odoo import api, fields, models, tools, _


class PMSGenerateRS(models.TransientModel):
    _name = "pms.generate.rs"
    _description = "Generate Rent Schedule"

    rent_ids = fields.Many2many('pms.rent_schedule',
                                'pms_generate_rent_schedule',
                                'generate_id',
                                'rent_id',
                                string='Generate Rent Schedule')


