{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 from odoo import api, fields, models, _\
from odoo.exceptions import ValidationError\
import re\
\
\
class VehicleVehicle(models.Model):\
    _name = 'vehicle.vehicle'\
    _description = 'Vehicle'\
    _inherit = ['mail.thread', 'mail.activity.mixin']\
    _order = 'create_date desc, id desc'\
\
    # Basic Info\
    name = fields.Char(\
        string='Vehicle',\
        compute='_compute_name',\
        store=True,\
        index=True\
    )\
    vin = fields.Char(\
        string='VIN',\
        size=17,\
        required=True,\
        tracking=True,\
        help='Vehicle Identification Number (17 characters)'\
    )\
    \
    # Vehicle Specifications\
    make = fields.Char(string='Make', tracking=True)\
    model = fields.Char(string='Model', tracking=True)\
    year = fields.Integer(string='Year', tracking=True)\
    body_type = fields.Char(string='Body Type')\
    color = fields.Char(string='Color')\
    \
    # Fuel & Propulsion\
    fuel_type_primary = fields.Char(string='Primary Fuel Type')\
    fuel_type_secondary = fields.Char(string='Secondary Fuel Type')\
    electrification_level = fields.Char(string='Electrification Level')\
    propulsion = fields.Selection([\
        ('gas', 'Gasoline'),\
        ('diesel', 'Diesel'),\
        ('hybrid', 'Hybrid'),\
        ('phev', 'Plug-in Hybrid'),\
        ('bev', 'Battery Electric'),\
    ], string='Propulsion Type', compute='_compute_propulsion', store=True)\
    is_hybrid = fields.Boolean(string='Is Hybrid', compute='_compute_propulsion', store=True)\
    is_ev = fields.Boolean(string='Is Electric', compute='_compute_propulsion', store=True)\
    \
    # Parties\
    customer_id = fields.Many2one(\
        'res.partner',\
        string='Customer',\
        tracking=True,\
        domain=[('customer_rank', '>', 0)]\
    )\
    end_client_id = fields.Many2one(\
        'res.partner',\
        string='End Client',\
        tracking=True\
    )\
    \
    # Status & Lifecycle\
    status = fields.Selection([\
        ('draft', 'Draft'),\
        ('purchased', 'Purchased'),\
        ('paid', 'Paid'),\
        ('loaded', 'Loaded on Container'),\
        ('in_transit', 'In Transit'),\
        ('arrived_nl', 'Arrived at Port'),\
        ('customs_cleared', 'Customs Cleared'),\
        ('planned', 'Delivery Planned'),\
        ('on_truck', 'On Truck'),\
        ('delivered', 'Delivered'),\
        ('exception', 'Exception'),\
    ], string='Status', default='draft', required=True, tracking=True)\
    \
    # Destination\
    final_dest_country = fields.Char(string='Destination Country')\
    final_dest_city = fields.Char(string='Destination City')\
    final_dest_address = fields.Text(string='Destination Address')\
    \
    # Financial - Purchase\
    purchase_price = fields.Monetary(\
        string='Purchase Price',\
        currency_field='currency_id',\
        tracking=True\
    )\
    currency_id = fields.Many2one(\
        'res.currency',\
        string='Currency',\
        default=lambda self: self.env.company.currency_id\
    )\
    \
    # Financial - Transport Costs\
    na_dray_cost = fields.Monetary(\
        string='NA Drayage Cost',\
        currency_field='currency_id',\
        help='North America drayage to port'\
    )\
    ocean_cost = fields.Monetary(\
        string='Ocean Freight Cost',\
        currency_field='currency_id'\
    )\
    extra_cost_total = fields.Monetary(\
        string='Extra Costs',\
        compute='_compute_costs',\
        store=True,\
        currency_field='currency_id',\
        help='Storage, title fees, customs duties, etc.'\
    )\
    transport_total_cost = fields.Monetary(\
        string='Total Transport Cost',\
        compute='_compute_costs',\
        store=True,\
        currency_field='currency_id'\
    )\
    total_cost = fields.Monetary(\
        string='Total Cost',\
        compute='_compute_costs',\
        store=True,\
        currency_field='currency_id'\
    )\
    \
    # Links to other records
    sale_order_id = fields.Many2one('sale.order', string='Sales Order')
    # Note: invoice_ids removed - will be added in Phase 2 with proper setup
    \
    # Dates\
    purchase_date = fields.Date(string='Purchase Date')\
    eta_port = fields.Date(string='ETA at Port')\
    delivery_date = fields.Date(string='Delivery Date')\
    \
    # Notes\
    notes = fields.Text(string='Internal Notes')\
    \
    # Active flag\
    active = fields.Boolean(default=True)\
    \
    # SQL Constraints\
    _sql_constraints = [\
        ('vin_unique', 'UNIQUE(vin)', 'VIN must be unique!'),\
    ]\
    \
    @api.depends('year', 'make', 'model', 'vin')\
    def _compute_name(self):\
        """Compute vehicle display name"""\
        for vehicle in self:\
            parts = []\
            if vehicle.year:\
                parts.append(str(vehicle.year))\
            if vehicle.make:\
                parts.append(vehicle.make)\
            if vehicle.model:\
                parts.append(vehicle.model)\
            if vehicle.vin:\
                parts.append(f"(\{vehicle.vin\})")\
            vehicle.name = ' '.join(parts) if parts else 'New Vehicle'\
    \
    @api.depends('electrification_level', 'fuel_type_primary', 'fuel_type_secondary')\
    def _compute_propulsion(self):\
        """Classify propulsion type based on fuel and electrification data"""\
        for vehicle in self:\
            elec = (vehicle.electrification_level or '').lower()\
            fuel_p = (vehicle.fuel_type_primary or '').lower()\
            fuel_s = (vehicle.fuel_type_secondary or '').lower()\
            \
            # Check for Electric Vehicle (BEV)\
            if 'battery electric' in elec or fuel_p == 'electric' or fuel_s == 'electric':\
                vehicle.is_ev = True\
                vehicle.is_hybrid = False\
                vehicle.propulsion = 'bev'\
            # Check for Plug-in Hybrid (PHEV)\
            elif 'plug' in elec or 'phev' in elec:\
                vehicle.is_ev = False\
                vehicle.is_hybrid = True\
                vehicle.propulsion = 'phev'\
            # Check for Hybrid (non-plug-in)\
            elif 'hybrid' in elec or 'hybrid' in fuel_p or 'hybrid' in fuel_s:\
                vehicle.is_ev = False\
                vehicle.is_hybrid = True\
                vehicle.propulsion = 'hybrid'\
            # Check for Diesel\
            elif 'diesel' in fuel_p or 'diesel' in fuel_s:\
                vehicle.is_ev = False\
                vehicle.is_hybrid = False\
                vehicle.propulsion = 'diesel'\
            # Default to Gasoline\
            else:\
                vehicle.is_ev = False\
                vehicle.is_hybrid = False\
                vehicle.propulsion = 'gas'\
    \
    @api.depends('purchase_price', 'na_dray_cost', 'ocean_cost')\
    def _compute_costs(self):\
        """Compute total costs"""\
        for vehicle in self:\
            # For now, extra_cost_total will be 0 until we add cost lines\
            vehicle.extra_cost_total = 0.0\
            \
            # Transport total\
            vehicle.transport_total_cost = (\
                (vehicle.na_dray_cost or 0.0) +\
                (vehicle.ocean_cost or 0.0)\
            )\
            \
            # Grand total\
            vehicle.total_cost = (\
                (vehicle.purchase_price or 0.0) +\
                vehicle.transport_total_cost +\
                vehicle.extra_cost_total\
            )\
    \
    @api.constrains('vin')\
    def _check_vin(self):\
        """Validate VIN format"""\
        for vehicle in self:\
            if vehicle.vin:\
                # Remove whitespace and convert to uppercase\
                vin = vehicle.vin.strip().upper()\
                \
                # Check length\
                if len(vin) != 17:\
                    raise ValidationError(_('VIN must be exactly 17 characters long.'))\
                \
                # Check for valid characters (no I, O, Q allowed in VIN)\
                if not re.match(r'^[A-HJ-NPR-Z0-9]\{17\}$', vin):\
                    raise ValidationError(_(\
                        'VIN contains invalid characters. '\
                        'VIN can only contain A-Z (except I, O, Q) and 0-9.'\
                    ))\
                \
                # Update with cleaned VIN\
                if vehicle.vin != vin:\
                    vehicle.vin = vin\
    \
    def action_set_purchased(self):\
        """Mark vehicle as purchased"""\
        self.write(\{'status': 'purchased'\})\
        return True\
    \
    def action_set_paid(self):\
        """Mark vehicle as paid"""\
        self.write(\{'status': 'paid'\})\
        return True\
    \
    def action_set_delivered(self):\
        """Mark vehicle as delivered"""\
        self.write(\{\
            'status': 'delivered',\
            'delivery_date': fields.Date.today()\
        \})\
        return True\
    \
    @api.model\
    def create(self, vals):\
        """Override create to clean VIN"""\
        if 'vin' in vals and vals['vin']:\
            vals['vin'] = vals['vin'].strip().upper()\
        return super().create(vals)\
    \
    def write(self, vals):\
        """Override write to clean VIN"""\
        if 'vin' in vals and vals['vin']:\
            vals['vin'] = vals['vin'].strip().upper()\
        return super().write(vals)}
