import requests
import json
import urllib.request
from odoo import api, fields, models
from odoo.addons.property_management_system.requests_oauth2 import OAuth2BearerToken
from odoo.addons.property_management_system.models import api_rauth_config


class PMSApiIntegration(models.Model):
    _name = 'pms.api.integration'
    _description = "Api Integration"
    _orders = 'id, name'

    name = fields.Char("API Provider")
    base_url = fields.Char("Base Url",
                           help='Base Url is use to get and send data.')
    auth_url = fields.Char(
        'Authentication Url',
        help='Authentication Url is used to get access token.')
    username = fields.Char("Username")
    password = fields.Char("Password")
    api_integration_line = fields.One2many("pms.api.integration.line",
                                           'api_integration_id', "API Lines")
    active = fields.Boolean("Active", default=True, track_visibility=True)


class PMSApiIntegrationLine(models.Model):
    _name = 'pms.api.integration.line'
    _description = "Api Integration Line"
    _orders = 'id, name'

    name = fields.Char("Name")
    http_method_type = fields.Selection(
        [('get', 'GET'), ('post', 'POST'), ('put', 'PUT'), ('patch', 'PATCH'),
         ('delete', 'DELETE')],
        string="HTTP Method",
        default='get',
        help='Request Method for Integration System.')
    api_url = fields.Char(
        "API Url",
        help='url is a specific path to get data with the related method.')
    active = fields.Boolean("Active", default=True)
    api_integration_id = fields.Many2one('pms.api.integration', "API Provider")

    @api.multi
    def generate_api_data(self, values):
        payload = payload_name = payload_code = payload_active = url = get_api = url_get = data = url_save = None
        headers = {}
        CLIENT_ID = self.api_integration_id.username
        CLIENT_SECRET = self.api_integration_id.password
        access_token = self.api_integration_id.auth_url
        url = self.api_integration_id.base_url
        authon = api_rauth_config.Auth2Client(url, CLIENT_ID, CLIENT_SECRET,
                                              access_token)
        print(authon)
        if self.api_url and self.http_method_type == 'get':
            api_url = url + '/' + self.api_url
            with requests.Session() as s:
                s.auth = OAuth2BearerToken(authon.access_token)
                r = s.get(api_url, timeout=15)
                r.raise_for_status()
                data = r.json()
        if authon.access_token and self.http_method_type == 'post':
            if self.api_url:
                api_url = url + '/' + self.api_url
            host = url.split("//")[1]
            headers = {
                'Content-Type': "application/json",
                'Authorization': "Bearer " + authon.access_token,
                'User-Agent': "PostmanRuntime/7.15.2",
                'Accept': "*/*",
                'Cache-Control': "no-cache",
                'Host': host,
                'Accept-Encoding': "gzip, deflate",
                'Content-Length': "172",
                'Connection': "keep-alive",
                'cache-control': "no-cache"
            }
        return {'url': api_url, 'data': data, 'header': headers}
