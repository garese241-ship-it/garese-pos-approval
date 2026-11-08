/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { GpManagerAuthPopup } from "@garese_pos/app/cashier_control/manager_auth_popup";

const FLAGS = {
    discount: "gpa_discount_requires_manager",
    price: "gpa_price_requires_manager",
    refund: "gpa_refund_requires_manager",
    cancel: "gpa_cancel_requires_manager",
};

patch(PosStore.prototype, {
    /** Does this action need a manager's password for the current user? */
    gpaNeeds(purpose) {
        return Boolean(this.config[FLAGS[purpose]]) && !this.gpIsManager;
    },
    /**
     * Resolves to { ok, id }: ok is true when the action is allowed (not needed,
     * already approved for this order, or a manager just typed his password).
     * The server records the approval and checks it again when the order is saved.
     */
    async gpaRequire(purpose, title, body = "", orderUid = false) {
        if (!this.gpaNeeds(purpose)) {
            return { ok: true };
        }
        const session = this.pos_session.id;
        try {
            if (orderUid && (await this.orm.call("pos.session", "gpa_has_approval", [[session], purpose, orderUid]))) {
                return { ok: true };
            }
            const managers = await this.orm.call("pos.session", "gp_get_managers", [[session]]);
            if (!managers.length) {
                await this.popup.add(ErrorPopup, {
                    title: _t("No manager"),
                    body: _t("No user is manager of this Point of Sale: nobody can authorize this action."),
                });
                return { ok: false };
            }
            const { confirmed, payload } = await this.popup.add(GpManagerAuthPopup, {
                title,
                body,
                managers,
                purpose,
                authorize: (userId, password) =>
                    this.orm.call("pos.session", "gpa_authorize", [
                        [session],
                        userId,
                        password,
                        purpose,
                        orderUid,
                    ]),
            });
            return confirmed ? { ok: true, id: payload.id } : { ok: false };
        } catch {
            await this.popup.add(ErrorPopup, {
                title: _t("No connection"),
                body: _t("A manager's authorization needs the server. Check the network and try again."),
            });
            return { ok: false };
        }
    },
});

patch(ProductScreen.prototype, {
    async onNumpadClick(buttonValue) {
        if (["discount", "price"].includes(buttonValue) && this.currentOrder) {
            const purpose = buttonValue;
            const { ok } = await this.pos.gpaRequire(
                purpose,
                purpose === "discount" ? _t("Discount approved by a manager") : _t("Price change approved by a manager"),
                _t("A manager must type his password to do this."),
                this.currentOrder.name
            );
            if (!ok) {
                return;
            }
        }
        return super.onNumpadClick(...arguments);
    },
    async updateSelectedOrderline({ buffer }) {
        // buffer === null: the key removes the selected line
        if (buffer === null && this.pos.numpadMode === "quantity" && this.currentOrder?.get_selected_orderline()) {
            const { ok } = await this.pos.gpaRequire(
                "cancel",
                _t("Cancellation approved by a manager"),
                _t("A manager must type his password to delete this line."),
                this.currentOrder.name
            );
            if (!ok) {
                this.numberBuffer.reset();
                return;
            }
        }
        return super.updateSelectedOrderline(...arguments);
    },
});

patch(TicketScreen.prototype, {
    async _onBeforeDeleteOrder(order) {
        if (order.get_orderlines().length) {
            const { ok } = await this.pos.gpaRequire(
                "cancel",
                _t("Cancellation approved by a manager"),
                _t("A manager must type his password to delete this order."),
                order.name
            );
            if (!ok) {
                return false;
            }
        }
        return super._onBeforeDeleteOrder(...arguments);
    },
    async onDoRefund() {
        const { ok, id } = await this.pos.gpaRequire(
            "refund",
            _t("Refund approved by a manager"),
            _t("A manager must type his password to refund.")
        );
        if (!ok) {
            return;
        }
        const result = await super.onDoRefund(...arguments);
        // the refund order exists now: attach the approval to it
        const current = this.pos.get_order();
        if (id && current) {
            try {
                await this.orm.call("pos.session", "gpa_bind", [[this.pos.pos_session.id], id, current.name]);
            } catch {
                // the server checks again when the order is saved
            }
        }
        return result;
    },
});

patch(PaymentScreen.prototype, {
    async validateOrder() {
        const order = this.currentOrder;
        const discountProduct = this.pos.config.discount_product_id?.[0];
        const hasDiscount = order
            .get_orderlines()
            .some((line) => line.get_discount() > 0 || (discountProduct && line.get_product().id === discountProduct));
        if (hasDiscount) {
            const { ok } = await this.pos.gpaRequire(
                "discount",
                _t("Discount approved by a manager"),
                _t("This order has a discount: a manager must type his password."),
                order.name
            );
            if (!ok) {
                return;
            }
        }
        return super.validateOrder(...arguments);
    },
});
