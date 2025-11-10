{
    "name": "VIN Trade • Vehicles",
    "summary": "Core vehicle model (VIN-first) for VIN Trade operations",
    "version": "17.0.1.0.9",
    "author": "VIN Trade Inc.",
    "website": "",
    "category": "Operations/Inventory",
    "license": "OPL-1",
    "depends": ["base", "mail", "sale", "account"],
    "data": [
        "data/ir_sequence_data.xml",
        "security/ir.model.access.csv",
        "views/vehicle_views.xml",
        "views/sale_order_views.xml",
        "views/account_move_views.xml",
    ],
    "application": True,
    "installable": True,
}