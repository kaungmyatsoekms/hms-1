from odoo import models, fields, api, _
import tempfile
from odoo.tools.misc import xlwt
import io
import base64
from odoo.http import request
from odoo.tools import date_utils
from odoo.exceptions import UserError, ValidationError
import json
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


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
        data = {
            'ids': self.ids,
            'model': 'hms.reservation.line',
            'form': self.read(['property_id', 'arr_date', 'type_'])[0]
        }

        return {
            'type': 'ir_actions_xlsx_download',
            'data': {'model': 'wizard.hms.expected_arr_report_wizard',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Expected Arrival Report',
                     }
        }

    def get_xlsx_report(self, data, response):
        output=io.BytesIO() 
        filename= 'Expected Arrival Report ' + str(self.property_id.name) + '.xls'
        workbook = xlwt.Workbook()

        worksheet = workbook.add_sheet('Expected Arrival Report')
        font = xlwt.Font()
        font.bold = True
        for_left = xlwt.easyxf("font: bold 1, color black; borders: top double, bottom double, left double, right double; align: horiz left")
        for_left_not_bold = xlwt.easyxf("font: color black; align: horiz left")
        for_center_bold = xlwt.easyxf("font: bold 1, color black; align: horiz center")
        GREEN_TABLE_HEADER = xlwt.easyxf(
            'font: bold 1, name Tahoma, height 250;'
            'align: vertical center, horizontal center, wrap on;'
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

        report_title = 'Expected Arrival Report ' + str(self.property_id.name)

        worksheet.write_merge(0,1,0,2,report_title,GREEN_TABLE_HEADER)
        row = 2
        reservation_line_objs = self.env['hms.reservation.line'].search([
            ('property_id', '=', self.property_id.id),
            ('arrival', '=', self.arr_date),
            ('reservation_id.type','=',self.type_),
            ])
        worksheet.write(row, 0, 'Name' or '',for_left)
        worksheet.write(row, 1, 'Arr Date' or '',for_left)
        for obj in reservation_line_objs:
            row +=1
            # sheet = workbook.add_worksheet('Expected Arrival')
            worksheet.write(row,0,obj.property_id.name,for_left_not_bold)
            worksheet.write(row,1,obj.arrival,for_left_not_bold)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

