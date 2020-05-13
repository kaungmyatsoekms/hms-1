import datetime
from odoo import api, fields, models, tools, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class PMSLeaseTerminateWizard(models.TransientModel):
    _name = "pms.lease.terminate.wizard"
    _description = "Terminate Wizard"

    @api.model
    def _get_date(self):
        lease_ids = self.env['pms.lease_agreement'].browse(
            self._context.get('active_id', []))
        date = None
        if lease_ids:
            if not lease_ids.property_id.terminate_days:
                raise UserError(
                    _("Please set terminate days term in the property."))
            else:
                today = datetime.now().strftime('%Y-%m-%d')
                today_date = datetime.strptime(today, '%Y-%m-%d').date()
                for pro in lease_ids.property_id:
                    if pro.terminate_days:
                        date = today_date + relativedelta(
                            days=pro.terminate_days)
        return date or None

    date = fields.Date("Terminated Date", default=_get_date)

    @api.multi
    def action_terminate_wiz(self):
        lease_ids = self.env['pms.lease_agreement'].browse(
            self._context.get('active_id', []))
        date = None
        if self.date:
            if lease_ids:
                if not lease_ids.property_id.terminate_days:
                    raise UserError(
                        _("Please set terminate days term in the property."))
                else:
                    today = datetime.now().strftime('%Y-%m-%d')
                    today_date = datetime.strptime(today, '%Y-%m-%d').date()
                    for pro in lease_ids.property_id:
                        if pro.terminate_days:
                            date = today_date + relativedelta(
                                days=pro.terminate_days)
                if self.date < date:
                    raise UserError(
                        _("Termination date'%s' should not be earlier than the terminated term date'%s'."
                          % (self.date, date)))
                lease_ids.write({'terminate_period': date})
        else:
            raise UserError(_("Please set terminate period."))
        return lease_ids.send_mail()
