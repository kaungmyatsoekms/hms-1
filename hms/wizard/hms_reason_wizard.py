import datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class HMSCancelReasonWizard(models.TransientModel):
    _name = "hms.cancel_reason_wizard"
    _description = "Cancel Reason Wizard"

    def get_reservation_id(self):
        reservation = self.env['hms.reservation'].browse(
            self._context.get('active_id', []))
        if reservation:
            return reservation

    reservation_id = fields.Many2one("hms.reservation",
                                     default=get_reservation_id,
                                     store=True)
    reservation_no = fields.Char("Reservation",
                                 related="reservation_id.confirm_no",
                                 store=True)
    reason_id = fields.Many2one('hms.reason', string="Reason")

    def action_reason_wiz(self):
        reservations = self.env['hms.reservation'].browse(
            self._context.get('active_id', []))

        # Cancel Table record
        for d in reservations.reservation_line_ids:
            if d.state != 'cancel':
                #Update Availability
                rt_avails = self.env['roomtype.available'].search([('property_id','=',d.property_id.id),('ravail_date','>=', d.arrival),('ravail_date','<',d.departure),('ravail_rmty','=',d.room_type.id)])
                avails = self.env['availability.availability'].search([('property_id','=',d.property_id.id),('avail_date','>=', d.arrival),('avail_date','<',d.departure)])
                dep_avails = self.env['availability.availability'].search([('property_id','=',d.property_id.id),('avail_date','=',d.departure)])
                if d.state == 'confirm':
                    for record in rt_avails:
                        record.ravail_occupancy -= d.rooms
                    for avail in avails:
                        avail.avail_occupancy -= d.rooms
                        if avail.avail_date == d.arrival:
                            avail.avail_arrival -= d.rooms
                    for depavail in  dep_avails:
                        if depavail == d.departure:
                            depavail.avail_dep -= d.rooms
                elif d.state =='reservation':
                    for record in rt_avails:
                        record.ravail_unconfirm -= d.rooms
                    for avail in avails:
                        avail.avail_unconfirm -= d.rooms
                # Update State to reservation line
                d.write({
                    'reason_id': self.reason_id,
                    'state': 'cancel',
                    'active': False,
                })
                # res = {}
                self.env['hms.cancel.rsvn'].create({
                    'is_full_cancel':
                    True,
                    'state':
                    d.state,
                    'reservation_line_id':
                    d.id,
                    'property_id':
                    d.property_id.id,
                    'reservation_id':
                    d.reservation_id.id,
                    'user_id':
                    d.reservation_user_id.id,
                    'date_order':
                    d.madeondate,
                    'company_id':
                    d.company_id.id,
                    'group_id':
                    d.group_id.id,
                    'guest_id':
                    d.guest_id.id,
                    'arrival':
                    d.arrival,
                    'departure':
                    d.departure,
                    'nights':
                    d.nights,
                    'no_ofrooms':
                    d.rooms,
                    'market':
                    d.market.id,
                    'source':
                    d.source.id,
                    'reservation_type':
                    d.reservation_type.id,
                    'reservation_status':
                    d.reservation_status.id,
                    'arrival_flight':
                    d.arrival_flight,
                    'arrival_flighttime':
                    d.arrival_flighttime,
                    'dep_flight':
                    d.dep_flight,
                    'dep_flighttime':
                    d.dep_flighttime,
                    'eta':
                    d.eta,
                    'etd':
                    d.etd,
                    'reason_id':
                    d.reason_id.id,
                    'confirm_no':
                    d.confirm_no,
                    'room_no':
                    d.room_no.id,
                    'room_type':
                    d.room_type.id,
                    'pax':
                    d.pax,
                    'child':
                    d.child,
                    'ratecode_id':
                    d.ratecode_id.id,
                    'room_rate':
                    d.room_rate,
                    'updown_amt':
                    d.updown_amt,
                    'updown_pc':
                    d.updown_pc,
                    'package_id':
                    d.package_id.id,
                    'allotment_id':
                    d.allotment_id,
                    'rate_nett':
                    d.rate_nett,
                    'fo_remark':
                    d.fo_remark,
                    'hk_remark':
                    d.hk_remark,
                    'cashier_remark':
                    d.cashier_remark,
                    'general_remark':
                    d.general_remark,
                    'citime':
                    d.citime,
                    'cotime':
                    d.cotime,
                    'extrabed':
                    d.extrabed,
                    'extrabed_amount':
                    d.extrabed_amount,
                    'extrabed_bf':
                    d.extrabed_bf,
                    'extrapax':
                    d.extrapax,
                    'extrapax_amount':
                    d.extrapax_amount,
                    'extrapax_bf':
                    d.extrapax_bf,
                    'child_bfpax':
                    d.child_bfpax,
                    'child_bf':
                    d.child_bf,
                    'extra_addon':
                    d.extra_addon,
                    'pickup':
                    d.pickup,
                    'dropoff':
                    d.dropoff,
                    'arrival_trp':
                    d.arrival_trp,
                    'arrival_from':
                    d.arrival_from,
                    'departure_trp':
                    d.departure_trp,
                    'departure_from':
                    d.departure_from,
                    'visa_type':
                    d.visa_type,
                    'visa_issue':
                    d.visa_issue,
                    'visa_expire':
                    d.visa_expire,
                    'arrive_reason_id':
                    d.arrive_reason_id,
                })
        # Update Status & Flag for Group
        reservations.write({
            'reason_id': self.reason_id,
            'state': 'cancel',
            'is_full_cancel': True,
        })
        # reservations.cancel_status()
        # reservations.copy_cancel_record()
        # return reservations.send_mail()


class HMSCancelReasonLineWizard(models.TransientModel):
    _name = "hms.cancel_reason_line_wizard"
    _description = "Cancel Reason Wizard"

    def get_reservation_line_id(self):
        reservation_line = self.env['hms.reservation.line'].browse(
            self._context.get('active_id', []))
        if reservation_line:
            return reservation_line

    reservation_line_id = fields.Many2one("hms.reservation.line",
                                          default=get_reservation_line_id,
                                          store=True)
    reservation_no = fields.Char("Reservation",
                                 related="reservation_line_id.confirm_no",
                                 store=True)
    reason_id = fields.Many2one('hms.reason', string="Reason")

    def action_reason_line_wiz(self):
        reservation_lines = self.env['hms.reservation.line'].browse(
            self._context.get('active_id', []))

        for d in reservation_lines:
            #Update Availability
            rt_avails = self.env['roomtype.available'].search([('property_id','=',d.property_id.id),('ravail_date','>=', d.arrival),('ravail_date','<',d.departure),('ravail_rmty','=',d.room_type.id)])
            avails = self.env['availability.availability'].search([('property_id','=',d.property_id.id),('avail_date','>=', d.arrival),('avail_date','<',d.departure)])
            dep_avails = self.env['availability.availability'].search([('property_id','=',d.property_id.id),('avail_date','=',d.departure)])
            if d.state == 'confirm':
                for record in rt_avails:
                    record.ravail_occupancy -= d.rooms
                for avail in avails:
                    avail.avail_occupancy -= d.rooms
                    if avail.avail_date == d.arrival:
                        avail.avail_arrival -= d.rooms
                for depavail in  dep_avails:
                    if depavail == d.departure:
                        depavail.avail_dep -= d.rooms
            elif d.state =='reservation':
                for record in rt_avails:
                    record.ravail_unconfirm -= d.rooms
                for avail in avails:
                    avail.avail_unconfirm -= d.rooms
            # Update State to reservation line
            d.write({
                'reason_id': self.reason_id,
                'state': 'cancel',
                'active': False,
            })
        reservation_lines.copy_cancel_record()
        # Check All Reservation lines are same state, update main group to state
        rec = 0
        confirm = 0
        for d in reservation_lines.reservation_id.reservation_line_ids:
            if d.state != reservation_lines.state:
                rec = rec + 1
            if d.state =='confirm':
                confirm = confirm +1
        if rec == 0:
            reservation_lines.reservation_id.write({
                'state': 'cancel',
                'is_full_cancel': True,
            })
        else :
            if confirm == 0:
                reservation_lines.reservation_id.write({
                    'state':
                    'reservation',
                    'reservation_type': 2,
                    'reservation_status': 13,
                })
        # return reservations.send_mail()