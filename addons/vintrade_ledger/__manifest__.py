# -*- coding: utf-8 -*-
{
    "name": "VIN Trade • Customer Ledger",
    "version": "17.0.1.0.2",  # <-- bump
    "summary": "Customer credit limit, wallet balance, statements, and invoice guard",
    "author": "VIN Trade Inc.",
    "website": "",
    "category": "Accounting",
    "license": "OPL-1",
    "depends": ["base", "mail", "contacts", "account", "vintrade_vehicle"],
    "data": [
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/partner_views.xml",
        "views/wallet_views.xml",
        "wizards/statement_views.xml",
        "reports/statement_templates.xml",
    ],
    "installable": True,
    "application": True,   # <-- make it show in Apps
}