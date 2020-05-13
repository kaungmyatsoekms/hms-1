import json
import datetime
import calendar
from calendar import monthrange
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.addons.property_management_system.models import api_rauth_config


class PMSLeaseAgreement(models.Model):
    _name = 'pms.lease_agreement'
    _inherit = ['mail.thread']
    _description = "Lease Agreements"
    _order = "property_id, company_tanent_id, state, start_date"

    name = fields.Char("Name",
                       default="New",
                       compute="compute_tanent",
                       track_visibility=True)
    property_id = fields.Many2one("pms.properties", track_visibility=True)
    company_tanent_id = fields.Many2one("res.partner",
                                        "Tenant",
                                        required=True,
                                        track_visibility=True,
                                        domain=[('company_channel_type.name',
                                                 '=', "Tenant")])
    start_date = fields.Date("Start Date",
                             required=True,
                             track_visibility=True)
    end_date = fields.Date("End Date", track_visibility=True, required=True)
    extend_to = fields.Date("Extend End", track_visibility=True)
    vendor_type = fields.Char("Vendor Type", track_visibility=True)
    company_vendor_id = fields.Many2one('res.partner',
                                        "Vendor",
                                        required=True,
                                        track_visibility=True,
                                        domain=[('company_channel_type.name',
                                                 '=', "POS Vendor")])
    currency_id = fields.Many2one('res.currency',
                                  "Currency",
                                  related="property_id.currency_id",
                                  track_visibility=True,
                                  required=True)
    pos_submission = fields.Boolean("Pos Submission", track_visibility=True)
    pos_submission_type = fields.Selection([('FTP', 'FTP'), ('WS', 'WS SOAP'),
                                            ('API', 'Restful API'),
                                            ('MANUAL', 'Manual')],
                                           "Submission Type",
                                           default='API',
                                           track_visibility=True)
    sale_data_type = fields.Selection([('POS-01', 'Transaction'),
                                       ('POS-02', 'Transaction /w Item'),
                                       ('POS-01D', 'Daily Sales'),
                                       ('POS-01M', 'Monthly Sales')],
                                      "Sales Data Type",
                                      default='POS-01',
                                      track_visibility=True)
    pos_submission_frequency = fields.Selection([('15 Minutes', '15 Minutes'),
                                                 ('Daily', 'Daily'),
                                                 ('Monthly', 'Monthly')],
                                                "Submit Frequency",
                                                default='15 Minutes',
                                                track_visibility=True)
    reset_gp_flat = fields.Boolean("Reset GP Flag", track_visibility=True)
    reset_date = fields.Date("Reset Date", track_visibility=True)
    remark = fields.Text("Remark", track_visibility=True)
    state = fields.Selection([('BOOKING', 'Booking'), ('NEW', "New"),
                              ('EXTENDED', "Extended"), ('RENEWED', 'Renewed'),
                              ('CANCELLED', "Cancelled"),
                              ('TERMINATED', 'Terminated'),
                              ('EXPIRED', "Expired")],
                             string="Status",
                             default="BOOKING",
                             track_visibility=True)
    # active = fields.Boolean(default=True, track_visibility=True)
    lease_agreement_line = fields.One2many("pms.lease_agreement.line",
                                           "lease_agreement_id",
                                           "Lease Agreement Units",
                                           required=True,
                                           track_visibility=True)
    lease_no = fields.Char("Lease No",
                           default="New",
                           store=True,
                           track_visibility=True)
    old_lease_no = fields.Char("Old Lease No",
                               default="",
                               store=True,
                               track_visibility=True)
    extend_count = fields.Integer("Extend Times",
                                  store=True,
                                  track_visibility=True)
    # is_terminate = fields.Boolean("Is Terminate", track_visibility=True)
    terminate_period = fields.Date("Terminate Date", track_visibility=True)
    unit_no = fields.Char("Unit",
                          default='',
                          compute="compute_tanent",
                          store=True,
                          track_visibility=True)
    company_id = fields.Many2one(
        'res.company',
        "Company",
        default=lambda self: self.env.user.company_id.id,
        track_visibility=True)
    lease_rent_config_id = fields.One2many("pms.rent_schedule",
                                           "lease_agreement_id",
                                           "Rental Details",
                                           track_visibility=True)
    applicable_type_line_id = fields.One2many(
        'pms.lease.unit.charge.type.line', 'lease_id', "Charge Types")
    booking_date = fields.Date("Booking Date", required=True)
    booking_expdate = fields.Date("Booking ExpDate")
    is_api_post = fields.Boolean("Posted")
    reconfig_flag = fields.Selection([("new", "N"), ("config", "C"),
                                      ('survey', 'Y')],
                                     default="new",
                                     string="Reconfig Flag")

    @api.one
    @api.depends('company_tanent_id', 'lease_agreement_line')
    def compute_tanent(self):
        self.name = ''
        if self.company_tanent_id:
            self.name += self.company_tanent_id.name
        if self.lease_agreement_line:
            self.unit_no = ''
            self.name += '('
            count = 1
            for lag in self.lease_agreement_line:
                for unit in lag.unit_no:
                    if lag and count < len(self.lease_agreement_line):
                        self.name += str(unit.name) + '|'
                        self.unit_no += str(unit.name) + '|'
                    elif lag and count == len(self.lease_agreement_line):
                        self.name += str(unit.name) + ')'
                        self.unit_no += str(unit.name)
                count += 1
            # return self.name or 'New'

    @api.multi
    @api.onchange('start_date')
    def onchange_start_date(self):
        if self.start_date and self.property_id:
            self.end_date = prop = None
            prop = self.property_id
            if not prop.new_lease_term:
                raise UserError(_("Please set new lease term in Property."))
            if prop.new_lease_term and prop.new_lease_term.lease_period_type == 'month':
                self.end_date = self.start_date + relativedelta(
                    months=prop.new_lease_term.min_time_period
                ) - relativedelta(days=1)
            if prop.new_lease_term and prop.new_lease_term.lease_period_type == 'year':
                self.end_date = self.start_date + relativedelta(
                    years=prop.new_lease_term.min_time_period) - relativedelta(
                        days=1)

    # @api.multi
    # def toggle_active(self):
    #     for la in self:
    #         if not la.active:
    #             la.active = self.active
    #     super(PMSLeaseAgreement, self).toggle_active()

    @api.multi
    def action_activate(self):
        if not self.lease_agreement_line:
            raise UserError(_("Lease Unit Item does not exist."))
        if self.lease_agreement_line:
            res = {}
            res['name'] = res['lease_no'] = None
            res['name'] = self.name
            res['lease_no'] = self.lease_no
            for line in self.lease_agreement_line:
                if line.reconfig_flag not in ('config', 'survey'):
                    res['lease_agreement_line_id'] = res[
                        'lease_agreement_id'] = res['unit_no'] = res[
                            'extend_count'] = res['extend_to'] = None
                    res['lease_agreement_line_id'] = line.id
                    res['lease_agreement_id'] = self.id
                    res['unit_no'] = line.unit_no.id
                    res['extend_count'] = line.extend_count
                    res['extend_to'] = line.extend_to
                    for unit in line.unit_no:
                        # if unit.status == 'occupied' and line.state == 'BOOKING':
                        # raise UserError(
                        #     _("Unit(%s)'s status is Occupied that are using in a lease. Please set anthor unit."
                        #       % unit.unit_no))
                        if unit.status == 'occupied' and line.state == 'BOOKING' and unit.config_flag != 'config':
                            raise UserError(
                                _("Unit(%s)'s status is Occupied that are using in a lease. Please set anthor unit."
                                  % unit.unit_no))
                        if unit.status != 'occupied' and line.state == 'BOOKING' and unit.config_flag != 'config':
                            unit.write({'status': 'occupied'})
                        if unit.status == "vacant" and line.state == "NEW":
                            unit.write({'status': 'occupied'})
                    for ctype in line.applicable_type_line_id:
                        res['amount'] = res['charge_type'] = None
                        res['charge_type'] = ctype.applicable_charge_id.id
                        res['amount'] = ctype.total_amount
                        if self.property_id.rentschedule_type == 'prorated':
                            date = None
                            res['start_date'] = None
                            res['billing_date'] = None
                            day = 1
                            res['end_date'] = None
                            next_month_sdate = None
                            while day >= 1:
                                bill_type = ctype.applicable_charge_id.billing_type
                                res['property_id'] = self.property_id.id
                                if line.start_date and line.end_date:
                                    if not res['end_date']:
                                        if line.state == 'NEW':
                                            res['end_date'] = line.end_date
                                        elif line.state == 'EXTENDED':
                                            if line.start_date > line.extend_start:
                                                res['end_date'] = line.start_date
                                            else:
                                                res['end_date'] = line.extend_start
                                        else:
                                            res['end_date'] = line.start_date

                                    day, next_month_sdate = self.rent_schedule_prorated(
                                        bill_type, line, res, next_month_sdate)
                                else:
                                    raise UserError(
                                        _("Please set start date and end date for your lease."
                                          ))
                        if self.property_id.rentschedule_type == 'calendar':
                            date = None
                            res['start_date'] = None
                            res['end_date'] = None
                            s_day = 0
                            last_day = 0
                            day = 1
                            next_month_sdate = None
                            while day >= 1:
                                bill_type = ctype.applicable_charge_id.billing_type
                                res['property_id'] = self.property_id.id
                                if line.start_date and line.end_date:
                                    if not res['end_date']:
                                        if line.state == 'NEW':
                                            res['end_date'] = line.end_date
                                        elif line.state == 'EXTENDED':
                                            if line.start_date > line.extend_start:
                                                res['end_date'] = line.start_date
                                            else:
                                                res['end_date'] = line.extend_start
                                        else:
                                            res['end_date'] = line.start_date
                                    day, next_month_sdate = self.rent_schedule_calendar(
                                        bill_type, line, res, next_month_sdate)
                                else:
                                    raise UserError(
                                        _("Please set start date and end date for your lease."
                                          ))
                    if line.property_id:
                        property_id = line.property_id
                        if property_id.is_autogenerate_posid:
                            for prop in property_id:
                                if not prop.pos_id_format:
                                    raise UserError(
                                        _("Please set POSID Format in this property setting."
                                          ))
                                if prop.pos_id_format and prop.pos_id_format.format_line_id:
                                    val = []
                                    for ft in prop.pos_id_format.format_line_id:
                                        if ft.value_type == 'dynamic':
                                            if property_id.code and ft.dynamic_value == 'property code':
                                                val.append(property_id.code)
                                        if ft.value_type == 'fix':
                                            val.append(ft.fix_value)
                                        if ft.value_type == 'digit':
                                            sequent_ids = self.env[
                                                'ir.sequence'].search([
                                                    ('name', '=',
                                                     'Lease Interface Code')
                                                ])
                                            sequent_ids.write(
                                                {'padding': ft.digit_value})
                                        if ft.value_type == 'datetime':
                                            mon = yrs = ''
                                            if ft.datetime_value == 'MM':
                                                mon = datetime.today().month
                                                val.append(mon)
                                            if ft.datetime_value == 'MMM':
                                                mon = datetime.today(
                                                ).strftime('%b')
                                                val.append(mon)
                                            if ft.datetime_value == 'YY':
                                                yrs = datetime.today(
                                                ).strftime("%y")
                                                val.append(yrs)
                                            if ft.datetime_value == 'YYYY':
                                                yrs = datetime.today(
                                                ).strftime("%Y")
                                                val.append(yrs)
                                    space = []
                                    leasepos_no_pre = ''
                                    if len(val) > 0:
                                        for l in range(len(val)):
                                            leasepos_no_pre += str(val[l])
                        leasepos_no = ''
                        company_id = self.env.user.company_id.id
                        leasepos_no += self.env['ir.sequence'].with_context(
                            force_company=company_id).next_by_code(
                                'pms.lease.interface.code')
                        posinterface_id = self.env[
                            'pms.lease.interface.code'].create(
                                {'name': leasepos_no_pre + leasepos_no})
                        leasepos_ids = line.leaseunitpos_line_id.create({
                            'posinterfacecode_id':
                            posinterface_id.id,
                            'leaseagreementitem_id':
                            line.id
                        })
        if self.state == 'NEW' and self.extend_to:
            self.write({'state': 'EXTENDED'})
        elif self.state == 'EXTENDED':
            self.write({'state': 'EXTENDED'})
        else:
            val = []
            if self.lease_agreement_line:
                for lease in self.lease_agreement_line:
                    if lease.rent_schedule_line:
                        for sche in lease.rent_schedule_line:
                            val.append(sche.id)
                    # lease.action_invoice(inv_type='INITIAL_PAYMENT', vals=val)
            return self.write({'state': 'NEW'})

    def rent_schedule_prorated(self, bill_type, line, res, next_month_sdate):
        day = 0
        res['message_follower_ids'] = []
        rent_scheobj = self.env['pms.rent_schedule']
        if line.reconfig_flag != 'config':
            if line.end_date > res['end_date']:
                if not res['start_date']:
                    next_month_sdate = line.start_date
                if next_month_sdate == line.start_date:
                    res['start_date'] = next_month_sdate
                    res['end_date'] = next_month_sdate + relativedelta(
                        months=1)
                    res['end_date'] = res['end_date'] - relativedelta(days=1)
                    next_month_sdate = next_month_sdate + relativedelta(
                        months=1)
                    if bill_type == 'monthly':
                        res['billing_date'] = res['end_date']
                    if bill_type == 'quarterly':
                        res['billing_date'] = res['end_date'] + relativedelta(
                            months=2)
                    if bill_type == 'semi-annualy':
                        res['billing_date'] = res['end_date'] + relativedelta(
                            months=5)
                    rent_scheobj.create(res)
                    day = 1
                else:
                    res['start_date'] = next_month_sdate
                    res['end_date'] = res['start_date'] + relativedelta(
                        months=1)
                    res['end_date'] = res['end_date'] - relativedelta(days=1)
                    next_month_sdate = next_month_sdate + relativedelta(
                        months=1)
                    if line.end_date <= res['end_date']:
                        res['end_date'] = line.end_date
                    if bill_type == 'monthly':
                        res['billing_date'] = res['end_date']
                    if bill_type == 'quarterly':
                        res['billing_date'] = res['end_date'] + relativedelta(
                            months=2)
                    if bill_type == 'semi-annualy':
                        res['billing_date'] = res['end_date'] + relativedelta(
                            months=5)
                    day = 1
                    rent_scheobj.create(res)
            elif line.state == 'NEW' and line.extend_to:
                if line.state == 'NEW' and line.end_date <= res[
                        'end_date'] and line.extend_to >= res[
                            'end_date'] + relativedelta(days=2):
                    if not res['start_date']:
                        next_month_sdate = line.end_date + relativedelta(
                            days=1)
                    if next_month_sdate == line.end_date:
                        res['start_date'] = next_month_sdate
                        res['end_date'] = next_month_sdate + relativedelta(
                            months=1)
                        res['end_date'] = res['end_date'] - relativedelta(
                            days=1)
                        next_month_sdate = next_month_sdate + relativedelta(
                            months=1)
                        if bill_type == 'monthly':
                            res['billing_date'] = res['end_date']
                        if bill_type == 'quarterly':
                            res['billing_date'] = res[
                                'end_date'] + relativedelta(months=2)
                        if bill_type == 'semi-annualy':
                            res['billing_date'] = res[
                                'end_date'] + relativedelta(months=5)
                        rent_scheobj.create(res)
                        day = 1
                    else:
                        next_month_sdate = res['end_date'] + relativedelta(
                            days=1)
                        res['start_date'] = next_month_sdate
                        res['end_date'] = next_month_sdate + relativedelta(
                            months=1)
                        res['end_date'] = res['end_date'] - relativedelta(
                            days=1)
                        next_month_sdate = next_month_sdate + relativedelta(
                            months=1)
                        if bill_type == 'monthly':
                            res['billing_date'] = res['end_date']
                        if bill_type == 'quarterly':
                            res['billing_date'] = res[
                                'end_date'] + relativedelta(months=2)
                        if bill_type == 'semi-annualy':
                            res['billing_date'] = res[
                                'end_date'] + relativedelta(months=5)
                        rent_scheobj.create(res)
                        day = 1
            elif line.state == 'NEW' and not line.extend_to:
                if not res['start_date']:
                    next_month_sdate = line.start_date
                if next_month_sdate == line.start_date:
                    res['start_date'] = next_month_sdate
                    res['end_date'] = next_month_sdate + relativedelta(
                        months=1)
                    res['end_date'] = res['end_date'] - relativedelta(days=1)
                    next_month_sdate = res['start_date'] + relativedelta(
                        months=1)
                    if bill_type == 'monthly':
                        res['billing_date'] = res['end_date']
                    if bill_type == 'quarterly':
                        res['billing_date'] = res['end_date'] + relativedelta(
                            months=2)
                    if bill_type == 'semi-annualy':
                        res['billing_date'] = res['end_date'] + relativedelta(
                            months=5)
                    rent_scheobj.create(res)
                    day = 1
            elif line.state == 'EXTENDED' and line.extend_to >= res[
                    'end_date'] + relativedelta(days=2):
                if not res['start_date']:
                    next_month_sdate = line.extend_start
                    if line.start_date > line.extend_start:
                        next_month_sdate = line.start_date
                if next_month_sdate == line.extend_start:
                    res['start_date'] = next_month_sdate
                    res['end_date'] = next_month_sdate + relativedelta(
                        months=1)
                    res['end_date'] = res['end_date'] - relativedelta(days=1)
                    next_month_sdate = next_month_sdate + relativedelta(
                        months=1)
                    if line.extend_to > res['end_date']:
                        res['end_date'] = line.extend_to
                    if bill_type == 'monthly':
                        res['billing_date'] = res['end_date']
                    if bill_type == 'quarterly':
                        res['billing_date'] = res['end_date'] + relativedelta(
                            months=2)
                    if bill_type == 'semi-annualy':
                        res['billing_date'] = res['end_date'] + relativedelta(
                            months=5)
                    rent_scheobj.create(res)
                    day = 1
                else:
                    res['start_date'] = next_month_sdate
                    res['end_date'] = next_month_sdate + relativedelta(
                        months=1)
                    res['end_date'] = res['end_date'] - relativedelta(days=1)
                    next_month_sdate = next_month_sdate + relativedelta(
                        months=1)
                    if line.extend_to < res['end_date']:
                        res['end_date'] = line.extend_to
                    if bill_type == 'monthly':
                        res['billing_date'] = res['end_date']
                    if bill_type == 'quarterly':
                        res['billing_date'] = res['end_date'] + relativedelta(
                            months=2)
                    if bill_type == 'semi-annualy':
                        res['billing_date'] = res['end_date'] + relativedelta(
                            months=5)
                    rent_scheobj.create(res)
                    day = 1
            else:
                day = 0
        return day, next_month_sdate

    def rent_schedule_calendar(self, bill_type, line, res, next_month_sdate):
        day = 0
        res['message_follower_ids'] = []
        rent_scheobj = self.env['pms.rent_schedule']
        if line.reconfig_flag != 'config':
            if not next_month_sdate:
                next_month_sdate = line.start_date
            if line.end_date > res['end_date']:
                s_day = line.start_date.day
                last_day = calendar.monthrange(line.start_date.year,
                                               line.start_date.month)[1]
                if not res['start_date']:
                    next_month_sdate = line.start_date
                if next_month_sdate == line.start_date:
                    res['start_date'] = next_month_sdate
                    res['end_date'] = next_month_sdate + relativedelta(
                        days=last_day - s_day)
                    next_month_sdate = next_month_sdate + relativedelta(
                        days=(last_day - s_day) + 1)
                    if bill_type == 'monthly':
                        res['billing_date'] = res['end_date']
                    if bill_type == 'quarterly':
                        res['billing_date'] = res['end_date'] + relativedelta(
                            months=2)
                    if bill_type == 'semi-annualy':
                        res['billing_date'] = res['end_date'] + relativedelta(
                            months=5)
                    rent_scheobj.create(res)
                    day = 1
                else:
                    res['start_date'] = next_month_sdate
                    l_day = calendar.monthrange(next_month_sdate.year,
                                                next_month_sdate.month)[1]
                    res['end_date'] = next_month_sdate + relativedelta(
                        days=l_day - 1)
                    next_month_sdate = next_month_sdate + relativedelta(
                        days=l_day)
                    if line.end_date <= res['end_date']:
                        res['end_date'] = line.end_date
                    # if self.state == 'BOOKING' and res[
                    #         'end_date'] > line.end_date:
                    #     res['end_date'] = line.end_date
                    # if self.state == 'NEW' and not line.extend_to:
                    #     res['end_date'] = line.end_date
                    # if self.state == 'NEW' and line.extend_to:
                    #     if self.state == 'NEW' and res[
                    #             'end_date'] > line.extend_to:
                    #         res['end_date'] = line.extend_to
                    # if self.state == 'EXTENDED' and res[
                    #         'end_date'] > line.extend_to:
                    #     res['end_date'] = line.extend_to
                    if bill_type == 'monthly':
                        res['billing_date'] = res['end_date']
                    if bill_type == 'quarterly':
                        res['billing_date'] = res['end_date'] + relativedelta(
                            months=2)
                    if bill_type == 'semi-annualy':
                        res['billing_date'] = res['end_date'] + relativedelta(
                            months=5)
                    day = 1
                    rent_scheobj.create(res)
            elif line.state == 'NEW' and not line.extend_to and line.end_date > next_month_sdate:
                s_day = line.start_date.day
                last_day = calendar.monthrange(line.start_date.year,
                                               line.start_date.month)[1]
                if not res['start_date']:
                    next_month_sdate = line.start_date
                if next_month_sdate == line.start_date:
                    res['start_date'] = next_month_sdate
                    res['end_date'] = next_month_sdate + relativedelta(
                        days=last_day - s_day)
                    next_month_sdate = next_month_sdate + relativedelta(
                        days=(last_day - s_day) + 1)
                    if bill_type == 'monthly':
                        res['billing_date'] = res['end_date']
                    if bill_type == 'quarterly':
                        res['billing_date'] = res['end_date'] + relativedelta(
                            months=2)
                    if bill_type == 'semi-annualy':
                        res['billing_date'] = res['end_date'] + relativedelta(
                            months=5)
                    day = 1
                    rent_scheobj.create(res)
                else:
                    res['start_date'] = next_month_sdate
                    l_day = calendar.monthrange(next_month_sdate.year,
                                                next_month_sdate.month)[1]
                    res['end_date'] = next_month_sdate + relativedelta(
                        days=l_day - 1)
                    next_month_sdate = next_month_sdate + relativedelta(
                        days=l_day)
                    if bill_type == 'monthly':
                        res['billing_date'] = res['end_date']
                    if bill_type == 'quarterly':
                        res['billing_date'] = res['end_date'] + relativedelta(
                            months=2)
                    if bill_type == 'semi-annualy':
                        res['billing_date'] = res['end_date'] + relativedelta(
                            months=5)
                    day = 1
                    rent_scheobj.create(res)
            elif line.state == 'NEW' and line.extend_to:
                if line.state == 'NEW' and line.end_date <= res[
                        'end_date'] and line.extend_to >= res[
                            'end_date'] + relativedelta(days=2):
                    s_day = line.end_date.day
                    last_day = calendar.monthrange(line.end_date.year,
                                                   line.end_date.month)[1]
                    if not res['start_date']:
                        next_month_sdate = line.end_date
                    if next_month_sdate == line.end_date:
                        res['start_date'] = next_month_sdate + relativedelta(
                            days=1)
                        res['end_date'] = next_month_sdate + relativedelta(
                            days=last_day - s_day)
                        next_month_sdate = next_month_sdate + relativedelta(
                            days=(last_day - s_day) + 1)
                        if bill_type == 'monthly':
                            res['billing_date'] = res['end_date']
                        if bill_type == 'quarterly':
                            res['billing_date'] = res[
                                'end_date'] + relativedelta(months=2)
                        if bill_type == 'semi-annualy':
                            res['billing_date'] = res[
                                'end_date'] + relativedelta(months=5)
                        day = 1
                        rent_scheobj.create(res)
                    else:
                        res['start_date'] = next_month_sdate
                        l_day = calendar.monthrange(next_month_sdate.year,
                                                    next_month_sdate.month)[1]
                        res['end_date'] = res['end_date'] + relativedelta(
                            days=l_day)
                        next_month_sdate = next_month_sdate + relativedelta(
                            days=l_day)
                        if line.extend_to < res['end_date']:
                            res['end_date'] = line.extend_to
                        if bill_type == 'monthly':
                            res['billing_date'] = res['end_date']
                        if bill_type == 'quarterly':
                            res['billing_date'] = res[
                                'end_date'] + relativedelta(months=2)
                        if bill_type == 'semi-annualy':
                            res['billing_date'] = res[
                                'end_date'] + relativedelta(months=5)
                        day = 1
                        rent_scheobj.create(res)
            elif line.state == 'EXTENDED' and line.extend_to >= res[
                    'end_date'] + relativedelta(days=2):
                s_day = 0
                last_day = 0
                line_date = False
                if not res['start_date']:
                    next_month_sdate = line.extend_start
                    line_date = line.extend_start
                    if line.extend_start < line.start_date:
                        next_month_sdate = line.start_date - relativedelta(
                            days=1)
                        line_date = line.start_date - relativedelta(days=1)
                if next_month_sdate == line_date:
                    res['start_date'] = next_month_sdate + relativedelta(
                        days=1)
                    s_day = res['start_date'].day
                    last_day = calendar.monthrange(res['start_date'].year,
                                                   res['start_date'].month)[1]
                    ext_day = last_day - s_day
                    res['end_date'] = res['end_date'] + relativedelta(
                        days=(ext_day) if s_day > 1 else last_day - 1)
                    next_month_sdate = next_month_sdate + relativedelta(
                        days=(ext_day) if s_day > 1 else last_day + 1)
                    if bill_type == 'monthly':
                        res['billing_date'] = res['end_date']
                    if bill_type == 'quarterly':
                        res['billing_date'] = res['end_date'] + relativedelta(
                            months=2)
                    if bill_type == 'semi-annualy':
                        res['billing_date'] = res['end_date'] + relativedelta(
                            months=5)
                    rent_scheobj.create(res)
                    day = 1
                else:
                    res['start_date'] = next_month_sdate
                    l_day = calendar.monthrange(next_month_sdate.year,
                                                next_month_sdate.month)[1]
                    res['end_date'] = res['end_date'] + relativedelta(
                        days=l_day)
                    next_month_sdate = next_month_sdate + relativedelta(
                        days=l_day)
                    if line.extend_to < res['end_date']:
                        res['end_date'] = line.extend_to
                    if self.state == 'BOOKING' and res[
                            'end_date'] > line.end_date:
                        res['end_date'] = line.end_date
                    if self.state == 'NEW' and res['end_date'] > line.extend_to:
                        res['end_date'] = line.extend_to
                    if self.state == 'EXTENDED' and res[
                            'end_date'] > line.extend_to:
                        res['end_date'] = line.extend_to
                    if bill_type == 'monthly':
                        res['billing_date'] = res['end_date']
                    if bill_type == 'quarterly':
                        res['billing_date'] = res['end_date'] + relativedelta(
                            months=2)
                    if bill_type == 'semi-annualy':
                        res['billing_date'] = res['end_date'] + relativedelta(
                            months=5)
                    rent_scheobj.create(res)
                    day = 1
            else:
                day = 0
        return day, next_month_sdate

    @api.multi
    def action_cancel(self):
        return self.write({'state': 'CANCELLED'})

    @api.multi
    def action_reset_confirm(self):
        return self.write({'state': 'BOOKING'})

    # @api.multi
    # def action_extend(self, start_date, end_date):
    #     if not self.company_id.extend_lease_term:
    #         raise UserError(
    #             _("Please set extend term in the property setting."))
    #     else:
    #         self.extend_count += 1
    #         if self.extend_count > self.company_id.extend_count:
    #             raise UserError(_("Extend Limit is Over."))
    #         # if self.extend_to:
    #         #     self.extend_to = self.extend_to + relativedelta(
    #         #         months=self.company_id.extend_lease_term.min_time_period)
    #         # else:
    #         #     self.extend_to = self.end_date + relativedelta(
    #         #         months=self.company_id.extend_lease_term.min_time_period)
    #         for d in self.lease_agreement_line:
    #             d.write({'extend_to': end_date})
    #         self._context().
    #         self.action_activate()
    #     return self.write({'extend_to': end_date,'state': 'EXTENDED'})

    def send_notify_email(self):
        partner_obj = self.env['res.partner']
        mail_mail = self.env['mail.mail']
        mail_ids = None
        today = datetime.now()
        # today_month_day = '%-' + today.strftime('%m') + '-' + today.strftime(
        #     '%d')
        notify_date = new_lease_ids = extend_lease_ids = par_id = None
        for se in self.env['pms.lease_agreement'].search([]):
            notify_date = new_lease_ids = extend_lease_ids = par_id = None
            par_id = partner_obj.search([('id', '=', se.company_tanent_id.id)])
            noti = None
            if se.state == 'NEW':
                noti = 'extend or renew'
                notify_date = se.end_date - relativedelta(
                    months=se.property_id.new_lease_term.notify_period
                ) + relativedelta(days=1)
                new_lease_ids = se.search([('end_date', '=', notify_date)])
            if se.state == 'EXTENDED':
                noti = 'extend'
                notify_date = se.extend_to - relativedelta(
                    months=se.property_id.extend_lease_term.notify_period)
                extend_lease_ids = se.search([('extend_to', '=', notify_date)])
            if new_lease_ids or extend_lease_ids:
                for val in par_id:
                    email_from = val.email
                    name = val.name
                    subject = "Mall Notify"
                    body = _("Hello %s,\n" % (name))
                    body += _(
                        "\tPlease Check Your Lease Agreements for Lease No(%s) to %s\n"
                        % (se.lease_no, noti))
                    footer = _("Kind regards.\n")
                    footer += _("%s\n\n" % val.company_id.name)
                    mail_ids = mail_mail.create({
                        'email_to':
                        email_from,
                        'subject':
                        subject,
                        'body_html':
                        '<pre><span class="inner-pre" style="font-size: 15px">%s<br>%s</span></pre>'
                        % (body, footer)
                    })
                    mail_ids.send()
        return None

    def send_mail(self):
        mail_ids = None
        today = datetime.now()
        today_month_day = today.strftime('%Y-%m-%d')
        partner_obj = self.env['res.partner']
        mail_mail = self.env['mail.mail']
        notify_date = new_lease_ids = extend_lease_ids = par_id = None
        par_id = partner_obj.search([('id', '=', self.company_tanent_id.id)])
        noti = None
        if not self.end_date:
            if self.state == 'NEW':
                noti = 'Activated'
                notify_date = today_month_day
                # notify_date = self.end_date - relativedelta(
                #     months=self.property_id.new_lease_term.notify_period
                # ) + relativedelta(days=1)
                # new_lease_ids = self.search([('end_date', '=', notify_date)])
            if self.state == 'EXTENDED':
                noti = 'Extended'
                notify_date = today_month_day
                # noti = 'Extend'
                # notify_date = self.extend_to - relativedelta(
                #     months=self.property_id.extend_lease_term.notify_period)
                # extend_lease_ids = self.search([('extend_to', '=', notify_date)])
        else:
            self.state == 'TERMINATED'
            noti = 'Terminated'
            notify_date = self.end_date.strftime('%Y-%m-%d')
        for val in par_id:
            email_from = val.email
            name = val.name
            subject = "ZPMS'Lease Notification"
            body = _("Hello %s,\n" % (name))
            body += _(
                "\tPlease Check Your Lease Agreements for Lease No(%s) is %s in %s.\n"
                % (self.lease_no, noti, today_month_day))
            footer = _("Kind regards.\n")
            footer += _("%s\n\n" % val.company_id.name)
            mail_ids = mail_mail.create({
                'email_to':
                email_from,
                'subject':
                subject,
                'body_html':
                '<pre><span class="inner-pre" style="font-size: 15px">%s<br>%s</span></pre>'
                % (body, footer)
            })
            mail_ids.send()

    @api.multi
    def action_renew(self):
        line = []
        end_date = None
        if self.lease_agreement_line:
            for l in self.lease_agreement_line:
                lease_line_id = self.env['pms.lease_agreement.line'].search([
                    ('id', '=', l.id)
                ])
                for les in lease_line_id:
                    for prop in self.property_id:
                        if prop.new_lease_term and prop.new_lease_term.lease_period_type == 'month':
                            end_date = les.end_date + relativedelta(
                                months=prop.new_lease_term.min_time_period
                            ) - relativedelta(days=1)
                        elif prop.new_lease_term and prop.new_lease_term.lease_period_type == 'year':
                            end_date = les.end_date + relativedelta(
                                years=prop.new_lease_term.min_time_period
                            ) - relativedelta(days=1)
                    appli_ids = []
                    for ctype in les.applicable_type_line_id:
                        app_id = self.env[
                            'pms.lease.unit.charge.type.line'].create({
                                'id':
                                ctype.id,
                                'applicable_charge_id':
                                ctype.applicable_charge_id.id,
                                'charge_type_id':
                                ctype.charge_type_id.id,
                                'applicable_charge_id':
                                ctype.calculation_method_id.id,
                                'rate':
                                ctype.rate,
                                'total_amount':
                                ctype.total_amount
                            })
                        appli_ids.append(app_id.id)
                    les.unit_no.write({'status': 'vacant'})
                    value = {
                        'property_id': les.property_id.id,
                        'unit_no': les.unit_no.id,
                        'start_date': les.end_date,
                        'end_date': end_date,
                        'company_tanent_id': les.company_tanent_id.id,
                        'remark': les.remark,
                        'applicable_type_line_id': [(6, 0, appli_ids)],
                    }
                    line_id = self.env['pms.lease_agreement.line'].create(
                        value)
                line.append(line_id.id)
        val = {
            'name': self.name,
            'property_id': self.property_id.id,
            'company_tanent_id': self.company_tanent_id.id,
            'booking_date': self.end_date,
            'start_date': self.end_date,
            'end_date': end_date,
            'vendor_type': self.vendor_type,
            'company_vendor_id': self.company_vendor_id.id,
            'currency_id': self.currency_id.id,
            'pos_submission': self.pos_submission,
            'pos_submission_type': self.pos_submission_type,
            'sale_data_type': self.sale_data_type,
            'pos_submission_frequency': self.pos_submission_frequency,
            'reset_gp_flat': self.reset_gp_flat,
            'reset_date': self.reset_date,
            'remark': self.remark,
            'state': 'BOOKING',
            # 'active': self.active,
            'lease_agreement_line': [(6, 0, line)],
            'old_lease_no': self.lease_no,
            'company_id': self.company_id.id,
        }
        new_lease_ids = self.env['pms.lease_agreement'].create(val)
        if new_lease_ids:
            new_lease_ids.action_activate()
            self.write({'state': 'RENEWED'})
            return new_lease_ids.action_view_new_lease()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    @api.depends('end_date', 'extend_to')
    def lease_expired(self):
        lease_ids = self.search([])
        today = datetime.now().strftime('%Y-%m-%d')
        today_date = datetime.strptime(today, '%Y-%m-%d').date()
        for exp in lease_ids:
            if exp.extend_to:
                if exp.extend_to < today_date:
                    exp.write({'state': 'EXPIRED'})
            if not exp.extend_to and exp.end_date:
                if exp.end_date < today_date:
                    exp.write({'state': 'EXPIRED'})
            if exp.booking_expdate:
                if exp.booking_expdate < today_date and exp.state == 'BOOKING':
                    exp.write({'state': 'CANCELLED'})

    @api.multi
    @api.depends('end_date', 'extend_to')
    def lease_expired(self):
        lease_ids = self.search([])
        today = datetime.now().strftime('%Y-%m-%d')
        today_date = datetime.strptime(today, '%Y-%m-%d').date()
        for exp in lease_ids:
            if exp.extend_to:
                if exp.extend_to < today_date:
                    exp.write({'state': 'EXPIRED'})
            if not exp.extend_to and exp.end_date:
                if exp.end_date < today_date:
                    exp.write({'state': 'EXPIRED'})
            if exp.booking_expdate:
                if exp.booking_expdate < today_date and exp.state == 'BOOKING':
                    exp.write({'state': 'EXPIRED'})

    @api.multi
    @api.depends('terminate_period')
    def lease_terminate(self):
        lease_ids = self.search([])
        today = datetime.now().strftime('%Y-%m-%d')
        today_date = datetime.strptime(today, '%Y-%m-%d').date()
        for ter in lease_ids:
            if ter.terminate_period:
                if ter.terminate_period == today_date or ter.terminate_period <= today_date:
                    ter.write({'state': 'TERMINATED'})
                    rent_schedule_ids = self.env['pms.rent_schedule'].search([
                        ('unit_no', '=', ter.unit_no),
                        ('lease_no', '=', ter.lease_no),
                        ('end_date', '>', ter.terminate_period)
                    ])
                    if rent_schedule_ids:
                        for rentid in rent_schedule_ids:
                            rentid.write({
                                'state': 'terminated',
                                'active': False
                            })
                            if rentid.start_date < ter.terminate_period and rentid.end_date > ter.terminate_period:
                                rentid.write({
                                    'state': 'generated',
                                    'active': True,
                                    'end_date': ter.terminate_period
                                })

    # @api.multi
    # def action_terminate(self, date):
    #     if self.terminate_period:
    #         for line in self:
    #             rent_schedule_ids = self.env['pms.rent_schedule'].search([
    #                 ('unit_no', '=', line.unit_no),
    #                 ('lease_no', '=', line.lease_no),
    #                 ('start_date', '>=', self.terminate_period)
    #             ])
    #             for rentid in rent_schedule_ids:
    #                 rentid.write({'state': 'terminated', 'active': False})
    #         terminated = self.write({'state': 'TERMINATED'})
    #     return terminated
                    ter.write({'state': 'TERMINATED'})
                    rent_schedule_ids = self.env['pms.rent_schedule'].search([
                        ('unit_no', '=', ter.unit_no),
                        ('lease_no', '=', ter.lease_no),
                        ('start_date', '>=', ter.terminate_period)
                    ])
                    for rentid in rent_schedule_ids:
                        rentid.write({'state': 'terminated'})

    @api.multi
    def action_terminate(self):
        if self.is_terminate == True and self.terminate_period:
            if self.terminate_period <= datetime.now().date():
                for line in self:
                    rent_schedule_ids = self.env['pms.rent_schedule'].search([
                        ('unit_no', '=', line.unit_no),
                        ('lease_no', '=', line.lease_no),
                        ('start_date', '>=', self.terminate_period)
                    ])
                    for rentid in rent_schedule_ids:
                        rentid.write({'state': 'terminated'})
                return self.write({'state': 'TERMINATED'})
            else:
                raise UserError(
                    _("Today date (%s) must be greater than or equal Tarminate date (%s)"
                      % (datetime.now().date(), self.terminate_period)))
        else:
            raise UserError(
                _("Please click is Terminate to set terminate date."))
        terminated = self.write({'state': 'TERMINATED'})
        if terminated:
            for line in self:
                rent_schedule_ids = self.env['pms.rent_schedule'].search([
                    ('unit_no', '=', line.unit_no),
                    ('lease_no', '=', line.lease_no),
                    ('start_date', '>=', self.terminate_period)
                ])
                rent_schedule_ids.write({'state': 'terminated'})
        return terminated

    @api.multi
    def action_view_new_lease(self):
        leases = self.env['pms.lease_agreement'].search([('old_lease_no', '=',
                                                          self.lease_no)])
        action = self.env.ref(
            'property_management_system.action_lease_aggrement_all').read()[0]
        if leases:
            action['views'] = [(self.env.ref(
                'property_management_system.view_lease_aggrement_form').id,
                                'form')]
            action['res_id'] = leases.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.model
    def create(self, values):
        property_id = None
        if 'lease_no' in values:
            lease_id = self.search([('lease_no', '=', values['lease_no'])])
            if lease_id:
                raise UserError(
                    _("%s is already existed." % values['lease_no']))
        if values['property_id']:
            property_id = self.env['pms.properties'].browse(
                values['property_id'])
            if property_id:
                for prop in property_id:
                    if not prop.lease_format:
                        raise UserError(
                            _("Please set Your Lease Format in the property setting."
                              ))
                    if prop.lease_format and prop.lease_format.format_line_id:
                        val = []
                        for ft in prop.lease_format.format_line_id:
                            if ft.value_type == 'dynamic':
                                if property_id.code and ft.dynamic_value == 'property code':
                                    val.append(property_id.code)
                            if ft.value_type == 'fix':
                                val.append(ft.fix_value)
                            if ft.value_type == 'digit':
                                sequent_ids = self.env['ir.sequence'].search([
                                    ('name', '=', 'Lease Agreement')
                                ])
                                sequent_ids.write({'padding': ft.digit_value})
                            if ft.value_type == 'datetime':
                                mon = yrs = ''
                                if ft.datetime_value == 'MM':
                                    mon = datetime.today().month
                                    val.append(mon)
                                if ft.datetime_value == 'MMM':
                                    mon = datetime.today().strftime('%b')
                                    val.append(mon)
                                if ft.datetime_value == 'YY':
                                    yrs = datetime.today().strftime("%y")
                                    val.append(yrs)
                                if ft.datetime_value == 'YYYY':
                                    yrs = datetime.today().strftime("%Y")
                                    val.append(yrs)
                        space = []
                        lease_no_pre = ''
                        if len(val) > 0:
                            for l in range(len(val)):
                                lease_no_pre += str(val[l])
        lease_no = ''
        if 'company_id' not in values:
            values['company_id'] = self.env.user.company_id.id
        lease_no += self.env['ir.sequence'].with_context(
            force_company=values['company_id']).next_by_code(
                'pms.lease_agreement')
        values['lease_no'] = lease_no_pre + lease_no
        if values['start_date'] and values['end_date']:
            termend_date = prop = setdate = termdate = None
            prop = property_id
            print(values['start_date'], values['end_date'])
            sdate = datetime.strptime(values['start_date'], '%Y-%m-%d')
            edate = datetime.strptime(values['end_date'], '%Y-%m-%d')
            if not prop.new_lease_term:
                raise UserError(_("Please set new lease term in Property."))
            if prop.new_lease_term and prop.new_lease_term.lease_period_type == 'month':
                termend_date = sdate + relativedelta(
                    months=prop.new_lease_term.min_time_period
                ) - relativedelta(days=1)
            if prop.new_lease_term and prop.new_lease_term.lease_period_type == 'year':
                termend_date = sdate + relativedelta(
                    years=prop.new_lease_term.min_time_period) - relativedelta(
                        days=1)
            setdate = edate - sdate
            termdate = termend_date - sdate
            year = self.find_years(termdate.days)
            if year <= 1:
                dyear = str(year) + ' year'
            else:
                dyear = str(year) + ' years'
            if setdate.days < termdate.days:
                raise UserError(
                    _("The new lease should have at lease %s contract." %
                      (dyear)))
        return super(PMSLeaseAgreement, self).create(values)

    def find_years(self, termdate):
        tdate = float(round(termdate, 2))
        year = float(round(tdate / 365, 2))
        return year

    @api.multi
    def write(self, vals):
        property_id = sdate = edate = None
        if 'start_date' in vals or 'end_date' in vals:
            termend_date = prop = setdate = termdate = None
            if 'property_id' in vals:
                property_id = self.env['pms.properties'].browse(
                    vals['property_id'])
            else:
                property_id = self.property_id
            prop = property_id
            if 'start_date' in vals:
                sdate = datetime.strptime(vals['start_date'], '%Y-%m-%d')
            else:
                sdate = datetime.strptime(str(self.start_date), '%Y-%m-%d')
            if 'end_date' in vals:
                edate = datetime.strptime(vals['end_date'], '%Y-%m-%d')
            else:
                edate = datetime.strptime(str(self.end_date), '%Y-%m-%d')
            if not prop.new_lease_term:
                raise UserError(_("Please set new lease term in Property."))
            if prop.new_lease_term and prop.new_lease_term.lease_period_type == 'month':
                termend_date = sdate + relativedelta(
                    months=prop.new_lease_term.min_time_period
                ) - relativedelta(days=1)
            if prop.new_lease_term and prop.new_lease_term.lease_period_type == 'year':
                termend_date = sdate + relativedelta(
                    years=prop.new_lease_term.min_time_period) - relativedelta(
                        days=1)
            setdate = edate - sdate
            termdate = termend_date - sdate
            year = self.find_years(termdate.days)
            if year <= 1:
                dyear = str(year) + ' year'
            else:
                dyear = str(year) + ' years'
            if setdate.days < termdate.days:
                raise UserError(
                    _("The new lease should have at lease %s contract." %
                      (dyear)))
        id = None
        id = super(PMSLeaseAgreement, self).write(vals)
        if 'state' in vals and id:
            if 'BOOKING' not in vals or 'CANCELLED' not in vals:
                if self.lease_rent_config_id:
                    property_id = self.env['pms.properties'].browse(
                        vals['property_id']
                    ) if 'property_id' in vals else self.property_id
                    if property_id.api_integration == True:
                        integ_obj = self.env['pms.api.integration'].search([])
                        rent_ids = self.env['pms.api.integration.line'].search(
                            [('name', '=', "LeaseAgreement")])
                        datas = api_rauth_config.APIData.get_data(
                            self, vals, property_id, integ_obj, rent_ids)
                        if datas:
                            if datas.res:
                                response = json.loads(datas.res)
                                if 'responseStatus' in response:
                                    if response['responseStatus']:
                                        if 'message' in response:
                                            if response[
                                                    'message'] == 'SUCCESS':
                                                self.write(
                                                    {'is_api_post': True})
                        if self.lease_agreement_line:
                            leaseitem_api_id = self.env[
                                'pms.api.integration.line'].search([
                                    ('name', '=', "Leaseunititem")
                                ])
                            datas = api_rauth_config.APIData.get_data(
                                self, vals, property_id, integ_obj,
                                leaseitem_api_id)
                            if datas:
                                if datas.res:
                                    response = json.loads(datas.res)
                                    if 'responseStatus' in response:
                                        if response['responseStatus']:
                                            if 'message' in response:
                                                if response[
                                                        'message'] == 'SUCCESS':
                                                    for litem in self.lease_agreement_line:
                                                        litem.write({
                                                            'is_api_post':
                                                            True
                                                        })
                        for loop in self.lease_agreement_line:
                            if loop.leaseunitpos_line_id:
                                leaseipos_api_id = self.env[
                                    'pms.api.integration.line'].search([
                                        ('name', '=', "Leaseunitpos")
                                    ])
                                datas = api_rauth_config.APIData.get_data(
                                    self, vals, property_id, integ_obj,
                                    leaseipos_api_id)

                                if datas:
                                    if datas.res:
                                        response = json.loads(datas.res)
                                        if 'responseStatus' in response:
                                            if response['responseStatus']:
                                                if 'message' in response:
                                                    if response[
                                                            'message'] == 'SUCCESS':
                                                        for lul in loop.leaseunitpos_line_id:
                                                            lul.write({
                                                                'is_api_post':
                                                                True
                                                            })
                        if self.lease_rent_config_id:
                            leasers_api_id = self.env[
                                'pms.api.integration.line'].search([
                                    ('name', '=', "RentSchedule")
                                ])
                            datas = api_rauth_config.APIData.get_data(
                                self, vals, property_id, integ_obj,
                                leasers_api_id)
                            if datas:
                                if datas.res:
                                    response = json.loads(datas.res)
                                    if 'responseStatus' in response:
                                        if response['responseStatus']:
                                            if 'message' in response:
                                                if response[
                                                        'message'] == 'SUCCESS':
                                                    for lrs in self.lease_rent_config_id:
                                                        lrs.write({
                                                            'is_api_post':
                                                            True
                                                        })
        return id

    def lease_agreement_scheduler(self):
        values = None
        property_ids = []
        property_id = self.env['pms.properties'].search([('api_integration',
                                                          '=', True)])
        for pro in property_id:
            property_ids.append(pro.id)
        lease_ids = self.search([('is_api_post', '=', False),
                                 ('property_id', 'in', property_ids),
                                 ('state', '!=', 'BOOKING')])
        if lease_ids:
            integ_obj = self.env['pms.api.integration'].search([])
            api_line_ids = self.env['pms.api.integration.line'].search([
                ('name', '=', "LeaseAgreement")
            ])
            datas = api_rauth_config.APIData.get_data(lease_ids, values,
                                                      property_id, integ_obj,
                                                      api_line_ids)
            if datas:
                if datas.res:
                    response = json.loads(datas.res)
                    if 'responseStatus' in response:
                        if response['responseStatus']:
                            if 'message' in response:
                                if response['message'] == 'SUCCESS':
                                    for lid in lease_ids:
                                        lid.write({'is_api_post': True})


class PMSLeaseAgreementLine(models.Model):
    _name = 'pms.lease_agreement.line'
    _inherit = ['mail.thread']
    _description = "Lease Agreement Line"
    _order = "id,name"

    def get_start_date(self):
        if self._context.get('start_date') != False:
            return self._context.get('start_date')

    def get_end_date(self):
        if self._context.get('end_date') != False:
            return self._context.get('end_date')

    # def get_property_id(self):
    #     if not self.property_id:
    #         return self.lease_agreement_id.property_id or None

    name = fields.Char("Name", compute="compute_name", track_visibility=True)
    lease_agreement_id = fields.Many2one("pms.lease_agreement",
                                         "Lease Agreement",
                                         track_visibility=True)
    property_id = fields.Many2one("pms.properties",
                                  related="lease_agreement_id.property_id",
                                  store=True,
                                  track_visibility=True)
    lease_no = fields.Char("Lease No",
                           related="lease_agreement_id.lease_no",
                           store=True,
                           track_visibility=True)
    unit_no = fields.Many2one("pms.space.unit",
                              domain=[('status', 'in', ['vacant']),
                                      ('spaceunittype_id.chargeable', '=',
                                       True)],
                              required=True,
                              track_visibility=True)
    start_date = fields.Date(string="Start Date",
                             default=get_start_date,
                             readonly=False,
                             required=True,
                             store=True,
                             track_visibility=True)
    end_date = fields.Date(string="End Date",
                           default=get_end_date,
                           readonly=False,
                           required=True,
                           store=True,
                           track_visibility=True)
    extend_to = fields.Date("Extend End", track_visibility=True)
    remark = fields.Text("Remark", track_visibility=True)
    rent_schedule_line = fields.One2many('pms.rent_schedule',
                                         'lease_agreement_line_id',
                                         "Rent Schedules",
                                         track_visibility=True)
    state = fields.Selection([('BOOKING', 'Booking'), ('NEW', "New"),
                              ('EXTENDED', "Extended"), ('RENEWED', 'Renewed'),
                              ('CANCELLED', "Cancelled"),
                              ('TERMINATED', 'Terminated'),
                              ('EXPIRED', "Expired")],
                             related="lease_agreement_id.state",
                             string='Status',
                             readonly=True,
                             copy=False,
                             store=True,
                             default='BOOKING',
                             track_visibility=True)
    extend_start = fields.Date("Extend Start",
                               store=True,
                               track_visibility=True)
    extend_count = fields.Integer("Extend Times",
                                  related="lease_agreement_id.extend_count",
                                  store=True,
                                  track_visibility=True)
    applicable_type_line_id = fields.One2many(
        'pms.lease.unit.charge.type.line', 'lease_line_id', "Charge Types")
    company_tanent_id = fields.Many2one(
        "res.partner",
        "Shop",
        required=True,
        related="lease_agreement_id.company_tanent_id")
    leaseunitpos_line_id = fields.One2many("pms.lease.unit.pos",
                                           'leaseagreementitem_id',
                                           "Lease Unit POS")
    is_api_post = fields.Boolean("Posted")

    reconfig_flag = fields.Selection([("new", "N"), ("config", "C"),
                                      ('survey', 'Y')],
                                     string="Reconfig Flag")
    reconfig_date = fields.Date("Reconfig Date")

    @api.one
    @api.depends('unit_no', 'lease_no')
    def compute_name(self):
        self.name = ''
        if self.unit_no and self.lease_no:
            self.name = self.lease_no + '/' + self.unit_no.name
        elif self.lease_no and not self.unit_no:
            self.name = self.lease_no
        elif self.unit_no and not self.lease_no:
            self.name = self.unit_no.name
        else:
            self.name = 'New'

    @api.one
    def get_interfacecode(self, val):
        posints = []
        if self.leaseunitpos_line_id:
            for lp in self.leaseunitpos_line_id:
                posints.append(lp.posinterfacecode_id.id)
        return posints or []

    @api.multi
    def action_view_invoice(self):
        invoices = self.env['account.invoice'].search([('lease_items', '=',
                                                        self.name)])
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id,
                                'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def action_invoice(self, inv_type, vals):
        invoice_month = invoices = None
        sch_ids = start_date = end_date = []
        if inv_type == 'INITIAL_PAYMENT':
            domain_sch_ids = [('id', 'in', vals)]
            sch_ids = self.env['pms.rent_schedule'].search(domain_sch_ids,
                                                           limit=6)
            if sch_ids:
                for sch in sch_ids:
                    start_date.append(sch.start_date)
                    end_date.append(sch.end_date)
                st_date = start_date[0]
                e_date = end_date[11]
                invoice_month = str(
                    calendar.month_name[st_date.month]) + '/' + str(
                        st_date.year) + ' - ' + str(
                            calendar.month_name[e_date.month]) + '/' + str(
                                e_date.year)
            # invoices = self.env['account.invoice'].search([('lease_no', '=', self.name)])
        if inv_type == 'MONTHLY' and vals:
            if vals[0][0] and vals[0][1]:
                invoice_month = str(
                    calendar.month_name[vals[0][0]]) + ' - ' + str(vals[0][1])
            invoices = self.env['account.invoice'].search([
                ('lease_items', '=', self.name),
                ('inv_month', '=', invoice_month)
            ])
        if invoices:
            raise UserError(
                _("Already create invoice for %s in %s." %
                  (calendar.month_name[vals[0][0]], vals[0][1])))
        else:
            invoice_lines = []
            payment_term = self.env['account.payment.term'].search([
                ('name', '=', 'Immediate Payment')
            ])
            product_name = product_id = prod_ids = prod_id = product_tmp_id = None
            for l in self.rent_schedule_line:
                product_name = l.lease_agreement_line_id.unit_no.name
                prod_ids = self.env['product.template'].search([
                    ('name', 'ilike', product_name)
                ])
                prod_id = self.env['product.product'].search([
                    ('product_tmpl_id', '=', prod_ids.id)
                ])
                if inv_type == 'MONTHLY' and vals:
                    area = rent = 0
                    if l.start_date.month == vals[0][
                            0] and l.start_date.year == vals[0][1]:
                        if not prod_ids:
                            val = {
                                'name': product_name,
                                'sale_ok': False,
                                'is_unit': True
                            }
                            product_tmp_id = self.env[
                                'product.template'].create(val)
                            product_tmp_ids = self.env[
                                'product.product'].search([
                                    ('product_tmpl_id', '=', product_tmp_id.id)
                                ])
                            if not product_tmp_ids:
                                product_id = self.env[
                                    'product.product'].create(
                                        {'product_tmpl_id': product_tmp_id.id})
                            product_id = product_tmp_ids or product_id
                        else:
                            product_id = prod_id
                        account_id = False
                        if product_id.id:
                            account_id = product_id.property_account_income_id.id or product_id.categ_id.property_account_income_categ_id.id
                        taxes = product_id.taxes_id.filtered(
                            lambda r: not self.lease_agreement_id.company_id or
                            r.company_id == self.lease_agreement_id.company_id)
                        unit = self.lease_agreement_id.lease_no
                        if l.charge_type.calcuation_method.name == 'area':
                            area = 1
                            rent = l.amount
                        elif l.charge_type.calcuation_method.name == 'meter_unit':
                            area = 1
                            rent = l.amount
                        else:
                            area = 1
                            rent = l.amount
                        inv_line_id = self.env['account.invoice.line'].create({
                            'name':
                            _(l.charge_type.name),
                            'account_id':
                            account_id,
                            'price_unit':
                            rent,
                            'quantity':
                            area,
                            'uom_id':
                            self.unit_no.uom.id,
                            'product_id':
                            product_id.id,
                            'invoice_line_tax_ids': [(6, 0, taxes.ids)],
                        })
                        invoice_lines.append(inv_line_id.id)
                if inv_type == 'INITIAL_PAYMENT' and vals:
                    area = rent = 0
                    if l.start_date in start_date:
                        if not prod_ids:
                            val = {
                                'name': product_name,
                                'sale_ok': False,
                                'is_unit': True
                            }
                            product_tmp_id = self.env[
                                'product.template'].create(val)
                            product_tmp_ids = self.env[
                                'product.product'].search([
                                    ('product_tmpl_id', '=', product_tmp_id.id)
                                ])
                            if not product_tmp_ids:
                                product_id = self.env[
                                    'product.product'].create(
                                        {'product_tmpl_id': product_tmp_id.id})
                            product_id = product_tmp_ids or product_id
                        else:
                            product_id = prod_id
                        account_id = False
                        if product_id.id:
                            account_id = product_id.property_account_income_id.id or product_id.categ_id.property_account_income_categ_id.id
                        taxes = product_id.taxes_id.filtered(
                            lambda r: not self.lease_agreement_id.company_id or
                            r.company_id == self.lease_agreement_id.company_id)
                        unit = self.lease_agreement_id.lease_no
                        if l.charge_type.calcuation_method.name == 'area':
                            area = 1
                            rent = l.amount
                        elif l.charge_type.calcuation_method.name == 'meter_unit':
                            area = 1
                            rent = l.amount
                        else:
                            area = 1
                            rent = l.amount
                        inv_line_id = self.env['account.invoice.line'].create({
                            'name':
                            _(l.charge_type.name),
                            'account_id':
                            account_id,
                            'price_unit':
                            rent,
                            'quantity':
                            area,
                            'uom_id':
                            self.unit_no.uom.id,
                            'product_id':
                            product_id.id,
                            'invoice_line_tax_ids': [(6, 0, taxes.ids)],
                        })
                        invoice_lines.append(inv_line_id.id)
            if not invoice_lines and vals:
                raise UserError(
                    _("No have Invoice Line for %s in %s." %
                      (calendar.month_name[vals[0][0]], vals[0][1])))
            inv_ids = self.env['account.invoice'].create({
                'lease_items':
                self.name,
                'lease_no':
                self.lease_agreement_id.lease_no,
                'unit_no':
                self.lease_agreement_id.unit_no,
                'inv_month':
                invoice_month,
                'partner_id':
                self.lease_agreement_id.company_tanent_id.id,
                'property_id':
                self.lease_agreement_id.property_id.id,
                'company_id':
                self.lease_agreement_id.company_id.id,
                'payment_term_id':
                payment_term.id,
                'invoice_line_ids': [(6, 0, invoice_lines)],
            })
            # self.invoice_count += 1
            inv_ids.action_invoice_open()
            is_email = self.env.user.company_id.invoice_is_email
            template_id = self.env.ref('account.email_template_edi_invoice',
                                       False)
            composer = self.env['mail.compose.message'].create(
                {'composition_mode': 'comment'})
            return inv_ids

    def lease_agreement_item_scheduler(self):
        values = None
        property_ids = []
        property_id = self.env['pms.properties'].search([('api_integration',
                                                          '=', True)])
        for pro in property_id:
            property_ids.append(pro.id)
        lease_line_ids = self.search([('is_api_post', '=', False),
                                      ('property_id', 'in', property_ids),
                                      ('state', '!=', 'BOOKING')])
        if lease_line_ids:
            integ_obj = self.env['pms.api.integration'].search([])
            api_line_ids = self.env['pms.api.integration.line'].search([
                ('name', '=', "Leaseunititem")
            ])
            datas = api_rauth_config.APIData.get_data(lease_line_ids, values,
                                                      property_id, integ_obj,
                                                      api_line_ids)
            if datas:
                if datas.res:
                    response = json.loads(datas.res)
                    if 'responseStatus' in response:
                        if response['responseStatus']:
                            if 'message' in response:
                                if response['message'] == 'SUCCESS':
                                    for lid in lease_line_ids:
                                        lid.write({'is_api_post': True})

    @api.multi
    def unlink(self):
        for agl in self:
            if agl.state not in ('BOOKING'):
                raise UserError(
                    _('You can not delete a lease agreement items in a activated lease agreement.'
                      ))
        return super(PMSLeaseAgreementLine, self).unlink()


class PMSChargeTypes(models.Model):
    _name = 'pms.charge_types'
    _description = "Charge Types"
    _order = 'ordinal_no,name'

    name = fields.Char("Charge Type", required=True, track_visibility=True)
    ordinal_no = fields.Integer("Ordinal No", required=True)
    calculate_method_ids = fields.Many2many("pms.calculation.method",
                                            "pms_charge_type_calculation",
                                            "charge_id", "calc_method_id",
                                            "Calculate Methods")
    active = fields.Boolean(default=True, track_visibility=True)
    _sql_constraints = [('name_unique', 'unique(name)',
                         'Charge Type is already existed.')]

    @api.multi
    def toggle_active(self):
        for la in self:
            if not la.active:
                la.active = self.active
        super(PMSChargeTypes, self).toggle_active()


class PMSTradeCategory(models.Model):
    _name = "pms.trade_category"
    _description = "Trade Category"

    name = fields.Char("Descritpion", required=True, track_visibility=True)
    code = fields.Char("Code", required=True, track_visibility=True)
    active = fields.Boolean(default=True, track_visibility=True)

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            code = record.name
            result.append((record.id, code))
        return result

    @api.model
    def create(self, values):
        trade_id = self.search([('code', '=', values['code'])])
        if trade_id:
            raise UserError(_("%s is already existed" % values['code']))
        return super(PMSTradeCategory, self).create(values)

    @api.multi
    def write(self, vals):
        if 'code' in vals:
            trade_id = self.search([('code', '=', vals['code'])])
            if trade_id:
                raise UserError(_("%s is already existed" % vals['code']))
        return super(PMSTradeCategory, self).write(vals)


class PMSSubTradeCategory(models.Model):
    _name = "pms.sub_trade_category"
    _description = "Sub Trade Category"

    name = fields.Char("Description", required=True, track_visibility=True)
    code = fields.Char("Code", required=True, track_visibility=True)
    trade_id = fields.Many2one("pms.trade_category",
                               "Trade",
                               track_visibility=True)
    active = fields.Boolean(default=True, track_visibility=True)

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            code = record.name
            result.append((record.id, code))
        return result

    @api.model
    def create(self, values):
        trade_id = self.search([('code', '=', values['code'])])
        if trade_id:
            raise UserError(_("%s is already existed" % values['code']))
        return super(PMSSubTradeCategory, self).create(values)

    @api.multi
    def write(self, vals):
        if 'code' in vals:
            trade_id = self.search([('code', '=', vals['code'])])
            if trade_id:
                raise UserError(_("%s is already existed" % vals['code']))
        return super(PMSSubTradeCategory, self).write(vals)
