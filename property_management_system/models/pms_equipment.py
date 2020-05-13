# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError


class PMSEquipment(models.Model):
    _name = 'pms.equipment'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Equipments"

    def _get_name(self):
        return self.name

    equipment_type_id = fields.Many2one("pms.equipment.type",
                                        string="Equipment Type",
                                        track_visibility=True,
                                        required=True)
    name = fields.Char("Serial No",
                       required=True,
                       track_visibility=True,
                       help='Serial No of Equipment')
    model = fields.Char("Model",
                        required=True,
                        track_visibility=True,
                        help='Model of Equipment.')
    manufacturer = fields.Char("Manufacturer", track_visibility=True)
    ref_code = fields.Char("Reference Code", track_visibility=True)
    # active = fields.Boolean(default=True, track_visibility=True)
    property_id = fields.Many2one("pms.properties",
                                  "Property",
                                  required=True,
                                  track_visibility=True)
    digit = fields.Integer(
        "Digit",
        track_visibility=True,
        help='The maximun capicity to display on equipment screen(esp. meter)')
    count_facility = fields.Integer("Count Unit",
                                    compute="_get_count_facility")
    roll_over_type = fields.Selection(
        [('normal', 'Normal'), ('kwtomw', 'KW to MW')],
        "Rollover Type",
        help='Which method will be use if equipment roll over.')

    @api.multi
    def _get_count_facility(self):
        count = 0
        unit_ids = self.env['pms.facilities'].search([('utilities_no', '=',
                                                       self.id),
                                                      ('status', '=', True)])
        for unit in unit_ids:
            self.count_facility += 1

    @api.multi
    def action_facilities(self):
        facility_ids = self.env['pms.facilities'].search([
            ('utilities_no', '=', self.id), ('status', '=', True)
        ])

        action = self.env.ref(
            'property_management_system.action_facilities_all').read()[0]
        if len(facility_ids) > 1:
            action['domain'] = [('id', 'in', facility_ids.ids)]
        elif len(facility_ids) == 1:
            action['views'] = [(self.env.ref(
                'property_management_system.view_facilities_form').id, 'form')]
            action['res_id'] = facility_ids.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.model
    def create(self, values):
        equip_id = self.search([('name', '=', values['name'])])
        if equip_id:
            raise UserError(_("%s is already existed" % values['name']))
        return super(PMSEquipment, self).create(values)

    @api.multi
    def write(self, vals):
        if 'name' in vals:
            equip_id = self.search([('name', '=', vals['name'])])
            if equip_id:
                raise UserError(_("%s is already existed" % vals['name']))
        return super(PMSEquipment, self).write(vals)


class PMSEquipmentType(models.Model):
    _name = 'pms.equipment.type'
    _description = 'Equipment Types'

    name = fields.Char("Equipment Type", required=True, track_visibility=True)
    active = fields.Boolean(default=True, track_visibility=True)
    ordinal_no = fields.Integer("Ordinal No",
                                required=True,
                                help='To display order as prefer.')
    # _sql_constraints = [('name_unique', 'unique(name)',
    #                      'Your name is exiting in the database.')]

    @api.model
    def create(self, values):
        equip_type_id = self.search([('name', '=', values['name'])])
        if equip_type_id:
            raise UserError(_("%s is already existed" % values['name']))
        return super(PMSEquipmentType, self).create(values)

    @api.multi
    def write(self, vals):
        if 'name' in vals:
            equip_type_id = self.search([('name', '=', vals['name'])])
            if equip_type_id:
                raise UserError(_("%s is already existed" % vals['name']))
        return super(PMSEquipmentType, self).write(vals)
