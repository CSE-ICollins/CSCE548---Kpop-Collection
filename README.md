# K-Pop Collection Manager

A database-backed console application to track your K-pop album and photocard collection.

## Database Schema

5 tables with full relationships and constraints:

```
artists ──< albums ──< collection_items ──< photocards
                  └──< wishlist
```

| Table | Description |
|---|---|
| `artists` | K-pop groups/solo artists |
| `albums` | Album releases with version counts |
| `collection_items` | Physical copies you own |
| `photocards` | Individual photocards pulled from albums |
| `wishlist` | Albums/versions you want to acquire |

## Setup

### Option A – SQLite (built-in, no install needed)
```bash
cd data_access
python seed_db.py     # creates kpop_collection.db and seeds 50+ rows
cd ../console_app
python console_app.py
```

### Option B – MySQL
Run the SQL scripts in order:
```bash
mysql -u root -p < sql/01_schema.sql
mysql -u root -p kpop_collection < sql/02_seed_data.sql
```

## Features
- View all artists, albums, collection items, photocards, wishlist
- Collection stats with mini ASCII bar chart
- Add artists and wishlist items interactively
- Mark wishlist items as acquired
- Full CRUD layer for all 5 tables

## Files
```
kpop_collection/
├── sql/
│   ├── 01_schema.sql          # MySQL schema (primary keys, FKs, constraints)
│   └── 02_seed_data.sql       # 50+ rows of test data
├── data_access/
│   ├── data_access.py         # DAOs with full CRUD for all 5 tables
│   └── seed_db.py             # Seeds SQLite database
└── console_app/
    └── console_app.py         # Interactive console front end
```

Business Layer + REST Service Layer
Architecture
Console Client (HTTP)
    ↓ requests
Flask Service Layer  (service/app.py)       ← REST API, /api/v1/
    ↓ method calls
Business Layer       (business/*.py)        ← validation, rules, dict conversion
    ↓ DAO calls
Data Access Layer    (kpop_dal.py)          ← sqlite3 CRUD
    ↓ SQL
SQLite Database      (kpop_collection.db)
Quick Start
bashpip install -r requirements.txt

# First time only — create and seed the database
python init_db.py

# Start the API server (Terminal 1)
python service/app.py
# API available at http://127.0.0.1:5000

# Run the console client (Terminal 2)
python client/console_client.py          # interactive menu
python client/console_client.py --demo   # automated CRUD demo
API Endpoints (35 total)

GET  /health
GET/POST      /api/v1/artists
GET/PUT/DELETE /api/v1/artists/{id}
PATCH          /api/v1/artists/{id}/deactivate
GET/POST       /api/v1/groups
GET             /api/v1/groups/{id}/members
GET/POST        /api/v1/albums
GET/POST        /api/v1/collection
GET             /api/v1/collection/spent
GET/POST        /api/v1/photocards
GET             /api/v1/photocards/value
PATCH           /api/v1/photocards/{id}/toggle-trade
GET/POST        /api/v1/wishlist
PATCH           /api/v1/wishlist/{id}/acquire
GET             /api/v1/reports/summary
GET             /api/v1/reports/photocards-per-artist
GET             /api/v1/reports/albums-per-group

Cloud Deployment (Render.com)

Push to GitHub
New Web Service → connect repo
Build command: pip install flask gunicorn
Start command: gunicorn service.app:app --bind 0.0.0.0:$PORT
Env var: DB_PATH=/opt/render/project/src/kpop_collection.db

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
📸 Overview
KPOP VAULT lets you track your K-pop album collection, photocards, groups/artists, and wishlist through a web interface backed by a REST API.
LayerTechnologyDescriptionDatabaseSQLite 37 tables, 9 FK relationships, 114 seed rowsData Access (DAL)Python sqlite3Full CRUD for all 7 tablesBusiness LayerPython classesValidation, business rules, typed exceptionsService LayerFlask 3.1 REST35 endpoints, JSON, CORS, file loggingFrontendHTML/CSS/JSSingle-page app, no framework, full CRUD UI

🚀 Quick Start
Prerequisites

Python 3.10+ — python.org/downloads
pip — bundled with Python
Git — git-scm.com
A modern web browser

1. Clone the repo
bashgit clone https://github.com/[your-username]/kpop-vault.git
cd kpop-vault
2. Install dependencies
bashpip install -r requirements.txt
3. Initialize the database
bashpython init_db.py
# Creates kpop_collection.db with 114 seed rows across 7 tables
4. Start the API server
bashpython service/app.py
# API live at http://127.0.0.1:5000
# Verify: http://127.0.0.1:5000/health -> {"status": "ok"}
5. Open the frontend
bash# Option A — static server (second terminal)
cd frontend && python -m http.server 8080
# Open: http://127.0.0.1:8080

# Option B — direct file open
# Double-click frontend/index.html in your file explorer

📁 Project Structure
kpop-vault/
├── kpop_dal.py              # Data Access Layer
├── kpop_collection.db       # SQLite database
├── init_db.py               # DB init & seed script
├── schema.sql               # SQL DDL
├── seed_data.sql            # 114-row seed data
├── requirements.txt
├── business/
│   ├── exceptions.py        # Domain exception hierarchy
│   ├── artist_service.py    # Artist business logic
│   └── group_service.py     # All other business services
├── service/
│   └── app.py               # Flask REST API (35 endpoints)
├── frontend/
│   └── index.html           # Web frontend (58KB, no framework)
├── client/
│   └── console_client.py    # Console test client
└── logs/
    └── api.log              # Auto-created by server

🔌 API Reference
Base URL: http://127.0.0.1:5000/api/v1
ResourceGETPOSTPUTDELETESpecial/artists✔ list, single, search✔✔✔PATCH /deactivate/groups✔ list, single, members✔✔✔—/albums✔ list, by-group, single✔✔✔—/collection✔ list, spent, single✔✔✔—/photocards✔ list, by-artist, trade, value, single✔✔✔PATCH /toggle-trade/wishlist✔ list, pending, single✔✔✔PATCH /acquire/reportssummary, pca, apg————
Example:
bashcurl http://127.0.0.1:5000/api/v1/artists
curl -X POST http://127.0.0.1:5000/api/v1/groups \
  -H "Content-Type: application/json" \
  -d '{"group_name":"LE SSERAFIM","agency":"HYBE","gender_type":"Girl Group"}'

🌐 Frontend Pages
PageTablesCreateUpdateDeleteSpecialDashboardReports———Bar chartsGroupsgroups, members✔✔✔View rosterArtistsartists✔✔✔DeactivateAlbumsalbums✔✔✔Filter by groupOwned Albumscollection_items✔✔✔Total spentPhotocardsphotocards✔✔✔Toggle tradeWishlistwishlist✔✔✔Mark acquired

☁️ Cloud Deployment (Render.com)

Push repo to GitHub
render.com → New + → Web Service → connect repo
Build Command: pip install -r requirements.txt
Start Command: gunicorn service.app:app --bind 0.0.0.0:$PORT
Env Var: DB_PATH = /opt/render/project/src/kpop_collection.db
Update frontend/index.html line 1: const API = 'https://your-app.onrender.com/api/v1';


Free tier spins down after 15 min. First request after spin-down takes ~30s.


✅ System Test Results
bashpython system_test.py
CategoryCountResultHealth & Reports4✔ PASSGroups CRUD6✔ PASSArtists CRUD + deactivate7✔ PASSAlbums CRUD5✔ PASSCollection CRUD5✔ PASSPhotocards CRUD + toggle8✔ PASSWishlist CRUD + acquire7✔ PASSBusiness rule validation7✔ PASSCleanup3✔ PASSTOTAL5252 / 52 PASS
Each write test verifies both the HTTP response and the SQLite database directly.

🔧 Environment Variables
VariableDefaultDescriptionDB_PATH<root>/kpop_collection.dbPath to SQLite databaseLOG_LEVELINFODEBUG / INFO / WARNING / ERRORPORT5000Flask server port

🛠️ Troubleshooting
ProblemSolutionModuleNotFoundError: flaskpip install -r requirements.txtkpop_collection.db not foundpython init_db.pyPort 5000 already in usePORT=5001 python service/app.pyFrontend red "API Offline"Start Flask: python service/app.pyCORS error in browser consoleVerify add_cors() in service/app.pyFK constraint on DELETEDelete children first, or use /deactivate for artists

🤖 AI Tool Notes
Built with Claude (Anthropic) across 4 projects.
AI did well: Schema design, all 35 Flask routes, business layer structure, full frontend visual design.
Required manual fixes: CORS configuration, DB_PATH portability, file logging, @handle_biz decorator refactor, frontend filter wiring and XSS-safe esc() helper.
Ratio: ~85% AI-generated, ~15% manual refinement.

📄 License
MIT — free to use, modify, and distribute.
//