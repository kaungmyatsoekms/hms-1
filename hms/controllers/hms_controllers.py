# -*- coding: utf-8 -*-
from odoo import http


class Hms(http.Controller):
    # @http.route('/hms/property/', auth='public')
    # def index(self, **kw):
    #     return "Hello, world"

    # @http.route('/hms/roomtype/', auth='public')
    # def index(self, **kw):
    #     roomtypes = http.request.env['hms.roomtype']
    #     return http.request.render('hms.index',{
    #         'roomtypes': roomtypes.search([])
    #     })

    # @http.route('/hms/hms/objects/', auth='public')
    # def list(self, **kw):
    #     return http.request.render('hms.listing', {
    #         'root': '/hms/hms',
    #         'objects': http.request.env['hms.hms'].search([]),
    #     })

    # @http.route('/hms/hms/objects/<model("hms.hms"):obj>/', auth='public')
    # def object(self, obj, **kw):
    #     return http.request.render('hms.object', {
    #         'object': obj
    #     })
