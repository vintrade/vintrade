# -*- coding: utf-8 -*-
from odoo import fields, models

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    vehicle_id = fields.Many2one(
        "vin.vehicle",
        string="Vehicle",
        help="Link this invoice line to a specific vehicle (by VIN)."
    )