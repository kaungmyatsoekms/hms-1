from odoo import api, fields, models, tools, _


class HMSSplitInvoice(models.TransientModel):
    _name = 'hms.split_invoice'
    _description = "Split Invoice"

    guest_id = fields.Many2one('res.partner',
                               string="Guest Name",
                               required=True,
                               domain="[('is_guest', '=', True)]")
    company_id = fields.Many2one(
        'res.partner',
        string="Company",
        domain="['&',('profile_no','!=',''),('is_company','=',True)]")

    def action_split_invoice(self):
        self.ensure_one()
