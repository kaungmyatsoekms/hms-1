# -*- coding: utf-8 -*-
{
    'name':
    "HMS",
    'summary':
    """
        Hotel Property Management System """,
    'description':
    """
        Hotel Property Management System :
        -Reservations, Reception, cashier, NightAudit
    """,
    'author':
    "HMS-Projects HMS, Developer Name",
    'website':
    "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/
    # addons/base/data/ir_module_category_data.xml
    # for the full list
    'category':
    'Test',
    'version':
    '1.0.0',
    # any module necessary for this one to work correctly
    'depends': [
<<<<<<< HEAD
        'base', 'graphql_base', 'contacts', 'uom', 'account', 'mail',
        'web', 'website', 'web_one2many_kanban','base_accounting_kit','web_tree_no_open'
=======
        'base', 'graphql_base', 'contacts', 'uom', 'account', 'mail', 'sale',
        'web', 'website', 'web_one2many_kanban'
>>>>>>> ab85484825706873f8134b10f985e2f87a0bd670
    ],
    "external_dependencies": {
        "python": ["graphene"]
    },
    #  'depends': ['base', 'contacts', 'uom', 'account', 'mail', 'web','website'],
    'css': ['static/src/css/room_kanban.css'],
    'qweb': ['static/src/xml/hotel_room_summary.xml'],
    # always loaded
    'data': [
        'security/hms_security.xml',
        'security/ir.model.access.csv',
        'wizard/hms_roomno_copy_wizard.xml',
        'views/hotel_views.xml',
        'views/property_onboarding_templates.xml',
        'data/hms.rsvntype.csv',
        'data/hms.rsvnstatus.csv',
        'data/hms.marketgroup.csv',
        'data/hms.marketsegment.csv',
        'data/hms.marketsource.csv',
        'data/hms.revenuetype.csv',
        'data/hms.bedtype.csv',
        'data/hms.roomlocation.csv',
        'data/hms.buildingtype.csv',
        'data/hms.building.csv',
        'data/hms.room.facility.type.csv',
        'data/hms.room.amenity.csv',
        'data/hms.roomtype.csv',
        'data/hms.roomview.csv',
        'views/hms_forecast_view.xml',
        'views/hms_bank_view.xml',
        'views/hms_format_view.xml',
        'views/hms_rule_configuration_view.xml',
        'data/hms_config_data.xml',
        'views/hms_company_view.xml',
        'views/hms_users_view.xml',
        'views/hms_country_view.xml',
        'data/res_country_data.xml',
        'views/hms_currency_view.xml',
        'data/res.country.state.csv',
        'views/hms_city_view.xml',
        'data/hms.city.csv',
        'views/hms_township_view.xml',
        'data/hms.township.csv',
        'data/res_partner_title_data.xml',
        'views/hms_company_type.xml',
        'data/hms.company.category.csv',
        'data/hms.guest.category.csv',
        'views/hms_contacts_view.xml',
        'data/ir_sequence_data.xml',
        'views/hms_profiles_req_view.xml',
        'data/hms.nationality.csv',
        'views/hms_allotment_view.xml',
        'wizard/hms_confirm_wizard_view.xml',
        'wizard/hms_unconfirm_wizard_view.xml',
        'wizard/hms_reason_wizard_view.xml',
        'wizard/hms_rersvn_wizard_view.xml',
        'wizard/hms_checkin_wizard_view.xml',
        'wizard/hms_move_room_wizard_view.xml',
        'report/confirm_letter_template.xml',
        'wizard/hms_confirm_letter_wizard_view.xml',
        'views/hms_reservation_view.xml',
        'views/room_summ_view.xml',
        'views/action_manager.xml',
        'data/hms.reasontype.csv',
        'data/hms.reason.csv',
        'views/hms_managment_report.xml',
        'wizard/hms_rc_detail_copy_wizard_view.xml',
        'views/hms_ratecode_view.xml',
        'wizard/property_report_wizard_view.xml',
        'wizard/reservation_report_wizard_view.xml',
        'wizard/in_house_report_wizard_view.xml',
        'report/reservation_report.xml',
        'report/property_template.xml',
        'report/reservation_template.xml',
        'report/expected_arrival_template.xml',
        'report/inhouse_template.xml',
        'data/hms_scheduled_actions_data.xml',
        'views/color_attribute_view.xml',
        'wizard/hms_ratecat_terminate_wizard_view.xml',
        'views/hms_rate_config.xml',
        'data/hms.reservation.fields.csv',
        'views/hms_package_config.xml',
        'data/res.lang.csv',
        'data/hms_color_attribute_data.xml',
        'report/cashier_mail_template.xml',
        'wizard/hms_invoice_send_views.xml',
        'views/hms_cashier_view.xml',
        

        #'views/views.xml',
        # 'views/templates.xml',
    ],
    # 'css': ['static/src/css/room_kanban.css'],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable':
    True,
    'application':
    True,
}
