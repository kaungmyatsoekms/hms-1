# -*- coding: utf-8 -*-
{
    'name': "HMS",
    'summary': """
        Hotel Property Management System """,
    'description': """
        Hotel Property Management System :
        -Reservations, Reception, cashier, NightAudit
    """,
    'author': "HMS-Projects HMS, Developer Name",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/
    # addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Test',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail'],
    #  'depends': ['base', 'contacts', 'uom', 'account', 'mail', 'web'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/hotel_views.xml',
        'views/hms_bank_view.xml',
        'views/hms_format_view.xml',
        'views/hms_rule_configuration_view.xml',
        'data/hms_config_data.xml',
        'views/hms_company_view.xml',
        #'views/views.xml',
        #'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
}
