# -*- coding: utf-8 -*-
{
    'name': "estate",

    'summary': """
        
    """,

    'description': """
         
    """,

    'author': "Odoo",
    'website': "https://www.odoo.com",

    'category': 'Tutorials/Estate',
    'version': '0.1',

    # any module necessary for this one to work correctly
    # 'depends': ['base_setup', 'onboarding', 'product', 'analytic', 'portal', 'digest'],
    'application': True,
    'installable': True,
    'data': [
        'security/ir.model.access.csv',
        'reports/estate_property_offers_reports.xml',
        'views/estate_property_offer_views.xml',
        'views/estate_property_type_views.xml',
        'views/estate_property_views.xml',
        'views/res_users_views.xml',
        'views/menu.xml',

        'reports/estate_property_offers_templates.xml',
    ],
    'license': 'AGPL-3'
}
