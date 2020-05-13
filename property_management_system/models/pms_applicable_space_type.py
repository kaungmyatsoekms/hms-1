from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError


class PMSApplicableSpaceType(models.Model):
    _name = 'pms.applicable.space.type'
    _description = 'Applicable Space Type'
    _order = 'ordinal_no,name'

    name = fields.Char("Space Type", required=True, track_visibility=True)
    space_type_id = fields.Many2one("pms.space.type",
                                    "Main Space Type",
                                    required=True)
    chargeable = fields.Boolean("IsChargable", track_visibility=True)
    divisible = fields.Boolean("Manageable", track_visibility=True)
    ordinal_no = fields.Integer("Ordinal No",
                                required=True,
                                help='To display order as prefer')
    active = fields.Boolean(default=True)

    @api.multi
    def toggle_active(self):
        for pt in self:
            if not pt.active:
                pt.active = self.active
        super(PMSTerms, self).toggle_active()

    @api.model
    def create(self, values):
        charge_type_id = self.search([('name', '=', values['name'])])
        if charge_type_id:
            raise UserError(_("%s is already existed" % values['name']))
        return super(PMSApplicableSpaceType, self).create(values)

    @api.multi
    def write(self, vals):
        if 'name' in vals:
            charge_type_id = self.search([('name', '=', vals['name'])])
            if charge_type_id:
                raise UserError(_("%s is already existed" % vals['name']))
        return super(PMSApplicableSpaceType, self).write(vals)