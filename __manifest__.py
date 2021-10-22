# -*- coding: utf-8 -*-
{
    'name': "Repair Management",
    'summary': """Repair Management""",
    'description': """Repair Management""",
    'author': "CubicIt Egypt",
    'website': "http://www.cubicit-eg.com",
    'category': 'others',
    'version': '0.1',
    'depends': ['base', 'stock', 'sale'],
    'data': [
        'data/data.xml',
        'data/sequence.xml',
        'security/ir.model.access.csv',
        'views/menus.xml',
        'views/machine.xml',
        'views/product_brand_view.xml',
        'views/product_model.xml',
        'views/product_template.xml',
        'views/work_order.xml',
        'views/sale_order.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
