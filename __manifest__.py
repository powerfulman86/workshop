# -*- coding: utf-8 -*-
{
    'name': "Repair Management",
    'summary': """Repair Management""",
    'description': """Repair Management""",
    'author': "CubicIt Egypt",
    'website': "http://www.cubicit-eg.com",
    'category': 'others',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/product_brand_view.xml',
        'views/product_model.xml',
        'views/product_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
