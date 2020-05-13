# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError
from odoo.addons.property_management_system.models import api_rauth_config


class PMSFacilities(models.Model):
    _name = 'pms.facilities'
    _description = "Facilities"

    name = fields.Char(default="Utilities No",
                       related='utilities_no.name',
                       readonly=True,
                       store=True,
                       required=True,
                       track_visibility=True)
    utilities_type_id = fields.Many2one('pms.utilities.supply.type',
                                        "Utilities Supply Type",
                                        required=True,
                                        track_visibility=True)
    utilities_no = fields.Many2one("pms.equipment",
                                   "Utilities No",
                                   required=True,
                                   track_visibility=True)
    interface_type = fields.Selection([('auto', 'Auto'), ('manual', 'Manual'),
                                       ('mobile', 'Mobile')],
                                      "Data Interface Type",
                                      track_visibility=True)
    remark = fields.Text("Remark", track_visibility=True)
    status = fields.Boolean("Status",
                            default=False,
                            track_visibility=True,
                            help='Current Status of utilities.')
    facilities_line = fields.One2many("pms.facility.lines",
                                      "facility_id",
                                      "Facility Lines",
                                      track_visibility=True)
    property_id = fields.Many2one("pms.properties",
                                  "Property",
                                  required=True,
                                  track_visibility=True)
    count_unit = fields.Integer("Count Unit", compute="_get_count_unit")
    install_date = fields.Date("Installation Date",
                               track_visibility=True,
                               help='The date of Facility installation date.')
    e_meter_type = fields.Char("E Meter Type",
                               compute="compute_meters",
                               track_visibility=True,
                               help='Type of Electric Meters')
    last_rdate = fields.Date("LMR Date",
                             compute="compute_meters",
                             help='Last Month Reading Date.')
    lmr_rvalue = fields.Char("LMR Value",
                             compute="compute_meters",
                             help='Last Month Reading Value.')
    is_api_post = fields.Boolean("Posted")
    active = fields.Boolean(
        "Active",
        default=True,
        track_visibility=True,
    )
    end_date = fields.Date(
        "End Date",
        track_visibility=True,
    )

    # @api.onchange('utilities_type_id')
    # def onchange_utilities_type_id(self):
    #     parent_id = []
    #     domain = {}
    #     utilities_id = None
    #     if self.utilities_type_id != None:
    #         utilities_ids = self.env['pms.utilities.source.type'].search([
    #             ('utilities_type_id', '=', self.utilities_type_id.id)
    #         ])
    #         for loop in utilities_ids:
    #             parent_id.append(loop.id)
    #         domain = {'source_type_id': [('id', 'in', parent_id)]}
    #     return {'domain': domain}

    @api.multi
    def _get_count_unit(self):
        count = 0
        unit_ids = self.env['pms.space.unit'].search([('facility_line', '=',
                                                       self.id),
                                                      ('active', '=', True)])
        for unit in unit_ids:
            self.count_unit += 1

    @api.multi
    def action_units(self):
        unit_ids = self.env['pms.space.unit'].search([('facility_line', '=',
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

    @api.one
    @api.depends('facilities_line.source_type_id', 'facilities_line.lmr_value',
                 'facilities_line.lmr_date')
    def compute_meters(self):
        ldata = []
        emetertype = lmrvalue = lmrdate = None
        if self.facilities_line:
            if len(self.facilities_line) > 0:
                for line in self.facilities_line:
                    if not line.end_date:
                        ldata.append(line.source_type_id)
                    utiliy_id = self.env['pms.utilities.source.type'].browse(
                        line.source_type_id.id)
                    if emetertype:
                        emetertype += " | " + str(utiliy_id.code)
                        lmrvalue += " | " + str(line.lmr_value)
                    if not emetertype:
                        emetertype = str(utiliy_id.code)
                        lmrvalue = str(line.lmr_value)
                        lmrdate = line.lmr_date
        if emetertype:
            self.e_meter_type = emetertype
        if lmrvalue:
            self.lmr_rvalue = lmrvalue
        if lmrdate:
            self.last_rdate = lmrdate

    def suf_scheduler(self):
        values = self
        property_ids = []
        property_id = self.env['pms.properties'].search([('api_integration',
                                                          '=', True)])
        for pro in property_id:
            property_ids.append(pro.id)
        facility_ids = self.search([('is_api_post', '=', False),
                                    ('property_id', 'in', property_ids)])
        if facility_ids:
            integ_obj = self.env['pms.api.integration'].search([])
            api_line_ids = self.env['pms.api.integration.line'].search([
                ('name', '=', "SpaceUnitFacilities")
            ])
            datas = api_rauth_config.APIData.get_data(facility_ids, values,
                                                      property_id, integ_obj,
                                                      api_line_ids)
            if datas:
                if datas.res:
                    response = json.loads(datas.res)
                    if 'responseStatus' in response:
                        if response['responseStatus']:
                            if 'message' in response:
                                if response['message'] == 'SUCCESS':
                                    for fc in facility_ids:
                                        fc.write({'is_api_post': True})

    @api.model
    def create(self, values):
        epuip_id = self.env['pms.equipment'].search([('id', '=',
                                                      values['utilities_no'])])
        fac_id = self.search([('name', '=', epuip_id.name),
                              ('end_date', '=', False)])
        if fac_id:
            raise UserError(_("%s is already existed" % epuip_id.name))
        id = None
        ldata = []
        emetertype = lmrvalue = lmrdate = None
        if 'facilities_line' in values:
            if len(values['facilities_line']) > 0:
                for line in values['facilities_line']:
                    if not line[2]['end_date']:
                        ldata.append(line[2]['source_type_id'])
                dupes = [x for n, x in enumerate(ldata) if x in ldata[:n]]
                if dupes:
                    raise UserError(_("Utiliteis Source Type is same."))
        if 'end_date' in values:
            if values['end_date']:
                values['active'] = False
        id = super(PMSFacilities, self).create(values)
        if id:
            id.write({'is_api_post': False})
        return id

    @api.multi
    def write(self, values):
        if 'utilities_no' in values:
            epuip_id = self.env['pms.equipment'].search([
                ('id', '=', values['utilities_no'])
            ])
            fac_id = self.search([('name', '=', epuip_id.name)])
            if fac_id:
                raise UserError(_("%s is already existed" % epuip_id.name))
        ldata = []
        emetertype = lmrvalue = utiliy_id = lmrdate = None
        if 'facilities_line' in values:
            if len(values['facilities_line']) > 0:
                for line in values['facilities_line']:
                    if line[2]:
                        if 'source_type_id' in line[2]:
                            ldata.append(line[2]['source_type_id'])
                if self.facilities_line:
                    for fac in self.facilities_line:
                        ldata.append(fac.source_type_id.id)
                dupes = [x for n, x in enumerate(ldata) if x in ldata[:n]]
                if dupes:
                    raise UserError(
                        _("System does not allow same utilities source type for one utilities no."
                          ))
        if 'is_api_post' not in values:
            values['is_api_post'] = False
        if 'end_date' in values:
            if values['end_date']:
                values['active'] = False
        result = super(PMSFacilities, self).write(values)
        return result
