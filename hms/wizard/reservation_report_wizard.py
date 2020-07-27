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
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        name = data['record']
        user_obj = self.env.user
        wizard_record = request.env['wizard.hms.expected_arr_report_wizard'].search([])[-1]
        task_obj = request.env['project.task']
        users_selected = []
        stages_selected = []
        for elements in wizard_record.partner_select:
            users_selected.append(elements.id)
        for elements in wizard_record.stage_select:
            stages_selected.append(elements.id)
        if wizard_record.partner_select:
            if wizard_record.stage_select:
                current_task = task_obj.search([('project_id', '=', name),
                                                ('user_id', 'in', users_selected),
                                                ('stage_id', 'in', stages_selected)])

            else:
                current_task = task_obj.search([('project_id', '=', name),
                                                ('user_id', 'in', users_selected)])

        else:
            if wizard_record.stage_select:
                current_task = task_obj.search([('project_id', '=', name),
                                                ('stage_id', 'in', stages_selected)])
            else:
                current_task = task_obj.search([('project_id', '=', name)])
        vals = []
        for i in current_task:
            vals.append({
                'name': i.name,
                'user_id': i.user_id.name if i.user_id.name else '',
                'stage_id': i.stage_id.name,
            })
        if current_task:
            project_name = current_task[0].project_id.name
            user = current_task[0].project_id.user_id.name
        else:
            project_name = current_task.project_id.name
            user = current_task.project_id.user_id.name
        sheet = workbook.add_worksheet("Project Report")
        format1 = workbook.add_format({'font_size': 22, 'bg_color': '#D3D3D3'})
        format4 = workbook.add_format({'font_size': 22})
        format2 = workbook.add_format({'font_size': 12, 'bold': True, 'bg_color': '#D3D3D3'})
        format3 = workbook.add_format({'font_size': 10})
        format5 = workbook.add_format({'font_size': 10, 'bg_color': '#FFFFFF'})
        format7 = workbook.add_format({'font_size': 10, 'bg_color': '#FFFFFF'})
        format7.set_align('center')
        sheet.merge_range('A1:B1', user_obj.company_id.name, format5)
        sheet.merge_range('A2:B2', user_obj.company_id.street, format5)
        sheet.write('A3', user_obj.company_id.city, format5)
        sheet.write('B3', user_obj.company_id.zip, format5)
        sheet.merge_range('A4:B4', user_obj.company_id.state_id.name, format5)
        sheet.merge_range('A5:B5', user_obj.company_id.country_id.name, format5)
        sheet.merge_range('C1:H5', "", format5)
        sheet.merge_range(5, 0, 6, 1, "Project  :", format1)
        if project_name:
            sheet.merge_range(5, 2, 6, 7, project_name, format1)
        sheet.merge_range('A8:B8', "Project Manager    :", format5)
        if user:
            sheet.merge_range('C8:D8', user, format5)
        date_start = ''
        date_end = ''
        if current_task:
            date_start = str(current_task[0].project_id.date_start)
        if current_task:
            date_end = str(current_task[0].project_id.date)
        sheet.merge_range('A9:B9', "Start Date              :", format5)
        if not date_start:
            sheet.merge_range('C9:D9', '', format5)
        else:
            sheet.merge_range('C9:D9', date_start, format5)
        sheet.merge_range('A10:B10', "End Date                :", format5)
        if str(date_end):
            sheet.merge_range('C10:D10', date_end, format5)
        sheet.merge_range(0, 2, 4, 5, "", format5)
        sheet.merge_range(1, 6, 4, 7, "", format5)
        sheet.merge_range(7, 4, 9, 7, "", format5)
        sheet.merge_range(10, 4, 11, 7, "", format5)
        sheet.merge_range('A11:H12', 'Open Tasks', format4)
        sheet.merge_range('A13:D13', "Tasks", format2)
        sheet.merge_range('E13:F13', "Assigned", format2)
        sheet.merge_range('G13:H13', "Stage", format2)
        row_number = 13
        column_number = 0
        for val in vals:
            sheet.merge_range(row_number, column_number, row_number, column_number + 3, val['name'], format3)
            sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['user_id'], format3)
            sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, val['stage_id'], format3)
            row_number += 1

        row_number += 1
        sheet.merge_range(row_number, 0, row_number, 1, user_obj.company_id.phone, format7)
        sheet.merge_range(row_number, 2, row_number, 4, user_obj.company_id.email, format7)
        sheet.merge_range(row_number, 5, row_number, 7, user_obj.company_id.website, format7)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    # def get_xlsx_report(self, data, response):
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

