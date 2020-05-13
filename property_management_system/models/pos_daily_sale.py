# -*- coding: utf-8 -*-
import datetime
from odoo import api, fields, models
from odoo.addons.property_management_system.models import api_rauth_config


class POSDailySale(models.Model):
    _name = "pos.daily.sale"
    _description = 'POS Daily Sale'

    # property_id = fields.Many2one("pms.properties", "Mall", store=True)
    property_code = fields.Char("PropertyCode", store=True)
    pos_interface_code = fields.Char("POSInterfaceCode")
    pos_receipt_date = fields.Date("POSReceiptDate")
    grosssalesamount = fields.Float("GrossSaleAmount")
    currency = fields.Char("SaleCurrency")
    daily_sale_amt_b4tax = fields.Float("DailySaleAmtB4Tax")
    daily_servicechargeamt = fields.Float("DailyServiceChargeAmt")
    tax_amount = fields.Float("Tax")
    manual_net_sales = fields.Float("ManualNetSales")

    @api.multi
    def import_posdailysale(self):
        data = updatedata = setdatas = []
        integ_obj = self.env['pms.api.integration'].search([])
        api_line_ids = self.env['pms.api.integration.line'].search([
            ('name', '=', "POSDailySale")
        ])
        if api_line_ids:
            api_integ = api_line_ids.generate_api_data({
                'id': api_line_ids,
                'data': data
            })
            posdatas = []
            pos_sale_id = pos_exited_ids = None
            daily_in_ids = self.search([])
            for datas in list(api_integ.items()):
                posdatas.append(datas[1])
            sale_id = posdatas[1]
            for sid in sale_id:
                currency_id = code = business_date = None
                # code = self.env['pms.properties'].search([
                #     ('code', '=', sid['propertyCode'])
                # ]).code
                code = sid['propertyCode']
                currency_id = self.env['res.currency'].search([
                    ('name', '=', sid['currency'])
                ]).id
                b_date = str(sid['businessDate'][0] + sid['businessDate'][1] +
                             sid['businessDate'][2] + sid['businessDate'][3]
                             ) + '-' + str(sid['businessDate'][4] +
                                           sid['businessDate'][5]) + '-' + str(
                                               sid['businessDate'][6] +
                                               sid['businessDate'][7])
                business_date = datetime.datetime.strptime(
                    b_date, '%Y-%m-%d').strftime('%Y-%m-%d')
                pos_exited_ids = self.search([
                    ('pos_receipt_date', '=', business_date),
                    ('pos_interface_code', '=', sid['posInterfaceCode'])
                ])
                if not pos_exited_ids:
                    val = {
                        'property_code': code,
                        'pos_interface_code': sid['posInterfaceCode'],
                        'pos_receipt_date': business_date,
                        'grosssalesamount': sid['grossSalesAmount'],
                        'currency': currency_id,
                        'daily_sale_amt_b4tax': sid['dailySalesAmtB4Tax'],
                        'daily_servicechargeamt': sid['dailyServiceChargeAmt'],
                        'tax_amount': sid['tax'],
                        'manual_net_sales': sid['manualNetSales']
                    }
                    pos_sale_id = super(POSDailySale, self).create(val)
                updatedata.append({
                    'pOSInterfaceCode': sid['posInterfaceCode'],
                    'importBatchCode': sid['batchCode']
                })
                property_id = None
            uniq = []
            [uniq.append(x) for x in updatedata if x not in uniq]
            if uniq:
                posid = pos_exited_ids or pos_sale_id
                integ_obj = self.env['pms.api.integration'].search([])
                api_line_ids = self.env['pms.api.integration.line'].search([
                    ('name', '=', "UpdatePOSDailySale")
                ])
                datas = api_rauth_config.APIData.get_data(
                    posid, uniq, property_id, integ_obj, api_line_ids)
            return pos_sale_id
