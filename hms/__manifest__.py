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
    '0.1',

    # any module necessary for this one to work correctly
    'depends':
    ['base','graphql_base', 'contacts', 'uom', 'account', 'mail', 'point_of_sale', 'web','website'],
    "external_dependencies": {"python": ["graphene"]},
    #  'depends': ['base', 'contacts', 'uom', 'account', 'mail', 'web','website'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/hms_roomno_copy_wizard.xml',
        'views/hotel_views.xml',
        'data/rsvn.type.csv',
        'data/rsvn.status.csv',
        'data/market.group.csv',
        'data/market.segment.csv',
        'data/market.source.csv',
        'data/revenue.type.csv',
        'data/bed.type.csv',
        'data/hms.calculation.method.csv',
        'data/hms.charge_types.csv',
        'data/room.amenity.csv',
        'data/room.facility.type.csv',
        'data/room.type.csv',
        'views/hms_forecast_view.xml',
        'views/hms_bank_view.xml',
        'views/hms_format_view.xml',
        'views/hms_rule_configuration_view.xml',
        'data/hms_config_data.xml',
        'views/hms_company_view.xml',
        'views/hms_users_view.xml',
        'views/hms_country_view.xml',
        'data/res_country_data.xml',
        'data/res.country.state.csv',
        'views/hms_city_view.xml',
        'data/hms.city.csv',
        'views/hms_township_view.xml',
        'data/hms.township.csv',
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
        'views/hms_reservation_view.xml',
        'data/hms.reasontype.csv',
        'data/hms.reason.csv',
        'views/hms_charge_type.xml',
        'views/hms_package_charge_line.xml',
        'views/hms_managment_report.xml',
        'views/hms_ratecode_view.xml',
        'report/property_template.xml',
        'wizard/reservation_report_wizard_view.xml',
        'report/reservation_report.xml',
        'report/reservation_template.xml',
        'report/expected_arrival_template.xml',
        'data/hms_scheduled_actions_data.xml',
        'views/color_attribute_view.xml',
        # 'views/report_hms_reservation_view.xml',
        #'views/views.xml',
        # 'views/templates.xml',
    ],
    'css': ['static/src/css/room_kanban.css'],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable':
    True,
    'application':
    True,
}
