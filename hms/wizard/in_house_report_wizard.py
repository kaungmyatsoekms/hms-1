from odoo import models, fields, api, _
import tempfile
from odoo.tools.misc import xlwt
import io
import base64
from odoo.tools import date_utils
from datetime import datetime, timedelta


class InHouseReportWizard(models.TransientModel):
    _name = 'hms.inhouse_report_wizard'

    property_id = fields.Many2one('hms.property',
                                  string="Property",
                                  required=True)
    system_date = fields.Date(string="System Date",
                              related="property_id.system_date",
                              store=True)
    property_name = fields.Char(string="Property Name", store=True)
    with_rate = fields.Boolean(default=False)
    rate_attr = fields.Selection(string='Rate',
                                 selection=[('with', 'With Rate'),
                                            ('without', 'Without Rate')],
                                 compute='_compute_rate_attr',
                                 inverse='_write_rate_attr')
    sorting_method = fields.Selection(
        string="Sort By",
        selection=[('gname', 'Guest Name'), ('gpname', 'Group Name'),
                   ('cname', 'Company Name'), ('room', 'Room No'),
                   ('arr', 'Arrival Date'), ('dep', 'Departure Date')],
    )

    @api.onchange('property_id')
    def onchange_property_name(self):
        for rec in self:
            rec.property_name = rec.property_id.name

    # Radio Button for Rate Attr
    @api.depends('with_rate')
    def _compute_rate_attr(self):
        for rec in self:
            if rec.with_rate or self._context.get(
                    'default_rate_attr') == 'with':
                rec.rate_attr = 'with'
                rec.with_rate = True
            else:
                rec.rate_attr = 'without'

    def _write_rate_attr(self):
        for rec in self:
            rec.with_rate = rec.rate_attr == 'with'

    @api.onchange('rate_attr')
    def onchange_rate_attr(self):
        self.with_rate = (self.rate_attr == 'with')

    def get_report(self):
        data = {
            'ids':
            self.ids,
            'model':
            'hms.reservation.line',
            'form':
            self.read([
                'property_id', 'property_name', 'system_date', 'rate_attr',
                'with_rate', 'sorting_method'
            ])[0]
        }

        # ref `module_name.report_id` as reference.
        return self.env.ref('hms.inhouse_report').report_action(self,
                                                                data=data)

    def get_report_excel(self):

        output=io.BytesIO() 
        filename= 'Inhouse Report ('+ str(self.property_id.code) +') .xls'
        workbook = xlwt.Workbook(encoding='utf-8')

        worksheet = workbook.add_sheet('Inhouse Report')
        date_format = xlwt.XFStyle()
        date_format.num_format_str = 'dd/mm/yyyy'
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
        report_title=" "
        if self.rate_attr == 'with':
            report_title = 'Inhouse Report with Rate ' + str(self.property_id.code)
            worksheet.write_merge(0,1,0,15,report_title,GREEN_TABLE_HEADER)
        else:
            report_title = 'Inhouse Report ' + str(self.property_id.code)
            worksheet.write_merge(0,1,0,13,report_title,GREEN_TABLE_HEADER)
        worksheet.write(2,0,self.property_id.name,for_left)
        row = 3
        reservation_line_objs = self.env['hms.reservation.line'].search([
            ('property_id', '=', self.property_id.id),
            ('state', '=', 'checkin'),
            ('departure', '>', datetime.today()),
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
        if self.rate_attr == 'with':
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
            worksheet.write(row,8,obj.arrival or '',date_format)
            worksheet.write(row,9,obj.arrival_flight or '',for_left_not_bold)
            worksheet.write(row,10,obj.arrival_flighttime or '',for_left_not_bold)
            worksheet.write(row,11,obj.departure or '',date_format,)
            worksheet.write(row,12,obj.market.market_code or '',for_left_not_bold)
            worksheet.write(row,13,obj.source.source_code or '',for_left_not_bold)
            if self.rate_attr == 'with':
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
