{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 \{\
    'name': 'VIN Trade Vehicle Management',\
    'version': '17.0.1.0.0',\
    'category': 'Sales/Sales',\
    'summary': 'Vehicle lifecycle management for import/export operations',\
    'description': """\
        VIN Trade Vehicle Management\
        ============================\
        Core module for managing vehicle inventory through the complete lifecycle:\
        - Purchase to delivery tracking\
        - VIN-centric data model\
        - Multi-party coordination (customers, warehouses, carriers)\
        - Cost tracking and profitability\
    """,\
    'author': 'VIN Trade Inc.',\
    'website': 'https://vintradeinc.com',\
    'license': 'LGPL-3',\
    'depends': [\
        'base',\
        'sale_management',\
        'account',\
        'stock',\
        'contacts',\
    ],\
    'data': [\
        'security/vehicle_security.xml',\
        'security/ir.model.access.csv',\
        'data/vehicle_data.xml',\
        'views/vehicle_vehicle_views.xml',\
        'views/vehicle_menus.xml',\
    ],\
    'demo': [],\
    'installable': True,\
    'application': True,\
    'auto_install': False,\
\}}