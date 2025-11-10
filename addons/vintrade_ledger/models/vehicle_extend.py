# -*- coding: utf-8 -*-
from odoo import api, models, _
from odoo.exceptions import UserError


class VinVehicle(models.Model):
    _inherit = "vin.vehicle"

    def action_create_customer_invoice(self):
        self.ensure_one()
        partner = self.buyer_partner_id
        if not partner:
            return super().action_create_customer_invoice()

        if partner.on_hold:
            raise UserError(_("Customer is on hold; cannot create an invoice."))

        # live receivable balance for this partner/company
        aml = self.env["account.move.line"].search_read([
            ("partner_id", "=", partner.id),
            ("company_id", "=", self.company_id.id),
            ("account_id.account_type", "=", "asset_receivable"),
            ("parent_state", "!=", "cancel"),
        ], ["balance"])
        current_ar = sum(x["balance"] for x in aml)  # balance is signed in company currency

        # credit limit check (wallet can offset)
        limit = partner.credit_limit or 0.0
        wallet = partner.wallet_balance or 0.0
        projected = current_ar + (self.sale_price or self.expected_sale_price or 0.0) - wallet

        if limit and projected > limit:
            raise UserError(_(
                "Credit limit exceeded.\n\n"
                "Customer: %(cust)s\n"
                "Limit: %(lim).2f\n"
                "Current AR: %(ar).2f\n"
                "Wallet: %(wal).2f\n"
                "Projected after this invoice: %(proj).2f"
            ) % {
                "cust": partner.display_name,
                "lim": limit,
                "ar": current_ar,
                "wal": wallet,
                "proj": projected,
            })

        return super().action_create_customer_invoice()