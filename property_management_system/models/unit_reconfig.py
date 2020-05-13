from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class UnitReconfig(models.Model):
    _name = "unit.reconfig"
    _description = "Unit Reconfig"

    def _default_company_id(self):
        if not self.company_id:
            return self.env.user.company_id

    name = fields.Char("Name", readonly=True, store=True)
    property_id = fields.Many2one("pms.properties", "Property")
    reconfig_date = fields.Date("Reconfig Date")
    remark = fields.Text("Remark")
    state = fields.Selection([('draft', 'Draft'), ('reconfig', "Reconfig"),
                              ("done", "Done")],
                             string="Status",
                             default="draft")
    unit_expiring_id = fields.One2many("unit.reconfig.expiring",
                                       "unitreconfig_id",
                                       string="Expiring Unit")
    unit_new_id = fields.One2many("unit.reconfig.new", "unitreconfig_id",
                                  "New Unit")
    company_id = fields.Many2one("res.company",
                                 "Company",
                                 default=_default_company_id)
    lease_agreement_id = fields.Many2one("pms.lease_agreement",
                                         "Lease Agreement")

    def action_reconfig(self):
        if self.unit_expiring_id:
            for exp in self.unit_expiring_id:
                unit = exp.unit_id
                end_date = exp.end_date
                self.update_leaseitem(unit, end_date)
        else:
            raise UserError(_("Expiring unit must have."))
        if self.unit_new_id:
            for new in self.unit_new_id:
                unit = new.unit_id
                end_date = new.end_date
                self.insert_newleaseitem(unit, end_date)
        else:
            raise UserError(_("New unit must have."))
        self.write({'state': 'reconfig'})

    def update_leaseitem(self, unit, end_date):
        leaseline_id = None
        leaseline_id = self.env['pms.lease_agreement.line'].search([
            ('unit_no', '=', unit.id),
            ('state', 'not in',
             ['BOOKING', 'CANCELLED', 'EXPIRED', 'TERMINATED'])
        ])
        if leaseline_id:
            leaseline_id.write({
                'reconfig_date': self.reconfig_date,
                'reconfig_flag': 'config'
            })
            unit.write({'config_flag': 'config'})
            self.write({
                'lease_agreement_id':
                leaseline_id.lease_agreement_id.id,
            })

    @api.one
    def insert_newleaseitem(self, unit, end_date):
        leaseline_id = None
        leaseline_obj = self.env['pms.lease_agreement.line']
        leaseline_id = leaseline_obj.search([('unit_no', '=', unit.id)])
        if not leaseline_id:
            exist_unit = None
            if self.unit_expiring_id:
                for unexp in self.unit_expiring_id:
                    exist_unit = unexp.unit_id.id
            leaseline_id = leaseline_obj.search([('unit_no', '=', exist_unit),
                                                 ('state', 'in',
                                                  ['NEW', 'EXTENDED'])])
            if leaseline_id:
                lease_id = leaseline_id.copy(
                    default={
                        'unit_no': unit.id,
                        'start_date': end_date,
                        'reconfig_date': False,
                        'reconfig_flag': 'new',
                    })
                if leaseline_id.applicable_type_line_id:
                    for ctype in leaseline_id.applicable_type_line_id:
                        ctype_end_date = None
                        if leaseline_id.state == 'NEW':
                            ctype_end_date = leaseline_id.end_date
                        if leaseline_id.state == 'EXTENDED':
                            ctype_end_date = leaseline_id.extend_to
                        ctype.copy(
                            default={
                                'lease_line_id': lease_id.id,
                                'start_date': end_date,
                                'end_date': ctype_end_date,
                            })

    def action_done(self):
        if self.lease_agreement_id:
            for lease in self.lease_agreement_id:
                if self.unit_expiring_id:
                    for line in self.unit_expiring_id:
                        unexp = line.unit_id.id
                        lease_exist_id = lease.lease_agreement_line.search([
                            ('unit_no', '=', unexp),
                            ('reconfig_flag', '=', 'config')
                        ])
                        rent_ids = None
                        for charge in lease_exist_id.applicable_type_line_id:
                            if lease_exist_id.state == 'NEW':
                                rent_ids = self.env[
                                    'pms.rent_schedule'].search([
                                        ('unit_no', '=', unexp),
                                        ('charge_type', '=',
                                         charge.applicable_charge_id.id),
                                        ('lease_agreement_line_id', '=',
                                         lease_exist_id.id),
                                        ('start_date', '>=', line.end_date),
                                        ('end_date', '<=',
                                         lease_exist_id.end_date)
                                    ])
                                new_sch_id = self.env[
                                    'pms.rent_schedule'].search([
                                        ('unit_no', '=', unexp),
                                        ('charge_type', '=',
                                         charge.applicable_charge_id.id),
                                        ('lease_agreement_line_id', '=',
                                         lease_exist_id.id),
                                        ('start_date', '<', line.end_date),
                                        ('end_date', '>', line.end_date)
                                    ])
                                if new_sch_id:
                                    new_sch_id.write(
                                        {'end_date': line.end_date})
                            if lease_exist_id.state == 'EXTENDED':
                                rent_ids = self.env[
                                    'pms.rent_schedule'].search([
                                        ('unit_no', '=', unexp),
                                        ('charge_type', '=',
                                         charge.charge_type_id.id),
                                        ('lease_agreement_line_id', '=',
                                         lease_exist_id.id),
                                        ('start_date', '>=', line.end_date),
                                        ('end_date', '<=',
                                         lease_exist_id.extend_to)
                                    ])
                                ext_sch_id = self.env[
                                    'pms.rent_schedule'].search([
                                        ('unit_no', '=', unexp),
                                        ('charge_type', '=',
                                         charge.applicable_charge_id.id),
                                        ('lease_agreement_line_id', '=',
                                         lease_exist_id.id),
                                        ('start_date', '<', line.end_date),
                                        ('end_date', '>', line.end_date)
                                    ])
                                if ext_sch_id:
                                    ext_sch_id.write(
                                        {'end_date': line.end_date})
                            for rent in rent_ids:
                                rent.write({'active': False})
            lease_new_id = None
            if self.unit_new_id:
                for unew in self.unit_new_id:
                    lease_new_id = lease.lease_agreement_line.search([
                        ('unit_no', '=', unew.unit_id.id)
                    ])
                lease_new_id.lease_agreement_id.action_activate()
        self.write({'state': 'done'})

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
        if 'unit_expiring_id' not in vals:
            raise UserError(_("Expiring unit must have."))
        if 'unit_new_id' not in vals:
            raise UserError(_("New unit must have at least one."))
        return super(UnitReconfig, self).create(vals)

    @api.multi
    def unlink(self):
        if self.state in ('reconfig', 'done'):
            raise ValidationError(_("Can delete in only draft. "))
        return super(UnitReconfig, self).unlink()


class UnitReconfigExpiring(models.Model):
    _name = "unit.reconfig.expiring"
    _description = "Unit Reconfig Expiring"

    unit_id = fields.Many2one("pms.space.unit", "Unit")
    floor_id = fields.Many2one("pms.floor",
                               "Floor",
                               related="unit_id.floor_id",
                               readonly=True)
    unit_type_id = fields.Many2one("pms.applicable.space.type",
                                   "Unit Type",
                                   related="unit_id.spaceunittype_id",
                                   readonly=True)
    area = fields.Float("Area", related="unit_id.area", readonly=True)
    end_date = fields.Date("End Date")
    unitreconfig_id = fields.Many2one("unit.reconfig", "Unit Reconfig")

    @api.onchange('unit_id')
    def onchange_unit_id(self):
        units = []
        domain = {}
        lease_id = self.mapped('unitreconfig_id').lease_agreement_id
        if lease_id:
            for line in lease_id:
                for uno in line.lease_agreement_line:
                    units.append(uno.unit_no.id)
            domain = {'unit_id': [('id', 'in', units)]}
        return {'domain': domain}

    @api.multi
    def unlink(self):
        if self.unitreconfig_id:
            if self.unitreconfig_id.state in ('reconfig', 'done'):
                raise ValidationError(_("Can delete in only draft. "))
            return super(UnitReconfigExpiring, self).unlink()


class UnitConfigNew(models.Model):
    _name = "unit.reconfig.new"
    _description = "Unit Reconfig New"

    unit_id = fields.Many2one("pms.space.unit",
                              "Unit",
                              domain=[('status', '=', 'vacant')])
    floor_id = fields.Many2one("pms.floor",
                               "Floor",
                               related="unit_id.floor_id",
                               readonly=True)
    unit_type_id = fields.Many2one("pms.applicable.space.type",
                                   "Unit Type",
                                   related="unit_id.spaceunittype_id",
                                   readonly=True)
    area = fields.Float("Area", related="unit_id.area", readonly=True)
    end_date = fields.Date("End Date")
    unitreconfig_id = fields.Many2one("unit.reconfig", "Unit Reconfig")

    @api.multi
    def unlink(self):
        if self.unitreconfig_id:
            if self.unitreconfig_id.state in ('reconfig', 'done'):
                raise ValidationError(_("Can delete in only draft. "))
            return super(UnitConfigNew, self).unlink()