from odoo import models, fields, api, _
import tempfile
from odoo.tools.misc import xlwt
import io
import base64
from odoo.tools import date_utils
from odoo.exceptions import UserError, ValidationError


class ReservationReportWizard(models.TransientModel):
    _name = 'hms.reservation_report_wizard'

    property_id = fields.Many2one('hms.property',
                                  string="Property",
                                  required=True)
    date_start = fields.Date(string='Start Date',
                             required=True,
                             default=fields.Date.today)
    date_end = fields.Date(string='End Date',
                           required=True,
                           default=fields.Date.today)

    # def print_report(self):
    #     data = {
    #         'ids': self.ids,
    #         'model': self._name,
    #         'form': {
    #             'date_start': self.date_start,
    #             'date_end': self.date_end,
    #             'property_id': self.property_id.id,
    #         },
    #     }
    #     return self.env.ref('hms.reservation_report').report_action([],
    #                                                                 data=data)

    # def print_report(self):
    #     datas = {'ids': self.env.context.get('active_ids', [])}
    #     res = self.read(['property_id', 'date_start', 'date_end'])
    #     res = res and res[0] or {}
    #     datas['form'] = res
    #     return self.env.ref('hms.reservation_report').report_action([],
    #                                                                 data=datas)

    def get_report(self):
        data = {
            'ids': self.ids,
            'model': 'hms.reservation.line',
            'form': self.read(['property_id', 'date_start', 'date_end'])[0]
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('hms.reservation_report').report_action(self,
                                                                    data=data)


class ExpectedArrReportWizard(models.TransientModel):
    _name = 'hms.expected_arr_report_wizard'

    property_id = fields.Many2one('hms.property',
                                  string="Property",
                                  required=True)
    arr_date = fields.Date(string='Arrival Date',
                           required=True,
                           default=fields.Date.today)
    type_ = fields.Selection(
        string='Type',
        selection=[('individual', 'Individual'), ('group', 'Group')],
    )

    def get_report(self):
        data = {
            'ids': self.ids,
            'model': 'hms.reservation.line',
            'form': self.read(['property_id', 'arr_date', 'type_'])[0]
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('hms.expected_arrival_report').report_action(
            self, data=data)

    def get_report_excel(self):

        # wb1 = xlwt.Workbook()
        # ws1 = wb1.add_sheet('Expected Arrival Report')
        # fp = cStringIO.StringIO()


# Here all excel data and calculations


        output=io.BytesIO() 
        filename= 'Expected Arrival Report ('+ str(self.property_id.code) +') .xls'
        workbook = xlwt.Workbook(encoding='utf-8')

        worksheet = workbook.add_sheet('Expected Arrival Report')
        font = xlwt.Font()
        font.bold = True
        for_left = xlwt.easyxf("font: bold 1, color black; borders: top double, bottom double, left double, right double; align: horiz left")
        for_left_not_bold = xlwt.easyxf("font: color black; align: horiz left")
        for_center_bold = xlwt.easyxf("font: bold 1, color black; align: horiz center")
        GREEN_TABLE_HEADER = xlwt.easyxf(
            'font: bold 1, name Tahoma, height 250;'
            'align: vertical center, horizontal left, wrap on;'
            'borders: top double, bottom double, left double, right double;'
            )
        style = xlwt.easyxf('font:height 400, bold True, name Arial; align: horiz center, vert center;borders: top medium,right medium,bottom medium,left medium')

        alignment = xlwt.Alignment()  # Create Alignment
        alignment.horz = xlwt.Alignment.HORZ_RIGHT
        style = xlwt.easyxf('align: wrap yes')
        style.num_format_str = '0.00'

        worksheet.row(0).height = 320
        worksheet.col(0).width = 4000
        worksheet.col(1).width = 4000
        borders = xlwt.Borders()
        borders.bottom = xlwt.Borders.MEDIUM
        border_style = xlwt.XFStyle()  # Create Style
        border_style.borders = borders

        report_title = 'Expected Arrival Report ' + str(self.property_id.code)

        worksheet.write_merge(0,1,0,15,report_title,GREEN_TABLE_HEADER)
        worksheet.write(2,0,self.property_id.name,for_left)
        row = 3
        reservation_line_objs = self.env['hms.reservation.line'].search([
            ('property_id', '=', self.property_id.id),
            ('arrival', '=', self.arr_date),
            ('reservation_id.type','=',self.type_),
            ])
        worksheet.write(row, 0, 'Room' or '',for_left)
        worksheet.write(row, 1, 'Type' or '',for_left)
        worksheet.write(row, 2, 'Rooms' or '',for_left)
        worksheet.write(row, 3, 'Adult' or '',for_left)
        worksheet.write(row, 4, 'Child' or '',for_left)
        worksheet.write(row, 5, 'Guest Name' or '',for_left)
        worksheet.write(row, 6, 'Group Name' or '',for_left)
        worksheet.write(row, 7, 'Company Name' or '',for_left) 
        worksheet.write(row, 8, 'Arrival' or '',for_left)
        worksheet.write(row, 9, 'Flight' or '',for_left)
        worksheet.write(row, 10, 'Time' or '',for_left)
        worksheet.write(row, 11, 'Departure' or '',for_left)
        worksheet.write(row,12,'Market' or '',for_left)
        worksheet.write(row, 13, 'Source' or '',for_left)
        worksheet.write(row, 14, 'RateCode' or '',for_left)
        worksheet.write(row, 15, 'Rate' or '',for_left)
        
        
        for obj in reservation_line_objs:
            row +=1
            worksheet.write(row,0,obj.room_no.room_no or '',for_left_not_bold)
            worksheet.write(row,1,obj.room_type.code or '',for_left_not_bold)
            worksheet.write(row,2,obj.rooms or '',for_left_not_bold)
            worksheet.write(row,3,obj.pax or '',for_left_not_bold)
            worksheet.write(row,4,obj.child or '',for_left_not_bold)
            worksheet.write(row,5,obj.guest_id.name or '',for_left_not_bold)
            worksheet.write(row,6,obj.group_id.name or '',for_left_not_bold)
            worksheet.write(row,7,obj.company_id.name or '',for_left_not_bold)
            worksheet.write(row,8,obj.arrival or '',for_left_not_bold)
            worksheet.write(row,9,obj.arrival_flight or '',for_left_not_bold)
            worksheet.write(row,10,obj.arrival_flighttime or '',for_left_not_bold)
            worksheet.write(row,11,obj.departure or '',for_left_not_bold)
            worksheet.write(row,12,obj.market.market_code or '',for_left_not_bold)
            worksheet.write(row,13,obj.source.source_code or '',for_left_not_bold)
            worksheet.write(row,14,obj.ratehead_id.rate_code or '',for_left_not_bold)
            worksheet.write(row,15,obj.room_rate or '',for_left_not_bold)
            
            
        output = io.BytesIO()
        workbook.save(output)
        out = base64.encodestring(output.getvalue())
        report_id=self.env['hms.excel.extended'].create({'excel_file': out, 'file_name': filename})
        output.close()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hms.excel.extended',
            'view_mode': 'form',
            'res_id': report_id.id,
            'views': [(False, 'form')],
            'target': 'new',
            'context': self._context,
        }

    #     output=io.BytesIO() 
    #     filename= 'Expected Arrival Report ' + str(self.property_id.name) + '.xls'
    #     workbook = xlwt.Workbook()

    #     worksheet = workbook.add_sheet('Expected Arrival Report')
    #     font = xlwt.Font()
    #     font.bold = True
    #     for_left = xlwt.easyxf("font: bold 1, color black; borders: top double, bottom double, left double, right double; align: horiz left")
    #     for_left_not_bold = xlwt.easyxf("font: color black; align: horiz left")
    #     for_center_bold = xlwt.easyxf("font: bold 1, color black; align: horiz center")
    #     GREEN_TABLE_HEADER = xlwt.easyxf(
    #         'font: bold 1, name Tahoma, height 250;'
    #         'align: vertical center, horizontal center, wrap on;'
    #         'borders: top double, bottom double, left double, right double;'
    #         )
    #     style = xlwt.easyxf('font:height 400, bold True, name Arial; align: horiz center, vert center;borders: top medium,right medium,bottom medium,left medium')

    #     alignment = xlwt.Alignment()  # Create Alignment
    #     alignment.horz = xlwt.Alignment.HORZ_RIGHT
    #     style = xlwt.easyxf('align: wrap yes')
    #     style.num_format_str = '0.00'

    #     worksheet.row(0).height = 320
    #     worksheet.col(0).width = 4000
    #     worksheet.col(1).width = 4000
    #     borders = xlwt.Borders()
    #     borders.bottom = xlwt.Borders.MEDIUM
    #     border_style = xlwt.XFStyle()  # Create Style
    #     border_style.borders = borders

    #     report_title = 'Expected Arrival Report ' + str(self.property_id.name)

    #     worksheet.write_merge(0,1,0,2,report_title,GREEN_TABLE_HEADER)
    #     row = 2
    #     reservation_line_objs = self.env['hms.reservation.line'].search([
    #         ('property_id', '=', self.property_id.id),
    #         ('arrival', '=', self.arr_date),
    #         ('reservation_id.type','=',self.type_),
    #         ])
    #     worksheet.write(row, 0, 'Name' or '',for_left)
    #     worksheet.write(row, 1, 'Arr Date' or '',for_left)
    #     for obj in reservation_line_objs:
    #         row +=1
    #         # sheet = workbook.add_worksheet('Expected Arrival')
    #         worksheet.write(row,0,obj.property_id.name,for_left_not_bold)
    #         worksheet.write(row,1,obj.arrival,for_left_not_bold)

    #     workbook.close()
    #     output.seek(0)
    #     response.stream.write(output.read())
    #     output.close()

