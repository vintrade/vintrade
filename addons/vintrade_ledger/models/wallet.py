# -*- coding: utf-8 -*-
from odoo import api, fields, models


class WalletMove(models.Model):
    _name = "vin.wallet.move"
    _description = "Customer Wallet Move"
    _order = "date desc, id desc"

    partner_id = fields.Many2one("res.partner", required=True, index=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related="company_id.currency_id", store=False, readonly=True)
    date = fields.Date(required=True, default=fields.Date.context_today)
    amount = fields.Monetary("Amount", currency_field="currency_id",
                             help="Positive = credit to customer wallet; Negative = spend/allocate.")
    note = fields.Char("Note")
    move_id = fields.Many2one("account.move", string="Linked Journal Entry/Invoice", readonly=True)