import requests
import pytz
import json
import datetime
from odoo.addons.property_management_system.rauth import OAuth2Service
from odoo import tools, _
from odoo import models, api


class APIData:
    def get_data(self, values, property_id, integ_obj, api_line_ids):
        self.values = values
        self.model_id = self
        property_ids = property_id
        integ_obj = integ_obj
        api_line_ids = api_line_ids
        api_integ = data = []
        headers = {}
        payload_code = payload_name = modify_date = payload = payload_area = None
        if api_line_ids:
            for line in api_line_ids:
                url_save = line.api_integration_id.base_url + '/' + line.api_url
                if line.http_method_type == 'post':
                    try:
                        api_integ = line.generate_api_data({
                            'id': line.id,
                            'data': self.values
                        })
                    except Exception:
                        if api_integ == []:
                            return None
                    headers = api_integ['header']
                    if line.name == 'Property':
                        modify_date = datetime.datetime.now().strftime(
                            '%Y-%m-%d')
                        bd = datetime.datetime.now().strftime('%Y%M%d')
                        bt = datetime.datetime.now().strftime("%H%M%S")
                        data_batch = BatchInfo()
                        data_batch.AppCode = "ZPMS"
                        data_batch.BatchCode = str(bd + bt)
                        data_batch.InterfaceCode = "Properties"
                        propertys = Property()
                        if self.values == None:
                            for pl in self.model_id:
                                data_batch.PropertyCode = pl.code
                                payload_code = pl.code
                                payload_name = pl.name
                                uom = pl.uom_id.name
                                autogenerate = pl.is_autogenerate_posid or False
                                currency = pl.currency_id.name or None
                                url = pl.web_site_url or None
                                tz = datetime.datetime.now(
                                    pytz.timezone(pl.timezone
                                                  or 'GMT')).strftime('%z')
                                tzh = sign = None
                                if tz:
                                    if tz[0] == '+':
                                        sign = 1
                                    else:
                                        sign = -1
                                    tzh = str(tz[1]) + str(tz[2]) + ":" + str(
                                        tz[3]) + str(tz[4]) + ':00'
                                propertys.PropertyID = ""
                                propertys.PropertyCode = pl.code
                                propertys.PropertyName = pl.name
                                propertys.UM = pl.uom_id.name or None
                                propertys.IsAutogenerate = autogenerate
                                propertys.Timezone = tzh
                                propertys.ExtPropertyCode = pl.code
                                propertys.LocalCurrency = currency
                                propertys.TimeZoneSign = sign
                                propertys.ExtDataSourceID = 'ZPMS'
                                propertys.ExtPropertyID = pl.id
                                propertys.ModifiedDate = datetime.datetime.now(
                                ).strftime('%Y-%m-%d')
                                propertys.WebSiteUrl = url
                                propertys.BatchInfo = data_batch.__dict__
                                data.append(propertys.__dict__)
                        elif 'is_api_post' in self.values and self.values[
                                'is_api_post'] == True:
                            return None
                        else:
                            if 'code' in self.values:
                                payload_code = str(self.values['code'])
                            if 'name' in self.values:
                                payload_name = str(self.values['name'])
                            payload_code = payload_code or self.model_id.code
                            payload_name = payload_name or self.model_id.name
                            uom = str(self.model_id.uom_id.name
                                      ) if self.model_id.uom_id else None
                            autogenerate = self.model_id.is_autogenerate_posid if self.model_id.is_autogenerate_posid == True else False
                            currency = str(
                                self.model_id.currency_id.name
                            ) if self.model_id.currency_id else None
                            url = str(self.model_id.web_site_url
                                      ) if self.model_id.web_site_url else None
                            tz = datetime.datetime.now(
                                pytz.timezone(self.model_id.timezone
                                              or 'GMT')).strftime('%z')
                            tzh = sign = None
                            if tz:
                                if tz[0] == '+':
                                    sign = 1
                                else:
                                    sign = -1
                                tzh = str(tz[1]) + str(tz[2]) + ":" + str(
                                    tz[3]) + str(tz[4]) + ':00'
                            data_batch.PropertyCode = str(payload_code)
                            propertys.PropertyID = ""
                            propertys.PropertyCode = payload_code
                            propertys.PropertyName = payload_name
                            propertys.UM = 'SQFT' if uom == 'sqft' else uom
                            propertys.IsAutogenerate = autogenerate
                            propertys.Timezone = tzh
                            propertys.ExtPropertyCode = payload_code
                            propertys.LocalCurrency = currency
                            propertys.TimeZoneSign = sign
                            propertys.ExtDataSourceID = 'ZPMS'
                            propertys.ExtPropertyID = str(self.model_id.id)
                            propertys.ModifiedDate = datetime.datetime.now(
                            ).strftime('%Y-%m-%d')
                            propertys.WebSiteUrl = url
                            propertys.BatchInfo = data_batch.__dict__
                            payload = propertys.__dict__
                    if line.name == 'Floor':
                        modify_date = datetime.datetime.now().strftime(
                            '%Y-%m-%d')
                        bd = datetime.datetime.now().strftime('%Y%M%d')
                        bt = datetime.datetime.now().strftime("%H%M%S")
                        data_batch = BatchInfo()
                        # floor = Floor()
                        data_batch.AppCode = "ZPMS"
                        data_batch.BatchCode = str(bd + bt)
                        data_batch.InterfaceCode = "Floors"
                        if self.values == None:
                            for fl in self.model_id:
                                floor = Floor()
                                payload_code = fl.code
                                payload_name = fl.name
                                data_batch.PropertyCode = fl.property_id.code
                                # payload_active = fl.active
                                floor.BatchInfo = data_batch.__dict__
                                floor.FloorID = ""
                                floor.FloorCode = payload_code
                                floor.FloorDesc = payload_name
                                floor.ModifiedDate = modify_date
                                floor.ExtDataSourceID = "ZPMS"
                                floor.Remark = ''
                                floor.ExtFloorID = str(fl.id)
                                data.append(floor.__dict__)
                        elif 'is_api_post' in self.values and self.values[
                                'is_api_post'] == True:
                            return None
                        else:
                            floor = Floor()
                            if 'code' in self.values:
                                payload_code = str(self.values['code'])
                            if 'name' in self.values:
                                payload_name = str(self.values['name'])
                            data_batch.PropertyCode = self.property_id.code
                            floor.BatchInfo = data_batch.__dict__
                            floor.FloorID = ""
                            floor.FloorCode = payload_code or self.model_id.code
                            floor.FloorDesc = payload_name or self.model_id.name
                            floor.ModifiedDate = modify_date
                            floor.ExtDataSourceID = "ZPMS"
                            floor.Remark = ''
                            floor.ExtFloorID = str(self.model_id.id)
                            payload = floor.__dict__
                    if line.name == 'CRMAccount':
                        if len(self.model_id) >= 1 or self.values == None:
                            for crm in self.model_id:
                                payload_name = crm.name
                                modify_date = datetime.datetime.now().strftime(
                                    '%Y-%m-%d')
                                payload_active = crm.active
                                data_batch = BatchInfo()
                                data_batch.AppCode = "ZPMS"
                                data_batch.PropertyCode = None
                                bd = datetime.datetime.now().strftime('%Y%M%d')
                                bt = datetime.datetime.now().strftime("%H%M%S")
                                data_batch.BatchCode = str(bd + bt)
                                data_batch.InterfaceCode = "CRMAccounts"
                                crmaccount = CRMAccount()
                                crmaccount.CRMAccountName = payload_name
                                crmaccount.CRMAccountID = None
                                if len(crm.company_channel_type) > 1:
                                    for ccn in crm.company_channel_type:
                                        if crmaccount.CRMAccountTypeID:
                                            crmaccount.CRMAccountTypeID = str(
                                                crmaccount.CRMAccountTypeID
                                            ) + str(ccn.code)
                                        else:
                                            crmaccount.CRMAccountTypeID = str(
                                                ccn.code)
                                        if len(crm.company_channel_type
                                               ) < count:
                                            crmaccount.CRMAccountTypeID += ','
                                else:
                                    crmaccount.CRMAccountTypeID = crm.company_channel_type.code or None
                                crmaccount.Remark = None
                                crmaccount.RegNo = None
                                crmaccount.WebSiteUrl = crm.website or None
                                crmaccount.CountryOfOrigin = None
                                crmaccount.ContactPerson = None
                                crmaccount.Phone = crm.phone or None
                                crmaccount.Address = None
                                crmaccount.TenantCode = None
                                crmaccount.Trade = str(
                                    crm.trade_id.name
                                ) if crm.trade_id else None
                                crmaccount.TradeCategory = str(
                                    crm.sub_trade_id.name
                                ) if crm.sub_trade_id else None
                                crmaccount.CRMAccountTypeDescription = None
                                crmaccount.ExtDataSourceID = "ZPMS"
                                crmaccount.ExtCRMAccountID = str(crm.id)
                                crmaccount.ModifiedDate = modify_date
                                crmaccount.BatchInfo = data_batch.__dict__
                                data.append(crmaccount.__dict__)
                        else:
                            phone = None
                            if 'name' in self.values:
                                payload_name = str(self.values['name'])
                            payload_name = payload_name or self.model_id.name
                            modify_date = datetime.datetime.now().strftime(
                                '%Y-%m-%d')
                            if 'active' in self.values:
                                if self.values['active'] == True:
                                    payload_active = 'true'
                                else:
                                    payload_active = 'false'
                            data_batch = BatchInfo()
                            data_batch.AppCode = "ZPMS"
                            data_batch.PropertyCode = None
                            bd = datetime.datetime.now().strftime('%Y%M%d')
                            bt = datetime.datetime.now().strftime("%H%M%S")
                            data_batch.BatchCode = str(bd + bt)
                            data_batch.InterfaceCode = "CRMAccounts"
                            crmaccount = CRMAccount()
                            crmaccount.CRMAccountName = payload_name
                            crmaccount.CRMAccountID = None
                            if len(self.model_id.company_channel_type) > 1:
                                for ccn in self.model_id.company_channel_type:
                                    if crmaccount.CRMAccountTypeID:
                                        crmaccount.CRMAccountTypeID = str(
                                            crmaccount.CRMAccountTypeID) + str(
                                                ccn.code)
                                    else:
                                        crmaccount.CRMAccountTypeID = str(
                                            ccn.code)
                                    if len(self.model_id.company_channel_type
                                           ) < count:
                                        crmaccount.CRMAccountTypeID += ','
                            else:
                                crmaccount.CRMAccountTypeID = self.model_id.company_channel_type.code or None
                            crmaccount.Remark = None
                            crmaccount.RegNo = None
                            if 'website' in self.values:
                                crmaccount.WebSiteUrl = self.values[
                                    'website'] if self.values[
                                        'website'] != False else None
                            crmaccount.CountryOfOrigin = None
                            crmaccount.ContactPerson = None
                            if 'phone' in self.values:
                                phone = self.values['phone']
                            crmaccount.Phone = phone or self.model_id.phone
                            crmaccount.Address = None
                            crmaccount.TenantCode = None
                            crmaccount.Trade = str(
                                self.model_id.trade_id.name
                            ) if self.model_id.trade_id else None
                            crmaccount.TradeCategory = str(
                                self.model_id.sub_trade_id.name
                            ) if self.model_id.sub_trade_id else None
                            crmaccount.CRMAccountTypeDescription = None
                            crmaccount.ExtDataSourceID = "ZPMS"
                            crmaccount.ExtCRMAccountID = str(self.model_id.id)
                            crmaccount.ModifiedDate = modify_date
                            crmaccount.BatchInfo = data_batch.__dict__
                            payload = crmaccount.__dict__
                    if line.name == 'SpaceUnit':
                        start_date = end_date = payload_remark = payload_active = None
                        data_batch = BatchInfo()
                        data_batch.AppCode = "ZPMS"
                        bd = datetime.datetime.now().strftime('%Y%M%d')
                        bt = datetime.datetime.now().strftime("%H%M%S")
                        data_batch.BatchCode = str(bd + bt)
                        data_batch.InterfaceCode = "SpaceUnits"
                        if self.values == None:
                            for sp in self.model_id:
                                spaceunit = SpaceUnit()
                                payload_name = sp.name
                                payload_area = sp.area
                                start_date = sp.start_date.strftime(
                                    '%Y-%m-%d') if sp.start_date else None
                                end_date = sp.end_date.strftime(
                                    '%Y-%m-%d') if sp.end_date else None
                                payload_uom = sp.uom.name
                                payload_remark = sp.remark
                                floor_id = sp.floor_id.id
                                modify_date = datetime.datetime.now().strftime(
                                    '%Y-%m-%d')
                                payload_active = sp.active
                                data_batch.PropertyCode = sp.property_id.code
                                spaceunit.PropertyCode = sp.property_id.code
                                spaceunit.FloorID = floor_id
                                spaceunit.SpaceUnitNo = payload_name
                                spaceunit.DisplayOrdinal = None
                                spaceunit.StartDate = start_date
                                spaceunit.EndDate = end_date
                                spaceunit.Area = payload_area
                                spaceunit.SpaceUnitID = ''
                                spaceunit.UM = payload_uom
                                spaceunit.Remark = payload_remark
                                spaceunit.ExtDataSourceID = 'ZPMS'
                                spaceunit.ExtSpaceUnitID = str(sp.id)
                                spaceunit.ModifiedDate = modify_date
                                spaceunit.Status = payload_active
                                spaceunit.BatchInfo = data_batch.__dict__
                                data.append(spaceunit.__dict__)
                        else:
                            spaceunit = SpaceUnit()
                            if 'name' in self.values:
                                payload_name = payload_name or str(
                                    self.model_id.name)
                                payload_name = self.values['name']
                            payload_name = payload_name or str(
                                self.model_id.name)
                            if 'area' in self.values:
                                payload_area = str(self.values['area'])
                            payload_area = payload_area or str(
                                self.model_id.area)
                            if 'start_date' in self.values:
                                start_date = self.values['start_date']
                            start_date = start_date or self.model_id.start_date.strftime(
                                '%Y-%m-%d')
                            if 'end_date' in self.values:
                                end_date = self.values['end_date']
                            end_date = end_date or self.model_id.end_date.strftime(
                                '%Y-%m-%d') if self.model_id.end_date else None
                            floor_code = str(self.model_id.floor_code)
                            payload_uom = str(self.model_id.uom.name)
                            if 'remark' in self.values:
                                payload_remark = self.values['remark']
                            payload_remark = payload_remark or self.model_id.remark
                            floor_id = str(self.model_id.floor_id.id)
                            modify_date = datetime.datetime.now().strftime(
                                '%Y-%m-%d')
                            if 'active' in self.values:
                                payload_active = self.values['active']
                            payload_active = payload_active or False
                            data_batch.PropertyCode = property_ids.code
                            spaceunit.PropertyCode = property_ids.code
                            spaceunit.FloorID = floor_id
                            spaceunit.SpaceUnitNo = payload_name
                            spaceunit.FloorCode = floor_code
                            spaceunit.DisplayOrdinal = None
                            spaceunit.StartDate = start_date
                            spaceunit.EndDate = end_date
                            spaceunit.Area = payload_area
                            spaceunit.SpaceUnitID = ''
                            spaceunit.UM = payload_uom
                            spaceunit.Remark = payload_remark
                            spaceunit.ExtDataSourceID = 'ZPMS'
                            spaceunit.ExtSpaceUnitID = str(self.model_id.id)
                            spaceunit.ModifiedDate = modify_date
                            spaceunit.Status = payload_active
                            spaceunit.BatchInfo = data_batch.__dict__
                            payload = spaceunit.__dict__
                    if line.name == 'SpaceUnitFacilities':
                        modify_date = datetime.datetime.now().strftime(
                            '%Y-%m-%d')
                        data_batch = BatchInfo()
                        data_batch.AppCode = "ZPMS"
                        bd = datetime.datetime.now().strftime('%Y%M%d')
                        bt = datetime.datetime.now().strftime("%H%M%S")
                        data_batch.BatchCode = str(bd + bt)
                        data_batch.InterfaceCode = "Facilities"
                        if 'create' not in self.values and len(
                                self.model_id) >= 1:
                            for facl in self.model_id:
                                flineids = space_unit_id = PropertyCode = UtilityMeterNo = UtilityType = StartDate = Remark = Digit = None
                                if 'facilities_line' in facl:
                                    if facl.facilities_line:
                                        flineids = facl.facilities_line
                                        space_unit_id = self.values.env[
                                            'pms.space.unit'].search([
                                                ('property_id', '=',
                                                 facl.property_id.id)
                                            ])
                                    PropertyCode = facl.property_id.code
                                    UtilityMeterNo = facl.utilities_no.name
                                    UtilityType = facl.utilities_type_id.code
                                    StartDate = facl.install_date.strftime(
                                        '%Y-%m-%d'
                                    ) if facl.install_date != False else None
                                    Remark = str(
                                        facl.remark
                                    ) if facl.remark != False else None
                                    Digit = facl.utilities_no.digit
                                if 'facility_line' in facl:
                                    if facl.facility_line:
                                        for fal in facl.facility_line:
                                            if fal.facilities_line:
                                                flineids = fal.facilities_line
                                                StartDate = fal.install_date.strftime(
                                                    '%Y-%m-%d'
                                                ) if fal.install_date != False else None
                                                PropertyCode = fal.property_id.code
                                                UtilityMeterNo = fal.utilities_no.name
                                                UtilityType = fal.utilities_type_id.code
                                                Remark = str(
                                                    fal.remark
                                                ) if fal.remark != False else None
                                                Digit = fal.utilities_no.digit
                                for facline in flineids:
                                    facility = SpaceUnitFacility()
                                    data_batch.PropertyCode = PropertyCode
                                    facility.UtilityMeterNo = UtilityMeterNo
                                    facility.UtilityType = UtilityType
                                    facility.StartDate = StartDate
                                    facility.Remark = Remark
                                    facility.Digit = Digit
                                    if space_unit_id:
                                        for sp in space_unit_id:
                                            if sp.facility_line:
                                                for spf in sp.facility_line:
                                                    if spf.id == facl.id:
                                                        facility.SpaceUnitID = sp.id
                                    else:
                                        facility.SpaceUnitID = self.model_id.id
                                    facility.SpaceUnitFacilityID = ''
                                    facility.EndDate = facline.end_date.strftime(
                                        '%Y-%m-%d'
                                    ) if facline.end_date != False else None
                                    facility.LastReadingOn = facline.lmr_date.strftime(
                                        '%Y-%m-%d'
                                    ) if facline.lmr_date != False else None
                                    facility.LastReadingValue = facline.lmr_value
                                    facility.LastReadingNOC = 0
                                    facility.LastReadingNOH = 0
                                    facility.EMeterType = facline.source_type_id.code
                                    facility.IsNew = True
                                    facility.UpdateMethod = None
                                    facility.Indicator = None
                                    facility.CanChangeMeterNo = False
                                    facility.ExtDataSourceID = 'ZPMS'
                                    facility.ExtSpaceUnitFacilityID = str(
                                        facline.id)
                                    facility.ModifiedDate = modify_date
                                    facility.BatchInfo = data_batch.__dict__
                                    if facility.SpaceUnitID:
                                        data.append(facility.__dict__)
                        else:
                            if self.model_id.facility_line.facilities_line:
                                for facline in self.model_id.facility_line.facilities_line:
                                    facility = SpaceUnitFacility()
                                    data_batch.PropertyCode = facline.property_id.code
                                    facility.SpaceUnitID = str(
                                        self.model_id.id)
                                    facility.SpaceUnitFacilityID = ''
                                    facility.StartDate = str(
                                        self.model_id.start_date)
                                    facility.EndDate = str(
                                        self.model_id.end_date
                                    ) if self.model_id.end_date else None
                                    facility.UtilityMeterNo = self.model_id.facility_line.utilities_no.name
                                    facility.UtilityType = self.model_id.facility_line.utilities_type_id.code
                                    facility.LastReadingOn = str(
                                        facline.lmr_date)
                                    facility.LastReadingValue = facline.lmr_value
                                    facility.LastReadingNOC = 0
                                    facility.LastReadingNOH = 0
                                    facility.EMeterType = facline.source_type_id.code
                                    facility.Remark = str(
                                        self.model_id.remark
                                    ) if self.model_id.remark != False else None
                                    facility.IsNew = True
                                    facility.UpdateMethod = None
                                    facility.Digit = self.model_id.facility_line.utilities_no.digit
                                    facility.Indicator = None
                                    facility.CanChangeMeterNo = False
                                    facility.ExtDataSourceID = 'ZPMS'
                                    facility.ExtSpaceUnitFacilityID = str(
                                        facline.id)
                                    facility.ModifiedDate = modify_date
                                    facility.BatchInfo = data_batch.__dict__
                                    data.append(facility.__dict__)
                    if line.name == 'LeaseAgreement':
                        # payload_code = str(self.values['code'])
                        # payload_name = str(self.values['name'])
                        modify_date = datetime.datetime.now().strftime(
                            '%Y-%m-%d')
                        # if self.values['active'] == True:
                        #     payload_active = 'true'
                        # else:
                        #     payload_active = 'false'
                        data_batch = BatchInfo()
                        data_batch.AppCode = "ZPMS"
                        bd = datetime.datetime.now().strftime('%Y%M%d')
                        bt = datetime.datetime.now().strftime("%H%M%S")
                        data_batch.BatchCode = str(bd + bt)
                        data_batch.InterfaceCode = "LeaseAgreements"
                        lease = LeaseAgreement()
                        if len(self.model_id) >= 1 and self.values == None:
                            for lg in self.model_id:
                                data_batch.PropertyCode = lg.property_id.code
                                lease.LeaseAgreementID = ""
                                lease.CrmAccountID = lg.company_tanent_id.id or None
                                lease.PosVendorID = lg.company_vendor_id.id or None
                                lease.PropertyID = lg.property_id.id
                                lease.LeaseStartDate = lg.start_date.strftime(
                                    '%Y-%m-%d'
                                ) if lg.start_date != False else None
                                lease.LeaseEndDate = lg.end_date.strftime(
                                    '%Y-%m-%d'
                                ) if lg.end_date != False else None
                                lease.Remark = ''
                                status = None
                                ext_date = None
                                if lg.state == 'NEW':
                                    status = "New"
                                elif lg.state == 'EXTENDED':
                                    status = "Extended"
                                    ext_date = lg.extend_to
                                elif lg.state == 'TERMINATED':
                                    status = 'Pre-terminated'
                                elif lg.state == 'CANNELLED':
                                    status = 'Cancelled'
                                elif lg.state == 'RENEWED':
                                    status = 'Renewed'
                                elif lg.state == 'EXPIRED':
                                    status = 'Expired'
                                else:
                                    status = 'New'
                                lease.ExtendedTo = ext_date.strftime(
                                    '%Y-%m-%d') if ext_date != None else None
                                lease.LeaseStatus = status
                                lease.ExternalLeaseNo = str(
                                    lg.lease_no) or None
                                lease.DefaultLocalCurrency = lg.property_id.currency_id.name or None
                                lease.PropertyCode = property_ids.code
                                lease.PosSubmissionFrequency = lg.pos_submission_frequency or None
                                lease.SpaceUnitNo = lg.unit_no or None
                                lease.AppAccessKeyStatus = True
                                lease.ExtDataSourceID = 'ZPMS'
                                lease.ModifiedDate = modify_date
                                lease.ExtLeaseAgreementID = lg.id
                                lease.PosSubmissionType = lg.pos_submission_type or None
                                lease.SalesDataType = lg.sale_data_type or None
                                lease.BatchInfo = data_batch.__dict__
                                data.append(lease.__dict__)
                        else:
                            ext_date = None
                            data_batch.PropertyCode = property_ids.code
                            lease.LeaseAgreementID = ""
                            lease.CrmAccountID = self.model_id.company_tanent_id.id or None
                            lease.PosVendorID = self.model_id.company_vendor_id.id or None
                            lease.PropertyID = property_ids.id
                            lease.LeaseStartDate = self.model_id.start_date.strftime(
                                '%Y-%m-%d'
                            ) if self.model_id.start_date != False else None
                            lease.LeaseEndDate = self.model_id.end_date.strftime(
                                '%Y-%m-%d'
                            ) if self.model_id.end_date != False else None
                            lease.Remark = self.model_id.remark or None
                            status = None
                            if self.values['state'] == 'NEW':
                                status = "New"
                            elif self.values['state'] == 'EXTENDED':
                                status = "Extended"
                                ext_date = self.model_id.extend_to
                            elif self.values['state'] == 'TERMINATED':
                                status = 'Pre-terminated'
                            elif self.values['state'] == 'CANNELLED':
                                status = 'Cancelled'
                            elif self.values['state'] == 'RENEWED':
                                status = 'Renewed'
                            elif self.values['state'] == 'EXPIRED':
                                status = 'Expired'
                            else:
                                status = None
                            lease.ExtendedTo = ext_date.strftime(
                                '%Y-%m-%d') if ext_date != None else None
                            lease.LeaseStatus = status
                            lease.ExternalLeaseNo = str(
                                self.model_id.lease_no) or None
                            lease.DefaultLocalCurrency = self.model_id.property_id.currency_id.name or None
                            lease.PropertyCode = property_ids.code
                            lease.PosSubmissionFrequency = self.model_id.pos_submission_frequency or None
                            lease.SpaceUnitNo = self.model_id.unit_no or None
                            lease.AppAccessKeyStatus = True
                            lease.ExtDataSourceID = 'ZPMS'
                            lease.ModifiedDate = modify_date
                            lease.ExtLeaseAgreementID = self.model_id.id
                            lease.PosSubmissionType = self.model_id.pos_submission_type or None
                            lease.SalesDataType = self.model_id.sale_data_type or None
                            lease.BatchInfo = data_batch.__dict__
                            payload = lease.__dict__
                    if line.name == 'Leaseunititem':
                        data_batch = BatchInfo()
                        data_batch.AppCode = "ZPMS"
                        bd = datetime.datetime.now().strftime('%Y%M%d')
                        bt = datetime.datetime.now().strftime("%H%M%S")
                        data_batch.BatchCode = str(bd + bt)
                        data_batch.InterfaceCode = "LeaseUnitItem"
                        modify_date = datetime.datetime.now().strftime(
                            '%Y-%m-%d')
                        if len(self.model_id) >= 1 and self.values == None:
                            for lgl in self.model_id:
                                data_batch.PropertyCode = lgl.property_id.code
                                leaseline = LeaseAgreementItem()
                                leaseline.LeaseAgreementID = lgl.lease_agreement_id.id if lgl.lease_agreement_id.id != False else ""
                                leaseline.LeaseAgreementItemID = ''
                                leaseline.SpaceUnitID = lgl.unit_no.id if lgl.unit_no.id != False else ""
                                leaseline.StartDate = lgl.start_date.strftime(
                                    '%Y-%m-%d'
                                ) if lgl.start_date != False else None
                                leaseline.EndDate = lgl.end_date.strftime(
                                    '%Y-%m-%d'
                                ) if lgl.end_date != False else None
                                leaseline.ExtendedTo = lgl.extend_to.strftime(
                                    '%Y-%m-%d'
                                ) if lgl.extend_to != False else None
                                leaseline.Remark = lgl.remark if lgl.remark != False else None
                                leaseline.CrmAccountID = lgl.company_tanent_id.id if lgl.company_tanent_id != False else None
                                leaseline.ExtDataSourceID = "ZPMS"
                                leaseline.ModifiedDate = modify_date
                                leaseline.ExtLeaseAgreementItemID = (lgl.id)
                                leaseline.Active = True
                                leaseline.BatchInfo = data_batch.__dict__
                                data.append(leaseline.__dict__)
                        else:
                            if self.model_id.lease_agreement_line:
                                data_batch.PropertyCode = property_ids.code
                                for facline in self.model_id.lease_agreement_line:
                                    leaseline = LeaseAgreementItem()
                                    leaseline.LeaseAgreementID = self.model_id.id if self.model_id != False else ""
                                    leaseline.LeaseAgreementItemID = ''
                                    leaseline.SpaceUnitID = facline.unit_no.id if facline.unit_no.id != False else ""
                                    leaseline.StartDate = facline.start_date.strftime(
                                        '%Y-%m-%d'
                                    ) if facline.start_date != False else None
                                    leaseline.EndDate = facline.end_date.strftime(
                                        '%Y-%m-%d'
                                    ) if facline.end_date != False else None
                                    leaseline.ExtendedTo = facline.extend_to.strftime(
                                        '%Y-%m-%d'
                                    ) if facline.extend_to != False else None
                                    leaseline.Remark = facline.remark if facline.remark != False else None
                                    leaseline.CrmAccountID = self.model_id.company_tanent_id.id if self.model_id.company_tanent_id != False else None
                                    leaseline.ExtDataSourceID = "ZPMS"
                                    leaseline.ModifiedDate = modify_date
                                    leaseline.ExtLeaseAgreementItemID = (
                                        facline.id)
                                    leaseline.Active = True
                                    leaseline.BatchInfo = data_batch.__dict__
                                    data.append(leaseline.__dict__)
                    if line.name == 'Leaseunitpos':
                        data_batch = BatchInfo()
                        data_batch.AppCode = "ZPMS"
                        data_batch.PropertyCode = property_ids.id
                        bd = datetime.datetime.now().strftime('%Y%M%d')
                        bt = datetime.datetime.now().strftime("%H%M%S")
                        data_batch.BatchCode = str(bd + bt)
                        data_batch.InterfaceCode = "LeaseUnitPOS"
                        modify_date = datetime.datetime.now().strftime(
                            '%Y-%m-%d')
                        if len(self.model_id) >= 1 and self.values == None:
                            for lup in self.model_id:
                                leasepos = LeaseUnitPos()
                                leasepos.LeaseAgreementItemPosInterfaceCodeID = ""
                                leasepos.LeaseAgreementID = lup.leaseagreementitem_id.lease_agreement_id.id
                                leasepos.LeaseAgreementItemID = lup.leaseagreementitem_id.id
                                leasepos.SpaceUnitID = lup.leaseagreementitem_id.unit_no.id
                                leasepos.InactiveDate = lup.inactivedate.strftime(
                                    '%Y-%m-%d'
                                ) if lup.inactivedate != False else None
                                leasepos.PosInterfaceCode = lup.posinterfacecode_id.name
                                leasepos.UsePosID = lup.useposid
                                leasepos.Status = lup.posidisactive
                                leasepos.ExtDataSourceID = "ZPMS"
                                leasepos.ExtLeaseAgreementItemPosInterfaceCodeID = lup.id
                                leasepos.ModifiedDate = modify_date
                                leasepos.Active = lup.active
                                leasepos.BatchInfo = data_batch.__dict__
                                data.append(leasepos.__dict__)
                        else:
                            if self.model_id.lease_agreement_line and self.model_id.lease_agreement_line.leaseunitpos_line_id:
                                for lline in self.model_id.lease_agreement_line:
                                    if lline.leaseunitpos_line_id:
                                        for pl in lline.leaseunitpos_line_id:
                                            leasepos = LeaseUnitPos()
                                            leasepos.LeaseAgreementItemPosInterfaceCodeID = ""
                                            leasepos.LeaseAgreementID = self.model_id.id
                                            leasepos.LeaseAgreementItemID = lline.id
                                            leasepos.SpaceUnitID = lline.unit_no.id
                                            leasepos.InactiveDate = pl.inactivedate.strftime(
                                                '%Y-%m-%d'
                                            ) if pl.inactivedate != False else None
                                            leasepos.PosInterfaceCode = pl.posinterfacecode_id.name
                                            leasepos.UsePosID = pl.useposid
                                            leasepos.Status = pl.posidisactive
                                            leasepos.ExtDataSourceID = "ZPMS"
                                            leasepos.ExtLeaseAgreementItemPosInterfaceCodeID = pl.id
                                            leasepos.ModifiedDate = modify_date
                                            leasepos.Active = pl.active
                                            leasepos.BatchInfo = data_batch.__dict__
                                            data.append(leasepos.__dict__)
                    if line.name == 'RentSchedule':
                        data_batch = BatchInfo()
                        data_batch.AppCode = "ZPMS"
                        bd = datetime.datetime.now().strftime('%Y%M%d')
                        bt = datetime.datetime.now().strftime("%H%M%S")
                        data_batch.BatchCode = str(bd + bt)
                        data_batch.InterfaceCode = "RentSchedule"
                        modify_date = datetime.datetime.now().strftime(
                            '%Y-%m-%d')
                        if len(self.model_id) >= 1 and self.values == None:
                            for rs in self.model_id:
                                data_batch.PropertyCode = rs.property_id.id
                                rentschedule = RentSchedule()
                                rentschedule.RentScheduleID = ""
                                rentschedule.PropertyID = rs.property_id.id
                                rentschedule.StartDate = rs.start_date.strftime(
                                    '%Y-%m-%d') if rs.start_date else None
                                rentschedule.EndDate = rs.end_date.strftime(
                                    '%Y-%m-%d') if rs.end_date else None
                                rentschedule.ChargeType = rs.charge_type.charge_type_id.name if rs.charge_type else None
                                rentschedule.CurrencyCode = rs.lease_agreement_id.currency_id.name
                                rentschedule.AmountLocal = rs.amount
                                rentschedule.LeaseAgreementItemID = rs.lease_agreement_line_id.id
                                rentschedule.ExtRentScheduleID = rs.id
                                rentschedule.ExtDataSourceID = 'ZPMS'
                                rentschedule.ModifiedDate = modify_date
                                rentschedule.Active = rs.active
                                rentschedule.BatchInfo = data_batch.__dict__
                                data.append(rentschedule.__dict__)
                        else:
                            if self.model_id.lease_agreement_line and self.model_id.lease_rent_config_id:
                                for lline in self.model_id.lease_agreement_line:
                                    if lline.rent_schedule_line:
                                        for pl in lline.rent_schedule_line:
                                            data_batch.PropertyCode = property_ids.id
                                            rentschedule = RentSchedule()
                                            rentschedule.RentScheduleID = ""
                                            rentschedule.PropertyID = self.property_id.id
                                            rentschedule.StartDate = pl.start_date.strftime(
                                                '%Y-%m-%d'
                                            ) if pl.start_date else None
                                            rentschedule.EndDate = pl.end_date.strftime(
                                                '%Y-%m-%d'
                                            ) if pl.end_date else None
                                            rentschedule.ChargeType = pl.charge_type.charge_type_id.name if pl.charge_type else None
                                            rentschedule.CurrencyCode = self.model_id.currency_id.name
                                            rentschedule.AmountLocal = pl.amount
                                            rentschedule.LeaseAgreementItemID = lline.id
                                            rentschedule.ExtRentScheduleID = pl.id
                                            rentschedule.ExtDataSourceID = 'ZPMS'
                                            rentschedule.ModifiedDate = modify_date
                                            rentschedule.Active = pl.active
                                            rentschedule.BatchInfo = data_batch.__dict__
                                            data.append(rentschedule.__dict__)
                    if line.name == 'UpdatePOSDailySale':
                        data = self.values
                    if line.name == 'UpdateUtilitiesMonthlySale':
                        data = self.values
                    prepaylad = json.dumps([payload])
                    dprepaylay = json.dumps(data)
                    r = requests.request(
                        "POST",
                        url_save,
                        data=json.dumps([payload] if payload else data),
                        headers=headers)
                    self.res = r.text
        return self


class Auth2Client:
    def __init__(self,
                 url=None,
                 client_id=None,
                 client_secret=None,
                 access_token=None):
        self.access_token = self.service = self.url = None
        self.url = url
        self.service = OAuth2Service(
            name="foo",
            client_id=client_id,
            client_secret=client_secret,
            access_token_url=access_token,
            authorize_url=access_token,
            base_url=url,
        )
        return self.get_access_token()

    def get_access_token(self):
        data = {
            'code': 'bar',
            'grant_type': 'client_credentials',
            'redirect_uri': self.url
        }
        session = self.service.get_auth_session(data=data, decoder=json.loads)
        self.access_token = session.access_token


class BatchInfo:
    AppCode = None
    PropertyCode = None
    BatchCode = None
    InterfaceCode = None


class Property:
    PropertyID = None
    PropertyCode = None
    PropertyName = None
    DisplayOrdinal = None
    UM = None
    IsAutogenerate = None
    Timezone = None
    ExtPropertyCode = None
    LocalCurrency = None
    TimeZoneSign = None
    ExtDataSourceID = None
    ExtPropertyID = None
    ModifiedDate = None
    WebSiteUrl = None
    BatchInfo = None


class Floor:
    FloorID = None
    FloorCode = None
    FloorDesc = None
    DisplayOrdinal = None
    Remark = None
    ExtDataSourceID = None
    ExtFloorID = None
    ModifiedDate = None
    BatchInfo = None


class CRMAccount:
    CRMAccountName = None
    CRMAccountID = None
    CRMAccountTypeID = None
    Remark = None
    RegNo = None
    WebSiteUrl = None
    CountryOfOrigin = None
    ContactPerson = None
    Phone = None
    Address = None
    TenantCode = None
    Trade = None
    TradeCategory = None
    CRMAccountTypeDescription = None
    ExtDataSourceID = None
    ExtCRMAccountID = None
    ModifiedDate = None
    BatchInfo = None


class SpaceUnit:
    FloorID = None
    SpaceUnitID = None
    PropertyID = None
    SpaceUnitNo = None
    PropertyCode = None
    FloorCode = None
    DisplayOrdinal = None
    Area = None
    Remark = None
    StartDate = None
    EndDate = None
    UM = None
    Status = None
    ExtDataSourceID = None
    ExtSpaceUnitID = None
    ModifiedDate = None
    BatchInfo = None


class SpaceUnitFacility:
    SpaceUnitID = None
    SpaceUnitFacilityID = None
    StartDate = None
    EndDate = None
    UtilityMeterNo = None
    UtilityType = None
    LastReadingOn = None
    LastReadingValue = None
    LastReadingNOC = None
    LastReadingNOH = None
    EMeterType = None
    Remark = None
    IsNew = None
    UpdateMethod = None
    Digit = None
    Indicator = None
    CanChangeMeterNo = None
    ExtDataSourceID = None
    ExtSpaceUnitFacilityID = None
    ModifiedDate = None
    BatchInfo = None


class LeaseAgreement:
    LeaseAgreementID = None
    CrmAccountID = None
    PosVendorID = None
    PropertyID = None
    PosIDs = None
    LeaseStartDate = None
    LeaseEndDate = None
    ExtendedTo = None
    OldEndDate = None
    RevisedEndDate = None
    Remark = None
    EnforceGPFlag = None
    ResetGPFlag = None
    SetResetOn = None
    LeaseStatus = None
    ResetDate = None
    ExternalLeaseNo = None
    LeaseAggrementCode = None
    PosInterfaceCode = None
    AppAccessKey = None
    AppSecretAccessKey = None
    DefaultLocalCurrency = None
    PropertyName = None
    PropertyCode = None
    ShopName = None
    VendorName = None
    PosSubmissionFrequency = None
    LeaseStatusDesc = None
    SpaceUnitNo = None
    AppAccessKeyStatus = None
    DebugMode = None
    ExtDataSourceID = None
    ModifiedDate = None
    ExtLeaseAgreementID = None
    PosSubmissionType = None
    SalesDataType = None
    PosSubmissionTypeDesc = None
    SalesDataTypeDesc = None
    SubmissionLink = None
    BatchInfo = None


class LeaseAgreementItem:
    LeaseAgreementID = None
    LeaseAgreementItemID = None
    SpaceUnitID = None
    StartDate = None
    EndDate = None
    ExtendedTo = None
    Remark = None
    CrmAccountID = None
    ExtDataSourceID = None
    ModifiedDate = None
    ExtLeaseAgreementItemID = None
    Active = None
    BatchInfo = None


class LeaseUnitPos:
    LeaseAgreementItemPosInterfaceCodeID = None
    LeaseAgreementID = None
    LeaseAgreementItemID = None
    SpaceUnitID = None
    InactiveDate = None
    PosInterfaceCode = None
    UsePosID = None
    Status = None
    ExtDataSourceID = None
    ExtLeaseAgreementItemPosInterfaceCodeID = None
    ModifiedDate = None
    Active = None
    BatchInfo = None


class RentSchedule:
    RentScheduleID = None
    PropertyID = None
    StartDate = None
    EndDate = None
    ChargeType = None
    CurrencyCode = None
    AmountLocal = None
    LeaseAgreementItemID = None
    ExtRentScheduleID = None
    ExtDataSourceID = None
    ModifiedDate = None
    Active = None
    BatchInfo = None
