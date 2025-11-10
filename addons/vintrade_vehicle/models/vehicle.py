# -*- coding: utf-8 -*-
import json
import logging
import re

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

try:
    import requests
except Exception:
    requests = None

_logger = logging.getLogger(__name__)

VIN_TRANS = {
    **{str(i): i for i in range(10)},
    **dict(
        A=1, B=2, C=3, D=4, E=5, F=6, G=7, H=8,
        J=1, K=2, L=3, M=4, N=5, P=7, R=9,
        S=2, T=3, U=4, V=5, W=6, X=7, Y=8, Z=9,
    ),
}
VIN_WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]
VIN_FORBIDDEN = set("IOQ")


def _vin_check_digit(vin: str):
    total = 0
    for i, ch in enumerate(vin):
        if ch in VIN_FORBIDDEN:
            return None
        val = VIN_TRANS.get(ch)
        if val is None:
            return None
        total += int(val) * VIN_WEIGHTS[i]
    remainder = total % 11
    return "X" if remainder == 10 else str(remainder)


class VinVehicle(models.Model):
    _name = "vin.vehicle"
    _description = "Vehicle (VIN)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    # Company / currency
    company_id = fields.Many2one(
        "res.company", string="Company", required=True,
        default=lambda self: self.env.company.id, index=True,
    )
    currency_id = fields.Many2one(
        "res.currency", string="Currency", required=True,
        default=lambda self: self.env.company.currency_id.id,
        help="Currency for purchase and fee amounts.",
    )

    # Identity
    name = fields.Char(
        string="Reference",
        default=lambda self: self.env["ir.sequence"].next_by_code("vin.vehicle"),
        copy=False, index=True, tracking=True,
    )
    vin = fields.Char("VIN", required=True, index=True, tracking=True)
    vin_ok = fields.Boolean("VIN Check OK", compute="_compute_vin_ok", store=True)

    # Basic info
    year = fields.Char("Year", size=4, tracking=True)
    make = fields.Char("Make", tracking=True)
    model = fields.Char("Model", tracking=True)
    trim = fields.Char("Trim")
    body_type = fields.Char("Body Type")

    # Color as dropdown
    exterior_color = fields.Selection(
        [
            ("black", "Black"), ("white", "White"), ("gray", "Gray"),
            ("silver", "Silver"), ("blue", "Blue"), ("red", "Red"),
            ("green", "Green"), ("brown", "Brown"), ("beige", "Beige"),
            ("yellow", "Yellow"), ("orange", "Orange"), ("purple", "Purple"),
            ("gold", "Gold"), ("other", "Other"),
        ],
        string="Color", tracking=True,
    )

    # Distance travelled + unit
    distance_travelled = fields.Float("Distance Travelled")
    distance_uom = fields.Selection([("km", "KM"), ("mi", "MI")], string="Unit", default="km", required=True)

    # Declarations & conditions
    branding = fields.Char("Branding / Ownership Type")
    declaration = fields.Text("Declaration")
    total_loss = fields.Boolean("Total Loss")
    warranty_cancelled = fields.Boolean("Warranty Cancelled")
    carfax_declaration = fields.Text("Carfax Declaration")
    notes = fields.Text("Notes")

    # Repair estimate
    repair_estimate = fields.Monetary("Repair Estimate ($)", currency_field="currency_id", default=0.0)

    # Purchase
    purchase_date = fields.Date("Purchase Date", tracking=True)
    seller_partner_id = fields.Many2one("res.partner", string="Seller / Counterparty")
    seller = fields.Char("Seller (Text)")
    lot_number = fields.Char("Auction Lot #")
    purchase_price = fields.Monetary("Purchase Price", currency_field="currency_id", default=0.0)
    auction_fees = fields.Monetary("Auction Fees", currency_field="currency_id", default=0.0)
    other_fees = fields.Monetary("Other Fees", currency_field="currency_id", default=0.0)
    total_cost = fields.Monetary(
        "Total Cost", currency_field="currency_id",
        compute="_compute_total_cost", store=True,
        help="Sum of price + auction fees + other fees.",
    )

    # Commercial (sale side)
    buyer_partner_id = fields.Many2one("res.partner", string="Customer (Buyer)")
    expected_sale_price = fields.Monetary("Expected Sale Price", currency_field="currency_id", tracking=True)
    sale_price = fields.Monetary("Sale Price (Actual)", currency_field="currency_id",
                                 help="Set manually or use the same price on the customer invoice.")
    profit = fields.Monetary(
        "Profit", currency_field="currency_id",
        compute="_compute_profit", store=True,
        help="(Sale Price or Expected Sale Price) − Total Cost − Repair Estimate.",
    )

    # Workflow
    state = fields.Selection(
        [
            ("draft", "Draft"), ("purchased", "Purchased"), ("enroute", "En Route"),
            ("warehouse", "At Warehouse"), ("shipped", "Shipped"),
            ("delivered", "Delivered"), ("cancelled", "Cancelled"),
        ],
        default="draft", tracking=True,
    )

    # Attachments stat button
    attachment_count = fields.Integer("Attachments", compute="_compute_attachment_count")

    # NHTSA
    vin_decoded_at = fields.Datetime("VIN decoded at", readonly=True)
    vin_decoder_raw = fields.Json("VIN decoder raw response", readonly=True)
    engine_cylinders = fields.Char("Engine Cylinders", readonly=True)
    displacement = fields.Char("Displacement (L)", readonly=True)
    fuel_type = fields.Char("Fuel Type (Primary)", readonly=True)
    fuel_type_secondary = fields.Char("Fuel Type (Secondary)", readonly=True)
    electrification_level = fields.Char("Electrification Level", readonly=True)
    manufacturer = fields.Char("Manufacturer", readonly=True)
    plant_country = fields.Char("Plant Country", readonly=True)
    is_dg = fields.Boolean(
        "Dangerous Goods", compute="_compute_is_dg", store=True,
        help="Auto-checked for EV / Hybrid / PHEV based on NHTSA fields.",
    )

    # Accounting links
    vendor_bill_id = fields.Many2one("account.move", string="Vendor Bill", readonly=True)
    customer_invoice_id = fields.Many2one("account.move", string="Customer Invoice", readonly=True)

    create_vendor_bill_on_save = fields.Boolean(
        "Auto-create Vendor Bill",
        help="If enabled, a draft vendor bill is created on save using purchase amounts."
    )

    _sql_constraints = [("vin_unique", "unique(vin)", "This VIN already exists.")]

    # --- Compute / constraints ---
    @api.depends("vin")
    def _compute_vin_ok(self):
        for rec in self:
            rec.vin_ok = False
            if rec.vin and len(rec.vin.strip()) == 17:
                v = rec.vin.strip().upper()
                if any(ch in VIN_FORBIDDEN for ch in v):
                    continue
                check = _vin_check_digit(v)
                rec.vin_ok = (check == v[8])

    @api.constrains("vin")
    def _check_vin(self):
        for rec in self:
            if not rec.vin:
                continue
            v = rec.vin.strip().upper()
            if len(v) != 17:
                raise ValidationError(_("VIN must be exactly 17 characters."))
            if any(ch in VIN_FORBIDDEN for ch in v):
                raise ValidationError(_("VIN cannot contain I, O, or Q."))
            if not re.match(r"^[A-HJ-NPR-Z0-9]{17}$", v):
                raise ValidationError(_("VIN must be alphanumeric (no special chars)."))
            check = _vin_check_digit(v)
            if check is None or check != v[8]:
                raise ValidationError(_("Invalid VIN check digit."))

    @api.constrains("year")
    def _check_year(self):
        for rec in self:
            if rec.year:
                if not re.fullmatch(r"\d{4}", rec.year):
                    raise ValidationError(_("Year must be exactly 4 digits."))
                if not (1950 <= int(rec.year) <= 2035):
                    raise ValidationError(_("Year must be between 1950 and 2035."))

    @api.depends("purchase_price", "auction_fees", "other_fees")
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = (rec.purchase_price or 0.0) + (rec.auction_fees or 0.0) + (rec.other_fees or 0.0)

    @api.depends("sale_price", "expected_sale_price", "total_cost", "repair_estimate")
    def _compute_profit(self):
        for rec in self:
            sale = rec.sale_price if rec.sale_price not in (None, 0.0) else (rec.expected_sale_price or 0.0)
            rec.profit = sale - (rec.total_cost or 0.0) - (rec.repair_estimate or 0.0)

    @api.depends("electrification_level", "fuel_type", "fuel_type_secondary")
    def _compute_is_dg(self):
        kw = ("electric", "hybrid", "plug-in", "plug in", "phev", "ev", "bev", "hev")
        for rec in self:
            elec = (rec.electrification_level or "").strip().lower()
            ft1 = (rec.fuel_type or "").strip().lower()
            ft2 = (rec.fuel_type_secondary or "").strip().lower()
            rec.is_dg = bool(elec) or any(k in ft1 for k in kw) or any(k in ft2 for k in kw)

    @api.depends()
    def _compute_attachment_count(self):
        for rec in self:
            rec.attachment_count = self.env["ir.attachment"].search_count(
                [("res_model", "=", self._name), ("res_id", "=", rec.id)]
            )

    # --- NHTSA decode helpers ---
    @api.model
    def _safe_get(self, dct, key):
        v = (dct or {}).get(key)
        return v if v not in (None, "", "0") else False

    def _nhtsa_decode(self, vin):
        vin = (vin or "").strip().upper()
        if not vin:
            raise UserError(_("VIN is empty"))
        url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValuesExtended/{vin}?format=json"
        try:
            if requests:
                resp = requests.get(url, timeout=10)
                resp.raise_for_status()
                data = resp.json()
            else:
                from urllib.request import urlopen
                import ssl
                ctx = ssl.create_default_context()
                with urlopen(url, timeout=15, context=ctx) as f:
                    data = json.loads(f.read().decode("utf-8"))
        except Exception as e:
            _logger.exception("NHTSA decode failed for VIN %s", vin)
            raise UserError(_("Could not reach NHTSA decode service: %s") % e)
        results = data.get("Results") or []
        if not results:
            raise UserError(_("No decode results returned for VIN %s") % vin)
        return results[0]

    def _vals_from_nhtsa(self, result):
        vals = {}
        vals["make"] = self._safe_get(result, "Make") or vals.get("make")
        vals["model"] = self._safe_get(result, "Model") or vals.get("model")
        year = self._safe_get(result, "ModelYear")
        if year:
            vals["year"] = str(year)
        vals["body_type"] = self._safe_get(result, "BodyClass")
        vals["manufacturer"] = self._safe_get(result, "Manufacturer")
        vals["plant_country"] = self._safe_get(result, "PlantCountry")
        vals["engine_cylinders"] = self._safe_get(result, "EngineCylinders")
        vals["displacement"] = self._safe_get(result, "DisplacementL")
        vals["fuel_type"] = self._safe_get(result, "FuelTypePrimary")
        vals["fuel_type_secondary"] = self._safe_get(result, "FuelTypeSecondary")
        vals["electrification_level"] = self._safe_get(result, "ElectrificationLevel")
        vals["vin_decoder_raw"] = result
        vals["vin_decoded_at"] = fields.Datetime.now()
        return vals

    def action_decode_vin(self):
        self.ensure_one()
        result = self._nhtsa_decode(self.vin)
        self.write(self._vals_from_nhtsa(result))
        return {
            "type": "ir.actions.client", "tag": "display_notification",
            "params": {"title": _("VIN decoded"), "message": _("Vehicle fields updated from NHTSA."),
                       "type": "success", "sticky": False}
        }

    @api.onchange("vin")
    def _onchange_vin_autodecode(self):
        if not self.vin:
            return
        v = self.vin.strip().upper()
        if len(v) != 17:
            return
        check = _vin_check_digit(v)
        if check is None or check != v[8]:
            return
        try:
            result = self._nhtsa_decode(v)
            vals = self._vals_from_nhtsa(result)
            for k, val in vals.items():
                setattr(self, k, val)
        except Exception:
            _logger.exception("Onchange VIN autodecode failed for %s", v)

    @api.model
    def create(self, vals):
        rec = super().create(vals)
        if vals.get("create_vendor_bill_on_save"):
            try:
                rec._create_vendor_bill()
            except Exception as e:
                _logger.exception("Auto vendor bill creation failed")
                rec.message_post(body=_("Vendor bill could not be created automatically: %s") % e)

        vin = vals.get("vin")
        if vin and len(vin.strip()) == 17 and _vin_check_digit(vin.strip().upper()) == vin.strip().upper()[8]:
            try:
                result = rec._nhtsa_decode(vin)
                vals2 = rec._vals_from_nhtsa(result)
                super(VinVehicle, rec.with_context(skip_autodecode=True)).write(vals2)
            except Exception:
                _logger.exception("Auto-decode on create failed for %s", vin)
        return rec

    def write(self, vals):
        res = super().write(vals)
        if vals.get("create_vendor_bill_on_save"):
            for rec in self:
                if not rec.vendor_bill_id:
                    try:
                        rec._create_vendor_bill()
                    except Exception as e:
                        _logger.exception("Vendor bill creation failed on write")
                        rec.message_post(body=_("Vendor bill could not be created: %s") % e)

        if "vin" in vals and not self.env.context.get("skip_autodecode"):
            for rec in self:
                vin = rec.vin and rec.vin.strip()
                if vin and len(vin) == 17 and _vin_check_digit(vin.upper()) == vin.upper()[8]:
                    try:
                        result = rec._nhtsa_decode(vin)
                        vals2 = rec._vals_from_nhtsa(result)
                        super(VinVehicle, rec.with_context(skip_autodecode=True)).write(vals2)
                    except Exception:
                        _logger.exception("Auto-decode on write failed for %s", vin)
        return res

    # --- Accounting helpers / actions ---
    def _get_default_expense_account(self):
        account = self.env["account.account"].search([
            ("account_type", "=", "expense"),
            ("company_id", "=", self.company_id.id),
        ], limit=1)
        if not account:
            raise UserError(_("Please configure at least one Expense account for company %s.") % self.company_id.display_name)
        return account

    def _get_default_income_account(self):
        account = self.env["account.account"].search([
            ("account_type", "=", "income"),
            ("company_id", "=", self.company_id.id),
        ], limit=1)
        if not account:
            raise UserError(_("Please configure at least one Income account for company %s.") % self.company_id.display_name)
        return account

    def action_open_attachments(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Documents"),
            "res_model": "ir.attachment",
            "view_mode": "kanban,tree,form",
            "domain": [("res_model", "=", self._name), ("res_id", "=", self.id)],
            "context": {"default_res_model": self._name, "default_res_id": self.id},
            "target": "current",
        }

    def action_create_vendor_bill(self):
        self.ensure_one()
        self._create_vendor_bill()
        return {"type": "ir.actions.act_window", "res_model": "account.move", "view_mode": "form", "res_id": self.vendor_bill_id.id}

    def _create_vendor_bill(self):
        self.ensure_one()
        if self.vendor_bill_id:
            return
        if not self.seller_partner_id:
            raise UserError(_("Select a Seller / Counterparty to create a vendor bill."))
        amount = (self.purchase_price or 0.0) + (self.auction_fees or 0.0) + (self.other_fees or 0.0)
        if not amount:
            raise UserError(_("No purchase amounts present (price/fees)."))
        expense_account = self._get_default_expense_account()
        move = self.env["account.move"].create({
            "move_type": "in_invoice",
            "partner_id": self.seller_partner_id.id,
            "invoice_date": self.purchase_date or fields.Date.context_today(self),
            "currency_id": self.currency_id.id,
            "invoice_line_ids": [(0, 0, {
                "name": f"Vehicle {self.vin} purchase & fees",
                "quantity": 1.0, "price_unit": amount, "account_id": expense_account.id,
            })],
            "invoice_origin": self.name,
        })
        self.vendor_bill_id = move.id
        self.message_post(body=_("Vendor Bill created: %s") % (move.name or move.display_name))

    def action_create_customer_invoice(self):
        """Create a draft customer invoice for this vehicle."""
        self.ensure_one()
        if self.customer_invoice_id:
            return {"type": "ir.actions.act_window", "res_model": "account.move", "view_mode": "form", "res_id": self.customer_invoice_id.id}

        if not self.buyer_partner_id:
            raise UserError(_("Select a Customer (Buyer) before creating an invoice."))

        amount = self.sale_price or self.expected_sale_price
        if not amount:
            raise UserError(_("Set a Sale Price or Expected Sale Price."))

        income_account = self._get_default_income_account()
        move = self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": self.buyer_partner_id.id,
            "invoice_date": fields.Date.context_today(self),
            "currency_id": self.currency_id.id,
            "invoice_line_ids": [(0, 0, {
                "name": f"Vehicle {self.make or ''} {self.model or ''} {self.year or ''} — VIN {self.vin}",
                "quantity": 1.0, "price_unit": amount, "account_id": income_account.id,
            })],
            "invoice_origin": self.name,
        })
        self.customer_invoice_id = move.id
        # Optionally set sale_price from created document’s line (keeps Profit consistent)
        self.sale_price = amount
        self.message_post(body=_("Customer Invoice created: %s") % (move.name or move.display_name))
        return {"type": "ir.actions.act_window", "res_model": "account.move", "view_mode": "form", "res_id": move.id}

    # State convenience
    def action_set_state(self, new_state): self.write({"state": new_state})
    def action_mark_purchased(self): self.action_set_state("purchased")
    def action_mark_enroute(self): self.action_set_state("enroute")
    def action_mark_warehouse(self): self.action_set_state("warehouse")
    def action_mark_shipped(self): self.action_set_state("shipped")
    def action_mark_delivered(self): self.action_set_state("delivered")