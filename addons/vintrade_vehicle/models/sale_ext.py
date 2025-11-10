# -*- coding: utf-8 -*-
from odoo import api, fields, models

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    vehicle_id = fields.Many2one(
        "vin.vehicle",
        string="Vehicle",
        domain=[("state", "!=", "cancelled")],
        help="Link this order line to a specific vehicle (by VIN)."
    )

    @api.onchange("vehicle_id")
    def _onchange_vehicle_id(self):
        if self.vehicle_id:
            v = self.vehicle_id
            self.name = (f"{(v.make or '').upper()} {(v.model or '')}".strip()
                         + (f" {v.year}" if v.year else "")
                         + f" — VIN {v.vin}")
            if v.expected_sale_price:
                self.price_unit = v.expected_sale_price