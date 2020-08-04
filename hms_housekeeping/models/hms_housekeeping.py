# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HMSHousekeeping(models.Model):

    _name = "hms.housekeeping"
    _description = "Reservation"

    property_ids = fields.Many2many('hms.property',
                                    related="user_id.property_id")
    user_id = fields.Many2one('res.users',
                              string='Salesperson',
                              default=lambda self: self.env.uid,
                              help='Salesperson')
    property_id = fields.Many2one('hms.property',string="Property", domain="[('id', '=?', property_ids)]",help="Property")
    current_date = fields.Date("Today's Date", required=True,
                               index=True,
                               states={'done': [('readonly', True)]},
                               default=fields.Date.today)
    clean_type = fields.Selection([('daily', 'Daily'),
                                   ('checkin', 'Check-In'),
                                   ('checkout', 'Check-Out')],
                                  'Clean Type', required=True,
                                  states={'done': [('readonly', True)]},)
    room_no = fields.Many2one('hms.hms.property.room', 'Room No', required=True,
                              states={'done': [('readonly', True)]},
                              index=True)
    activity_line_ids = fields.One2many('hms.housekeeping.activities',
                                        'a_list', 'Activities',
                                        states={'done': [('readonly', True)]},
                                        help='Detail of housekeeping'
                                        'activities')
    inspector_id = fields.Many2one('res.users', 'Inspector', required=True,
                                   index=True,
                                   states={'done': [('readonly', True)]})
    inspect_date_time = fields.Datetime('Inspect Date Time', required=True,
                                        states={'done': [('readonly', True)]})
    quality = fields.Selection([('excellent', 'Excellent'), ('good', 'Good'),
                                ('average', 'Average'), ('bad', 'Bad'),
                                ('ok', 'Ok')], 'Quality',
                               states={'done': [('readonly', True)]},
                               help="Inspector inspect the room and mark \
                                as Excellent, Average, Bad, Good or Ok. ")
    state = fields.Selection([('inspect', 'Inspect'), ('dirty', 'Dirty'),
                              ('clean', 'Clean'),
                              ('done', 'Done'),
                              ('cancel', 'Cancelled')], 'State',
                             states={'done': [('readonly', True)]},
                             index=True, required=True, readonly=True,
                             default='inspect')

    def action_set_to_dirty(self):
        """
        This method is used to change the state
        to dirty of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        for rec in self:
            rec.write({
                'state': 'dirty',
                'quality': False
            })
            rec.activity_line_ids.write({
                'clean': False,
                'dirty': True,
            })

    def room_cancel(self):
        """
        This method is used to change the state
        to cancel of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        for rec in self:
            rec.write({'state': 'cancel', 'quality': False})

    def room_done(self):
        """
        This method is used to change the state
        to done of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        for rec in self:
            if not rec.quality:
                raise ValidationError(_('Please update quality of work!'))
            rec.state = 'done'

    def room_inspect(self):
        """
        This method is used to change the state
        to inspect of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        for rec in self:
            rec.write({'state': 'inspect', 'quality': False})

    def room_clean(self):
        """
        This method is used to change the state
        to clean of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        for rec in self:
            rec.write({
                'state': 'clean',
                'quality': False
            })
            rec.activity_line_ids.write({
                'clean': True,
                'dirty': False,
            })
