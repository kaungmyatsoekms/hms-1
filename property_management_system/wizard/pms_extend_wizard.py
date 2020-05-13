import datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class PMSLeaseExtendWizard(models.TransientModel):
    _name = "pms.lease_extend_wizard"
    _description = "Extend Wizard"

    def get_lease_agreement_id(self):
        lease_extends = self.env['pms.lease_agreement'].browse(
            self._context.get('active_id', []))
        if lease_extends:
            return lease_extends

    def get_start_date(self):
        lease_extends = self.env['pms.lease_agreement'].browse(
            self._context.get('active_id', []))
        return lease_extends.extend_to + relativedelta(
            days=1
        ) if lease_extends.extend_to else lease_extends.end_date + relativedelta(
            days=1)

    def get_end_date(self):
        date = None
        lease_extends = self.env['pms.lease_agreement'].browse(
            self._context.get('active_id', []))
        if lease_extends.start_date and lease_extends.property_id:
            if not lease_extends.property_id.property_management_id:
                raise UserError(
                    _("Pease set management company with your mall."))
            else:
                company = None
                company = lease_extends.property_id
                if not company.extend_lease_term:
                    raise UserError(
                        _("Please set extend lease term in Setting."))
                if company.extend_lease_term and company.extend_lease_term.lease_period_type == 'month':
                    if lease_extends.extend_to == False:
                        date = lease_extends.end_date + relativedelta(
                            months=company.extend_lease_term.min_time_period)
                    else:
                        date = lease_extends.extend_to + relativedelta(
                            months=company.extend_lease_term.min_time_period)
                if company.extend_lease_term and company.extend_lease_term.lease_period_type == 'year':
                    if not lease_extends.extend_to:
                        date = lease_extends.end_date + relativedelta(
                            years=company.extend_lease_term.min_time_period)
                    else:
                        date = lease_extends.extend_to + relativedelta(
                            years=company.extend_lease_term.min_time_period)
                return date

    lease_no = fields.Many2one("pms.lease_agreement",
                               default=get_lease_agreement_id,
                               store=True)
    lease = fields.Char("Lease", related="lease_no.lease_no", store=True)
    extend_start_date = fields.Date('Extend Start Date',
                                    default=get_start_date)
    extend_end_date = fields.Date('Extend End Date', default=get_end_date)

    @api.multi
    def action_extend_wiz(self):
        lease_extends = self.env['pms.lease_agreement'].browse(
            self._context.get('active_id', []))

        if not lease_extends.property_id.extend_lease_term:
            raise UserError(
                _("Please set extend term in the property configuration."))
        else:
            lease_extends.extend_count += 1
            if lease_extends.extend_count > lease_extends.property_id.extend_count:
                raise UserError(_("Extend Limit is Over."))
            # if self.extend_to:
            #     self.extend_to = self.extend_to + relativedelta(
            #         months=self.company_id.extend_lease_term.min_time_period)
            # else:
            #     self.extend_to = self.end_date + relativedelta(
            #         months=self.company_id.extend_lease_term.min_time_period)
            for d in lease_extends.lease_agreement_line:
                d.write({
                    'extend_start': self.extend_start_date,
                    'extend_to': self.extend_end_date
                })
            lease_extends.write({
                'extend_to': self.extend_end_date,
            })
            lease_extends.action_activate()
        lease_extends.write({
            'state': 'EXTENDED',
        })
        return lease_extends.send_mail()
