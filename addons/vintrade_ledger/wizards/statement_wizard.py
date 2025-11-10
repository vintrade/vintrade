# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StatementWizard(models.TransientModel):
    _name = "vin.statement.wizard"
    _description = "Customer Statement Wizard"

    partner_id = fields.Many2one("res.partner", required=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    date_to = fields.Date("As of", required=True, default=fields.Date.context_today)
    include_all = fields.Boolean("Include fully paid items", default=False)

    def action_print(self):
        self.ensure_one()
        return self.env.ref("vintrade_ledger.report_customer_statement").report_action(self)