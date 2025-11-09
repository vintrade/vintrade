{
    "name": "VIN Trade • Vehicles",
    "summary": "Core vehicle model (VIN-first) for VIN Trade operations",
    "version": "17.0.1.0.0",
    "author": "VIN Trade Inc.",
    "website": "",
    "category": "Operations/Inventory",
    "license": "OPL-1",
    "depends": ["base", "mail"],  # keep light; we'll add others later
    "data": [
        "data/ir_sequence_data.xml",
        "security/ir.model.access.csv",
        "views/vehicle_views.xml",
    ],
    "assets": {},
    "application": True,
    "installable": True,
}