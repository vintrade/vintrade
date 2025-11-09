# -*- coding: utf-8 -*-
import json
import logging
import re

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

try:
    import requests  # used if available
except Exception:
    requests = None

_logger = logging.getLogger(__name__)

# --- VIN helpers (check digit) ---
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

    # Identity
    name = fields.Char(
        string="Reference",
        default=lambda self: self.env["ir.sequence"].next_by_code("vin.vehicle"),
        copy=False,
        index=True,
        tracking=True,
    )
    vin = fields.Char("VIN", required=True, index=True, tracking=True)
    vin_ok = fields.Boolean("VIN Check OK", compute="_compute_vin_ok", store=True)

    # Basic info
    year = fields.Char("Year", size=4, tracking=True)  # Char to avoid 2,017 formatting
    make = fields.Char("Make", tracking=True)
    model = fields.Char("Model", tracking=True)
    trim = fields.Char("Trim")
    body_type = fields.Char("Body Type")
    exterior_color = fields.Char("Color")
    odometer = fields.Float("Odometer", help="In miles or km (specify in Notes)")
    notes = fields.Text("Notes")

    # Parties / auction
    client_id = fields.Many2one("res.partner", string="Client")
    seller = fields.Char("Seller / Auction")
    lot_number = fields.Char("Auction Lot #")

    # Title
    title_status = fields.Selection(
        [
            ("clean", "Clean"),
            ("salvage", "Salvage"),
            ("rebuilt", "Rebuilt"),
            ("parts", "For Parts"),
            ("other", "Other"),
        ],
        string="Title Status",
    )
    title_province = fields.Char("Title Province/State")
    title_received = fields.Boolean("Title Received")
    title_received_date = fields.Date("Title Received On")

    # Workflow
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("purchased", "Purchased"),
            ("enroute", "En Route"),
            ("warehouse", "At Warehouse"),
            ("shipped", "Shipped"),
            ("delivered", "Delivered"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        tracking=True,
    )

    # Attachments stat button
    attachment_count = fields.Integer("Attachments", compute="_compute_attachment_count")

    # NHTSA decoder fields
    vin_decoded_at = fields.Datetime("VIN decoded at", readonly=True)
    vin_decoder_raw = fields.Json("VIN decoder raw response", readonly=True)

    engine_cylinders = fields.Char("Engine Cylinders", readonly=True)
    displacement = fields.Char("Displacement (L)", readonly=True)

    fuel_type = fields.Char("Fuel Type (Primary)", readonly=True)
    fuel_type_secondary = fields.Char("Fuel Type (Secondary)", readonly=True)
    electrification_level = fields.Char("Electrification Level", readonly=True)

    manufacturer = fields.Char("Manufacturer", readonly=True)
    plant_country = fields.Char("Plant Country", readonly=True)

    # Dangerous Goods (auto)
    is_dg = fields.Boolean(
        "Dangerous Goods",
        compute="_compute_is_dg",
        store=True,
        help="Auto-checked for EV / Hybrid / PHEV based on NHTSA fields.",
    )

    _sql_constraints = [
        ("vin_unique", "unique(vin)", "This VIN already exists."),
    ]

    # --- Computations / constraints ---
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

    @api.depends()
    def _compute_attachment_count(self):
        for rec in self:
            rec.attachment_count = self.env["ir.attachment"].search_count(
                [("res_model", "=", self._name), ("res_id", "=", rec.id)]
            )

    @api.depends("electrification_level", "fuel_type", "fuel_type_secondary")
    def _compute_is_dg(self):
        """Mark as Dangerous Goods when any electrification present or fuel mentions."""
        kw = ("electric", "hybrid", "plug-in", "plug in", "phev", "ev", "bev", "hev")
        for rec in self:
            elec = (rec.electrification_level or "").strip().lower()
            ft1 = (rec.fuel_type or "").strip().lower()
            ft2 = (rec.fuel_type_secondary or "").strip().lower()
            rec.is_dg = bool(elec) or any(k in ft1 for k in kw) or any(k in ft2 for k in kw)

    # --- UI helpers ---
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

    # Simple state buttons
    def action_set_state(self, new_state):
        for rec in self:
            rec.state = new_state

    def action_mark_purchased(self):
        self.action_set_state("purchased")

    def action_mark_enroute(self):
        self.action_set_state("enroute")

    def action_mark_warehouse(self):
        self.action_set_state("warehouse")

    def action_mark_shipped(self):
        self.action_set_state("shipped")

    def action_mark_delivered(self):
        self.action_set_state("delivered")

    # --- VIN decoding helpers ---
    @api.model
    def _safe_get(self, dct, key):
        v = (dct or {}).get(key)
        return v if v not in (None, "", "0") else False

    def _nhtsa_decode(self, vin):
        if not vin:
            raise UserError(_("VIN is empty"))
        vin = vin.strip().upper()
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
        """Build a values dict from an NHTSA result row."""
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

    # --- Button (manual refresh) ---
    def action_decode_vin(self):
        self.ensure_one()
        try:
            result = self._nhtsa_decode(self.vin)
        except UserError:
            raise
        except Exception as e:
            _logger.exception("VIN decode unexpected error")
            raise UserError(_("VIN decode failed: %s") % e)

        vals = self._vals_from_nhtsa(result)
        self.write(vals)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("VIN decoded"),
                "message": _("Vehicle fields updated from NHTSA."),
                "type": "success",
                "sticky": False,
            },
        }

    # --- Auto-decode on form change / create / VIN change ---
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
            # Onchange should never raise; just log.
            _logger.exception("Onchange VIN autodecode failed for %s", v)
            return

    @api.model
    def create(self, vals):
        rec = super().create(vals)
        vin = vals.get("vin")
        if vin and len(vin.strip()) == 17:
            v = vin.strip().upper()
            if _vin_check_digit(v) == v[8]:
                try:
                    result = rec._nhtsa_decode(v)
                    vals2 = rec._vals_from_nhtsa(result)
                    # bypass our write() override to avoid recursion
                    super(VinVehicle, rec.with_context(skip_autodecode=True)).write(vals2)
                except Exception:
                    _logger.exception("Auto-decode on create failed for %s", vin)
        return rec

    def write(self, vals):
        res = super().write(vals)
        if "vin" in vals and not self.env.context.get("skip_autodecode"):
            for rec in self:
                vin = rec.vin and rec.vin.strip()
                if vin and len(vin) == 17:
                    v = vin.upper()
                    if _vin_check_digit(v) == v[8]:
                        try:
                            result = rec._nhtsa_decode(v)
                            vals2 = rec._vals_from_nhtsa(result)
                            # bypass our own write again
                            super(VinVehicle, rec.with_context(skip_autodecode=True)).write(vals2)
                        except Exception:
                            _logger.exception("Auto-decode on write failed for %s", vin)
        return res