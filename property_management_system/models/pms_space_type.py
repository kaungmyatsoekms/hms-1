from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError


class PMSSpaceType(models.Model):
    _name = 'pms.space.type'
    _description = 'Space Type'
    _order = 'ordinal_no,name'

    name = fields.Char("Space Type", required=True, track_visibility=True)
    ordinal_no = fields.Integer("Ordinal No", required=True)
    active = fields.Boolean(default=True)

    @api.multi
    def toggle_active(self):
        for pt in self:
            if not pt.active:
                pt.active = self.active
        super(PMSSpaceType, self).toggle_active()

    @api.model
    def create(self, values):
        equip_id = self.search([('name', '=', values['name'])])
        if equip_id:
            raise UserError(_("%s is already existed" % values['name']))
        return super(PMSSpaceType, self).create(values)

    @api.multi
    def write(self, vals):
        if 'name' in vals:
            equip_id = self.search([('name', '=', vals['name'])])
            if equip_id:
                raise UserError(_("%s is already existed" % vals['name']))
        return super(PMSSpaceType, self).write(vals)
