# -*- coding: utf-8 -*-
{
    'name': "Repair Management",
    'summary': """Repair Management""",
    'description': """Repair Management""",
    'author': "CubicIt Egypt",
    'website': "http://www.cubicit-eg.com",
    'category': 'others',
    'version': '0.1',
    'depends': ['base', 'base_setup', 'contacts', 'stock', 'sale', 'purchase', 'account', 'calendar', 'portal', 'utm'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/sequence.xml',
        'views/menu_workshop.xml',
        'views/menu_backoffice.xml',
        'views/work_order.xml',
        'views/workshop_ticket.xml',
        'views/machine.xml',
        'views/stock_views.xml',
        'views/workshop_views.xml',
        'views/order_inspect.xml',
        'views/order_estimate.xml',
        'views/sale_order.xml',
        'report/order_template.xml',
        'report/inspection_template.xml',
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
