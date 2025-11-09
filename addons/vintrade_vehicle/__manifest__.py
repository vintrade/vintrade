{
    'name': 'VIN Trade Vehicle Management',
    'version': '17.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Vehicle lifecycle management for import/export operations',
    'description': """
        VIN Trade Vehicle Management
        ============================
        Core module for managing vehicle inventory through the complete lifecycle:
        - Purchase to delivery tracking
        - VIN-centric data model
        - Multi-party coordination (customers, warehouses, carriers)
        - Cost tracking and profitability
    """,
    'author': 'VIN Trade Inc.',
    'website': 'https://vintradeinc.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale_management',
        'account',
        'stock',
        'contacts',
    ],
    "data": [
        "data/ir_sequence_data.xml",
        "security/ir.model.access.csv",
        "views/vehicle_views.xml",
    ],
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}