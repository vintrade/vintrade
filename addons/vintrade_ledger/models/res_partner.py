# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools.misc import frozendict


class ResPartner(models.Model):
    _inherit = "res.partner"

    credit_limit = fields.Monetary(
        string="Credit Limit",
        currency_field="company_currency_id",
        help="Maximum outstanding receivable allowed for this customer."
    )
    on_hold = fields.Boolean(
        string="On Hold",
        help="If checked, new customer invoices are blocked."
    )
    wallet_balance = fields.Monetary(
        string="Wallet Balance",
        currency_field="company_currency_id",
        compute="_compute_wallet_balance",
        help="Sum of wallet entries for this customer (per company)."
    )
    company_currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        string="Company Currency",
        store=False,
        readonly=True,
    )

    wallet_move_count = fields.Integer(compute="_compute_wallet_move_count")

    def _compute_wallet_balance(self):
        for partner in self:
            amount = 0.0
            Wallet = self.env["vin.wallet.move"].with_context(
                company_id=partner.company_id.id
            )
            amount = sum(Wallet.search([
                ("partner_id", "=", partner.id),
                ("company_id", "=", partner.company_id.id),
            ]).mapped("amount"))
            partner.wallet_balance = amount

    def _compute_wallet_move_count(self):
        for p in self:
            p.wallet_move_count = self.env["vin.wallet.move"].search_count([
                ("partner_id", "=", p.id),
                ("company_id", "=", p.company_id.id),
            ])

    def action_open_wallet(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Wallet"),
            "res_model": "vin.wallet.move",
            "view_mode": "tree,form",
            "domain": [("partner_id", "=", self.id)],
            "context": frozendict({
                "default_partner_id": self.id,
                "default_company_id": self.company_id.id,
            }),
        }

    def action_open_statement_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Customer Statement"),
            "res_model": "vin.statement.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_partner_id": self.id,
                "default_company_id": self.company_id.id,
            },
        }