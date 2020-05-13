import json
import base64
from odoo.addons.property_management_system.requests_oauth2 import OAuth2BearerToken
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError
from odoo.addons.property_management_system.models import api_rauth_config


class PMSFloor(models.Model):
    _name = 'pms.floor'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "ZPMS Floor"
    _order = "code,name"

    name = fields.Char("Floor", required=True, track_visibility=True)
    code = fields.Char("Floor Code", required=True, track_visibility=True)
    floor_code_ref = fields.Char("Reference Code", track_visibility=True)
    active = fields.Boolean("Active", default=True, track_visibility=True)
    count_unit = fields.Integer("Count Unit", compute="_get_count_unit")
    property_id = fields.Many2one("pms.properties",
                                  "Property",
                                  index=True,
                                  required=True,
                                  track_visibility=True)
    is_api_post = fields.Boolean("Posted")

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            code = record.code
            result.append((record.id, code))
        return result

    @api.multi
    @api.onchange('code')
    def onchange_code(self):
        length = 0
        if self.code:
            length = len(self.code)
        if self.env.user.company_id.floor_code_len:
            if length > self.env.user.company_id.floor_code_len:
                raise UserError(
                    _("Floor Code Length must not exceed %s characters." %
                      (self.env.user.company_id.floor_code_len)))

    @api.multi
    def toggle_active(self):
        if self.active:
            unit_ids = self.env['pms.space.unit'].search([('floor_id', '=',
                                                           self.id)])
            for unit in unit_ids:
                if unit.active:
                    raise UserError(
                        _("Please Unactive of Space Unit %s with Floor Code (%s) of %s."
                          ) % (unit.name, self.code, self.name))
        for pt in self:
            if not pt.active:
                pt.active = self.active
        super(PMSFloor, self).toggle_active()

    @api.multi
    def _get_count_unit(self):
        count = 0
        unit_ids = self.env['pms.space.unit'].search([('floor_id', '=',
                                                       self.id),
                                                      ('active', '=', True)])
        for unit in unit_ids:
            self.count_unit += 1

    @api.multi
    def action_units(self):
        unit_ids = self.env['pms.space.unit'].search([('floor_id', '=',
                                                       self.id),
                                                      ('active', '=', True)])

        action = self.env.ref(
            'property_management_system.action_space_all').read()[0]
        if len(unit_ids) > 1:
            action['domain'] = [('id', 'in', unit_ids.ids)]
        elif len(unit_ids) == 1:
            action['views'] = [(self.env.ref(
                'property_management_system.view_space_unit_form').id, 'form')]
            action['res_id'] = unit_ids.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.model
    def create(self, values):
        floor_id = None
        floor_id = self.search([('code', '=', values['code']),
                                ('property_id', '=', values['property_id'])])

        if floor_id:
            raise UserError(_("%s is already existed.") % (values['code']))
        id = None
        id = super(PMSFloor, self).create(values)
        if id:
            property_obj = self.env['pms.properties']
            property_id = property_obj.browse(values['property_id'])
            if property_id.api_integration:
                integ_obj = self.env['pms.api.integration'].search([])
                api_line_ids = self.env['pms.api.integration.line'].search([
                    ('name', '=', "Floor")
                ])
                datas = api_rauth_config.APIData.get_data(
                    id, values, property_id, integ_obj, api_line_ids)
                if datas:
                    if datas.res:
                        response = json.loads(datas.res)
                        if 'responseStatus' in response:
                            if response['responseStatus']:
                                if 'message' in response:
                                    if response['message'] == 'SUCCESS':
                                        id.write({'is_api_post': True})
        return id

    @api.multi
    def write(self, vals):
        floor_id = None
        if 'code' in vals and 'property_id' in vals:
            floor_id = self.search([('code', '=', vals['code']),
                                    ('property_id', '=', vals['property_id'])])

            if floor_id:
                raise UserError(_("%s is already existed.") % (values['code']))
        if 'code' in vals and 'property_id' not in vals:
            floor_id = self.search([('code', '=', vals['code']),
                                    ('property_id', '=', self.property_id.name)
                                    ])
            if floor_id:
                raise UserError(_("%s is already existed.") % (vals['code']))
        id = None
        id = super(PMSFloor, self).write(vals)
        if id and self.property_id.api_integration:
            property_id = self.property_id
            integ_obj = self.env['pms.api.integration'].search([])
            api_line_ids = self.env['pms.api.integration.line'].search([
                ('name', '=', "Floor")
            ])
            if 'is_api_post' in vals:
                if vals['is_api_post']:
                    datas = api_rauth_config.APIData.get_data(
                        self, vals, property_id, integ_obj, api_line_ids)
                    if datas:
                        if datas.res:
                            response = json.loads(datas.res)
                            if 'responseStatus' in response:
                                if response['responseStatus']:
                                    if 'message' in response:
                                        if response['message'] == 'SUCCESS':
                                            self.write({'is_api_post': True})
            else:
                datas = api_rauth_config.APIData.get_data(
                    self, vals, property_id, integ_obj, api_line_ids)
                if datas:
                    if datas.res:
                        response = json.loads(datas.res)
                        if 'responseStatus' in response:
                            if response['responseStatus']:
                                if 'message' in response:
                                    if response['message'] == 'SUCCESS':
                                        self.write({'is_api_post': True})
        return id

    @api.multi
    def unlink(self):
        if len(self) > 1:
            for line in self:
                if line.active:
                    unit_ids = self.env['pms.space.unit'].search([
                        ('floor_id', '=', line.id)
                    ])
                    for unit in unit_ids:
                        if unit.active:
                            raise UserError(
                                _("Please Unactive of Space Unit %s with Floor Code (%s) of %s."
                                  ) % (unit.name, line.code, line.name))
        else:
            if self.active:
                unit_ids = self.env['pms.space.unit'].search([('floor_id', '=',
                                                               self.id)])
                for unit in unit_ids:
                    if unit.active:
                        raise UserError(
                            _("Please Unactive of Space Unit %s with Floor Code(%s) of %s."
                              ) % (unit.name, self.code, self.name))
        return super(PMSFloor, self).unlink()

    def floor_scheduler(self):
        values = None
        property_ids = []
        property_id = self.env['pms.properties'].search([('api_integration',
                                                          '=', True)])
        for pro in property_id:
            property_ids.append(pro.id)
        floor_ids = self.search([('is_api_post', '=', False),
                                 ('property_id', 'in', property_ids)])
        if floor_ids:
            integ_obj = self.env['pms.api.integration'].search([])
            api_line_ids = self.env['pms.api.integration.line'].search([
                ('name', '=', "Floor")
            ])
            datas = api_rauth_config.APIData.get_data(floor_ids, values,
                                                      property_id, integ_obj,
                                                      api_line_ids)
            if datas.res:
                response = json.loads(datas.res)
                if 'responseStatus' in response:
                    if response['responseStatus'] == True:
                        if 'message' in response:
                            if response['message'] == 'SUCCESS':
                                for fl in floor_ids:
                                    fl.write({'is_api_post': True})
