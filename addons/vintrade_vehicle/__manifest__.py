{
    "name": "VIN Trade • Vehicles",
    "summary": "Core vehicle model (VIN-first) for VIN Trade operations",
    "version": "17.0.1.0.1",  # incremented version for rebuild
    "author": "VIN Trade Inc.",
    "website": "",
    "category": "Operations/Inventory",
    "license": "OPL-1",
    "depends": ["base", "mail"],
    "data": [
        "data/ir_sequence_data.xml",
        "security/ir.model.access.csv",
        "views/vehicle_views.xml",
    ],
    "application": True,
    "installable": True,
}