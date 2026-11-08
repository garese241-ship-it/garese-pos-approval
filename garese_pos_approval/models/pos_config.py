from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    gpa_discount_requires_manager = fields.Boolean(
        string='Discounts Need a Manager',
        help="A cashier needs a manager's password to give a discount (line or order).")
    gpa_price_requires_manager = fields.Boolean(
        string='Price Changes Need a Manager',
        help="A cashier needs a manager's password to change the price of a line on the register.")
    gpa_refund_requires_manager = fields.Boolean(
        string='Refunds Need a Manager',
        help="A cashier needs a manager's password to refund an order.")
    gpa_cancel_requires_manager = fields.Boolean(
        string='Cancellations Need a Manager',
        help="A cashier needs a manager's password to delete an order line or an order.")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_gpa_discount_requires_manager = fields.Boolean(
        related='pos_config_id.gpa_discount_requires_manager', readonly=False)
    pos_gpa_price_requires_manager = fields.Boolean(
        related='pos_config_id.gpa_price_requires_manager', readonly=False)
    pos_gpa_refund_requires_manager = fields.Boolean(
        related='pos_config_id.gpa_refund_requires_manager', readonly=False)
    pos_gpa_cancel_requires_manager = fields.Boolean(
        related='pos_config_id.gpa_cancel_requires_manager', readonly=False)
