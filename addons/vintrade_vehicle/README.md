{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 # VIN Trade Vehicle Management - Phase 1\
\
## Overview\
Core vehicle management module for VIN Trade Inc. - Licensed Ontario Motor Vehicle Dealer (OMVIC).\
\
This Phase 1 implementation provides:\
- \uc0\u9989  Complete vehicle data model with VIN validation\
- \uc0\u9989  Automatic propulsion classification (Gas/Diesel/Hybrid/PHEV/BEV)\
- \uc0\u9989  Lifecycle status tracking (Draft \u8594  Delivered)\
- \uc0\u9989  Cost tracking (Purchase + Transport + Extras)\
- \uc0\u9989  Customer and destination management\
- \uc0\u9989  Security groups (User/Manager)\
- \uc0\u9989  Mobile-friendly views (Tree/Form/Kanban)\
- \uc0\u9989  Chatter integration for notes and activities\
\
## Module Structure\
```\
vintrade_vehicle/\
\uc0\u9500 \u9472 \u9472  __init__.py\
\uc0\u9500 \u9472 \u9472  __manifest__.py\
\uc0\u9500 \u9472 \u9472  README.md\
\uc0\u9500 \u9472 \u9472  models/\
\uc0\u9474    \u9500 \u9472 \u9472  __init__.py\
\uc0\u9474    \u9492 \u9472 \u9472  vehicle_vehicle.py\
\uc0\u9500 \u9472 \u9472  security/\
\uc0\u9474    \u9500 \u9472 \u9472  vehicle_security.xml\
\uc0\u9474    \u9492 \u9472 \u9472  ir.model.access.csv\
\uc0\u9500 \u9472 \u9472  data/\
\uc0\u9474    \u9492 \u9472 \u9472  vehicle_data.xml\
\uc0\u9500 \u9472 \u9472  views/\
\uc0\u9474    \u9500 \u9472 \u9472  vehicle_vehicle_views.xml\
\uc0\u9474    \u9492 \u9472 \u9472  vehicle_menus.xml\
\uc0\u9492 \u9472 \u9472  static/\
    \uc0\u9492 \u9472 \u9472  description/\
        \uc0\u9492 \u9472 \u9472  icon.png\
```\
\
## Installation on Odoo.sh\
\
### Step 1: Add to Git Repository\
\
1. Create the module folder structure in your GitHub repo:\
```\
   addons/vintrade_vehicle/\
```\
\
2. Copy all files from this artifact into the correct locations\
\
3. Commit and push:\
```bash\
   git add addons/vintrade_vehicle/\
   git commit -m "feat(vin): add Phase 1 VIN Trade Vehicle module"\
   git push origin main\
```\
\
### Step 2: Install Module Icon (Optional)\
\
Create a simple icon file:\
```bash\
mkdir -p addons/vintrade_vehicle/static/description\
# Add a 128x128 PNG icon as icon.png\
```\
\
Or the module will use Odoo's default icon.\
\
### Step 3: Deploy on Odoo.sh\
\
1. Odoo.sh will automatically detect the push and start building\
2. Wait for the build to complete (watch the status in Odoo.sh)\
3. Once deployed, go to your Odoo instance\
\
### Step 4: Install the Module\
\
1. Navigate to **Apps** menu\
2. Remove the "Apps" filter to show all modules\
3. Search for "VIN Trade"\
4. Click **Install**\
\
### Step 5: Configure Users\
\
1. Go to **Settings \uc0\u8594  Users & Companies \u8594  Users**\
2. Edit users who need access\
3. Under **Application Accesses**, find **VIN Trade** section\
4. Assign either:\
   - **User**: Can create/edit vehicles\
   - **Manager**: Full access including delete\
\
## Usage\
\
### Creating a Vehicle\
\
1. Navigate to **VIN Trade \uc0\u8594  Operations \u8594  Vehicles**\
2. Click **Create**\
3. Enter the VIN (17 characters) - it will auto-uppercase\
4. Fill in vehicle details (Make, Model, Year, etc.)\
5. Add fuel/electrification data to auto-classify propulsion type\
6. Set customer and destination\
7. Enter purchase price and transport costs\
8. Click **Save**\
\
### VIN Validation\
\
The module automatically:\
- Converts VIN to uppercase\
- Validates 17-character length\
- Checks for invalid characters (I, O, Q not allowed)\
- Ensures VIN uniqueness\
\
### Status Workflow\
\
Use the status buttons to track vehicle lifecycle:\
1. **Draft** \uc0\u8594  Mark Purchased \u8594  **Purchased**\
2. **Purchased** \uc0\u8594  Mark Paid \u8594  **Paid**\
3. Manual status changes for: Loaded, In Transit, Arrived, Customs Cleared\
4. **Planned/On Truck** \uc0\u8594  Mark Delivered \u8594  **Delivered**\
\
### Propulsion Auto-Classification\
\
Based on `fuel_type_primary`, `fuel_type_secondary`, and `electrification_level`:\
- **BEV**: Contains "battery electric" or fuel = "Electric"\
- **PHEV**: Contains "plug" or "phev"  \
- **Hybrid**: Contains "hybrid" (but not plug-in or BEV)\
- **Diesel**: Contains "diesel"\
- **Gas**: Default for all others\
\
## Testing Checklist\
\
- [ ] Create vehicle with valid 17-char VIN\
- [ ] Try invalid VIN (wrong length, invalid chars)\
- [ ] Test duplicate VIN (should fail)\
- [ ] Enter fuel data and verify propulsion auto-classification\
- [ ] Test cost calculations (purchase + transport = total)\
- [ ] Test status workflow buttons\
- [ ] Verify security (User vs Manager permissions)\
- [ ] Test search filters (Draft, In Transit, EVs, etc.)\
- [ ] Check mobile kanban view\
- [ ] Add notes and activities via chatter\
\
## What's Next (Future Phases)\
\
**Phase 2**: Business Logic & Integrations\
- NHTSA VIN decoder API integration\
- Ports and rate tables\
- Automatic transport cost calculation\
- Container tracking\
\
**Phase 3**: Extended Models\
- Cost lines (storage, title fees, customs)\
- Customs case management  \
- Truck load planning\
- Title management\
\
**Phase 4**: Advanced Features\
- Warehouse portal\
- Google Drive integration\
- OMVIC Bill of Sale\
- Email templates and automations\
\
## Support\
\
For issues or questions:\
- Check Odoo.sh logs: **Logs** tab in your project\
- Review commit history for changes\
- Contact: info@vintradeinc.com\
\
## License\
\
LGPL-3\
\
---\
\
**VIN Trade Inc.**  \
Licensed Ontario Motor Vehicle Dealer (OMVIC)  \
Toronto, Ontario, Canada}