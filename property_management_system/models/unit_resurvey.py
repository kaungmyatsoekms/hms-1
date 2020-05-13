from odoo import api, fields, models, _


class UnitResurvey(models.Model):
    _name = "unit.resurvey"
    _description = "Unit Resurvey"

    def _default_company_id(self):
        if not self.company_id:
            return self.env.user.company_id

    name = fields.Char("Name", readonly=True, store=True)
    property_id = fields.Many2one("pms.properties", "Property", requried=True)
    resurveyunit_id = fields.Many2one("pms.space.unit",
                                      "Resurvey Unit",
                                      requried=True)
    resunitfloor_id = fields.Many2one("pms.floor",
                                      "Resurvey Unit Floor",
                                      related="resurveyunit_id.floor_id")
    resunitspace_type = fields.Many2one(
        "pms.applicable.space.type",
        "Resurvey Unit Type",
        related="resurveyunit_id.spaceunittype_id",
        readonly=True)
    resunit_area = fields.Float("Resurvey Unit Area",
                                related="resurveyunit_id.area")
    resurvey_date = fields.Date("Resurvey Date", requried=True)
    unactive_date = fields.Date("Unacitve Date", requried=True)
    remark = fields.Text("Remark")
    state = fields.Selection([('draft', 'Draft'), ('resurvey', "Resurvey"),
                              ("done", "Done")],
                             string="Status",
                             default="draft")
    company_id = fields.Many2one("res.company",
                                 "Company",
                                 default=_default_company_id)
    newunit_id = fields.Many2one("pms.space.unit", "New Unit")
    newunit_floor_id = fields.Many2one("pms.floor",
                                       "New Unit Floor",
                                       related="newunit_id.floor_id")
    newunit_space_type_id = fields.Many2one("pms.applicable.space.type",
                                            "New Unit Space Type")
    newunit_area = fields.Float("Area")
    lease_agreement_id = fields.Many2one("pms.lease_agreement",
                                         "Lease Agreement")

    def action_resurvey(self):
        newunit_id = None
        if self.state == 'draft':
            if self.resurveyunit_id.status == 'occupied':
                self.resurveyunit_id.write({
                    'resurvey_date': self.resurvey_date,
                    'end_date': self.unactive_date,
                    'active': False,
                    'config_flag': 'survey'
                })
                default = {
                    'spaceunittype_id': self.resunitspace_type.id,
                    'area': self.resunit_area,
                    'start_date': self.resurvey_date,
                    'end_date': False,
                    'active': True,
                    'config_flag': 'new',
                }
                newunit_id = self.resurveyunit_id.copy(default=default)
            if newunit_id:
                self.update_lease_data()
            self.write({
                'state': 'resurvey',
                'newunit_id': newunit_id.id,
                'newunit_space_type_id': self.resunitspace_type.id,
                'newunit_area': self.resunit_area
            })

    def update_lease_data(self):
        leaseitem_id = None
        leaseitem_obj = self.env['pms.lease_agreement.line']
        leaseitem_id = leaseitem_obj.search([
            ('unit_no', '=', self.resurveyunit_id.id),
            ('state', 'not in', ('BOOKING', 'CANCELLED', 'EXPIRED',
                                 'TERMINATED'))
        ])
        if leaseitem_id:
            leaseitem_id.write({
                'reconfig_flag': 'survey',
                'reconfig_date': self.resurvey_date
            })
            default = {
                'reconfig_flag': 'new',
                'reconfig_date': False,
                'start_date': self.resurvey_date
            }
            leaseitem_id.lease_agreement_id.write({'reconfig_flag': 'survey'})
            self.write(
                {'lease_agreement_id': leaseitem_id.lease_agreement_id.id})
            lease_id = leaseitem_id.copy(default=default)
            if leaseitem_id.applicable_type_line_id:
                for ctype in leaseitem_id.applicable_type_line_id:
                    ctype_end_date = None
                    if leaseitem_id.state == 'NEW':
                        ctype_end_date = leaseitem_id.end_date
                    if leaseitem_id.state == 'EXTENDED':
                        ctype_end_date = leaseitem_id.extend_to
                    ctype.copy(
                        default={
                            'lease_line_id': lease_id.id,
                            'start_date': self.resurvey_date,
                            'end_date': ctype_end_date,
                        })

    def action_done(self):
        if self.lease_agreement_id:
            leaseitem_id = self.lease_agreement_id.lease_agreement_line.search(
                [('unit_no', '=', self.resurveyunit_id.id),
                 ('reconfig_flag', '=', 'survey')])
            rent_ids = None
            for charge in leaseitem_id.applicable_type_line_id:
                if leaseitem_id.state == 'NEW':
                    rent_ids = self.env['pms.rent_schedule'].search([
                        ('unit_no', '=', self.resurveyunit_id.id),
                        ('charge_type', '=', charge.applicable_charge_id.id),
                        ('lease_agreement_line_id', '=', leaseitem_id.id),
                        ('start_date', '>=', self.resurvey_date),
                        ('end_date', '<=', leaseitem_id.end_date)
                    ])
                    new_sch_id = self.env['pms.rent_schedule'].search([
                        ('unit_no', '=', self.resurveyunit_id.id),
                        ('charge_type', '=', charge.applicable_charge_id.id),
                        ('lease_agreement_line_id', '=', leaseitem_id.id),
                        ('start_date', '<', self.unactive_date),
                        ('end_date', '>', self.unactive_date)
                    ])
                    if new_sch_id:
                        new_sch_id.write({'end_date': self.unactive_date})
                if leaseitem_id.state == 'EXTENDED':
                    rent_ids = self.env['pms.rent_schedule'].search([
                        ('unit_no', '=', self.resurveyunit_id.id),
                        ('charge_type', '=', charge.charge_type_id.id),
                        ('lease_agreement_line_id', '=', leaseitem_id.id),
                        ('start_date', '>=', self.resurvey_date),
                        ('end_date', '<=', leaseitem_id.extend_to)
                    ])
                    ext_sch_id = self.env['pms.rent_schedule'].search([
                        ('unit_no', '=', self.resurveyunit_id.id),
                        ('charge_type', '=', charge.applicable_charge_id.id),
                        ('lease_agreement_line_id', '=', leaseitem_id.id),
                        ('start_date', '<', self.unactive_date),
                        ('end_date', '>', self.unactive_date)
                    ])
                    if ext_sch_id:
                        ext_sch_id.write({'end_date': self.unactive_date})
                for rent in rent_ids:
                    rent.write({'active': False})
            self.lease_agreement_id.action_activate()
        self.write({'state': 'done'})

    @api.onchange('newunit_space_type_id')
    def onchange_newunit_space_type_id(self):
        if self.newunit_space_type_id:
            self.newunit_id.write(
                {'spaceunittype_id': self.newunit_space_type_id.id})

    @api.onchange('newunit_area')
    def onchange_newunit_area(self):
        if self.newunit_area:
            self.newunit_id.write({'area': self.newunit_area})

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(
                    force_company=vals['company_id']).next_by_code(
                        'unit.reconfig') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'unit.reconfig') or _('New')
        return super(UnitResurvey, self).create(vals)
