# -*- coding: utf-8 -*-
# Copyright 2016, 2020 Openworx - Mario Gielissen
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "HMS Backend Theme",
    "summary": "HMS Backend Theme",
    "version": "13.0.0.3",
    "category": "Theme/Backend",
    "website": "http://www.zandotech.com",
	"description": """
		HMS Backend Theme for V13.00
    """,
	'images':[
        'images/screen.png'
	],
    "author": "Openworx",
    "license": "LGPL-3",
    "installable": True,
    "depends": [
        'web',
        'ow_web_responsive',

    ],
    "data": [
        'views/assets.xml',
		# 'views/res_company_view.xml',
		# 'views/users.xml',
        	'views/sidebar.xml',
    ],
    #'live_test_url': 'https://youtu.be/JX-ntw2ORl8'

}

