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