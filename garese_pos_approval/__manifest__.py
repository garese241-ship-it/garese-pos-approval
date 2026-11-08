{
    'name': 'GARESE POS Approvals',
    'version': '17.0.1.0.0',
    'category': 'Sales/Point of Sale',
    'summary': "Discounts, price changes, refunds and cancellations approved by a manager's password on the register",
    'description': """
GARESE POS Approvals
====================
Replaces ``garese_pos_secure_cash``. A cashier needs a Point of Sale manager to
type his Odoo password on the register to give a discount, change a price,
refund, or cancel an order line or an order. Each option is set per Point of
Sale. The controls are repeated on the server: a modified register cannot skip
them for discounts and refunds. Every approval is kept in a log.
""",
    'author': 'GARESE',
    'website': 'https://garese.ga',
    'license': 'OPL-1',
    'depends': ['point_of_sale', 'garese_pos'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_approval_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'garese_pos_approval/static/src/app/**/*',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
}
