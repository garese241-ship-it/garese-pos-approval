"""Approvals typed by a manager on the register, kept as a log and checked by the server."""
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

PURPOSES = [
    ('discount', 'Discount'),
    ('price', 'Price change'),
    ('refund', 'Refund'),
    ('cancel', 'Cancellation'),
]


class GpaApproval(models.Model):
    _name = 'gpa.approval'
    _description = 'POS manager approval'
    _order = 'id desc'

    session_id = fields.Many2one('pos.session', required=True, readonly=True, index=True, ondelete='cascade')
    config_id = fields.Many2one(related='session_id.config_id', store=True, readonly=True)
    purpose = fields.Selection(PURPOSES, required=True, readonly=True)
    order_uid = fields.Char(string='Order Reference', readonly=True, index=True,
                            help="Reference of the order on the register (e.g. Order 00012-001-0004).")
    manager_id = fields.Many2one('res.users', string='Approved By', required=True, readonly=True)
    cashier_id = fields.Many2one('res.users', string='Cashier', required=True, readonly=True)
    note = fields.Char(readonly=True)


class PosSession(models.Model):
    _inherit = 'pos.session'

    def gpa_authorize(self, user_id, password, purpose, order_uid=False, note=False):
        """A manager types his Odoo password: the approval is recorded."""
        self.ensure_one()
        if purpose not in dict(PURPOSES):
            return {'ok': False, 'message': _("Unknown action.")}
        manager, error = self._gp_verify_manager(user_id, password, purpose)
        if error:
            return error
        approval = self.env['gpa.approval'].sudo().create({
            'session_id': self.id,
            'purpose': purpose,
            'order_uid': order_uid or False,
            'manager_id': manager.id,
            'cashier_id': self.env.user.id,
            'note': note or False,
        })
        return {'ok': True, 'id': approval.id, 'name': manager.name}

    def gpa_bind(self, approval_id, order_uid):
        """Attach an approval requested before its order exists (refunds)."""
        self.ensure_one()
        approval = self.env['gpa.approval'].sudo().search([
            ('id', '=', approval_id), ('session_id', '=', self.id),
            ('cashier_id', '=', self.env.user.id), ('order_uid', '=', False)])
        approval.order_uid = order_uid
        return True

    def gpa_has_approval(self, purpose, order_uid):
        self.ensure_one()
        return bool(self.env['gpa.approval'].sudo().search_count([
            ('session_id', '=', self.id), ('purpose', '=', purpose), ('order_uid', '=', order_uid)]))


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def _gpa_needed(self, data, config):
        """Approvals this order needs, from what the server can see in it."""
        needs = set()
        lines = [line[2] for line in (data.get('lines') or []) if len(line) > 2 and isinstance(line[2], dict)]
        discount_product = getattr(config, 'discount_product_id', False)
        if config.gpa_discount_requires_manager and any(
                (line.get('discount') or 0) > 0
                or (discount_product and line.get('product_id') == discount_product.id)
                for line in lines):
            needs.add('discount')
        if config.gpa_refund_requires_manager and any(
                line.get('refunded_orderline_id') or (line.get('qty') or 0) < 0 for line in lines):
            needs.add('refund')
        return needs

    @api.model
    def _process_order(self, order, draft, existing_order):
        data = order['data']
        session = self.env['pos.session'].browse(data['pos_session_id'])
        config = session.config_id
        if not self.env.su and not session._gp_is_manager():
            missing = []
            for purpose in sorted(self._gpa_needed(data, config)):
                if not session.gpa_has_approval(purpose, data.get('name')):
                    missing.append(dict(PURPOSES)[purpose])
            if missing:
                raise UserError(_(
                    "A manager must approve this order (%(what)s) before it is saved.",
                    what=", ".join(missing)))
        return super()._process_order(order, draft, existing_order)
