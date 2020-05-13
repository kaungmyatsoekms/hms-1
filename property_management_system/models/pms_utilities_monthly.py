# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools
from odoo.addons.property_management_system.models import api_rauth_config


class UtilitiesMonthly(models.Model):
    _name = "pms.utilities.monthly"
    _description = "Utiltiy Monthly"

    name = fields.Char("LeaseNo")
    batchcode = fields.Char("BatchCode")
    property_code = fields.Char("PropertyCode")
    billingperiod = fields.Char("BillingPeriod")
    utilities_supply_type = fields.Char("UtilitiesSupplyType")
    utilities_source_type = fields.Char("UtilitiesSourceType")
    utilities_no = fields.Char("UtilitiesNo")
    end_value = fields.Float("End Value")
    start_value = fields.Float("Start Value")
    start_reading_date = fields.Date("LMR Date")
    end_reading_date = fields.Date("TMR Date")

    @api.multi
    def import_utilitiesmonthly(self):
        data = updatedata = []
        integ_obj = self.env['pms.api.integration'].search([])
        api_line_ids = self.env['pms.api.integration.line'].search([
            ('name', '=', "UtilitiesMonthlySale")
        ])
        if api_line_ids:
            api_integ = api_line_ids.generate_api_data({
                'id': api_line_ids,
                'data': data
            })
            utmdatas = []
            monthlydata_id = None
            daily_in_ids = self.search([])
            for datas in list(api_integ.items()):
                utmdatas.append(datas[1])
            utmonthly_datas = utmdatas[1]
            for mid in utmonthly_datas:
                utilityml_ids = self.search([
                    ('utilities_no', '=', mid['meterNo']),
                    ('utilities_source_type', '=', mid['transactionType']),
                    ('name', '=', mid['leaseNo']),
                    ('start_reading_date', '=', mid['startDate']),
                    ('end_reading_date', '=', mid['endDate'])
                ])
                if not utilityml_ids:
                    vals = {
                        'name': mid['leaseNo'],
                        'property_code': mid['propertyCode'],
                        'batchcode': mid['batchCode'],
                        'utilities_supply_type': mid['utilityType'],
                        'utilities_source_type': mid['transactionType'],
                        'utilities_no': mid['meterNo'],
                        'end_value': mid['endValue'],
                        'start_value': mid['startValue'],
                        'start_reading_date': mid['startDate'],
                        'end_reading_date': mid['endDate']
                    }
                    monthlydata_id = super(UtilitiesMonthly, self).create(vals)
                updatedata.append({'importBatchCode': mid['batchCode']})
            property_id = None
            uniq = []
            [uniq.append(x) for x in updatedata if x not in uniq]
            if uniq:
                posid = utilityml_ids or monthlydata_id
                integ_obj = self.env['pms.api.integration'].search([])
                api_line_ids = self.env['pms.api.integration.line'].search([
                    ('name', '=', "UpdateUtilitiesMonthlySale")
                ])
                datas = api_rauth_config.APIData.get_data(
                    posid, uniq, property_id, integ_obj, api_line_ids)
            return monthlydata_id
