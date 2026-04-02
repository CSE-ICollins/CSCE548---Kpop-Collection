# K-Pop Collection Manager

A database-backed console application to track your K-pop album and photocard collection.

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Database Schema

7 tables with full relationships and constraints:

```
artists ──< group_members >── groups ──< albums ──< collection_items ──< photocards
                                              └──< wishlist
```

| Table | Description |
|---|---|
| `artists` | K-pop artists |
| `groups` | K-pop groups |
| `group_members` | Artist ↔ group relationship |
| `albums` | Album releases with version counts |
| `collection_items` | Physical copies you own |
| `photocards` | Individual photocards pulled from albums |
| `wishlist` | Albums/versions you want to acquire |

✔ Primary keys  
✔ Foreign keys  
✔ Constraints and validation rules  

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Architecture (n-tier)

This project follows a layered n-tier architecture:

```
Console Client / Frontend
        ↓ HTTP requests
Flask Service Layer (service/app.py)
        ↓ method calls
Business Layer (business/*.py)
        ↓ DAO calls
Data Access Layer (kpop_dal.py)
        ↓ SQL
SQLite Database (kpop_collection.db)
```

### Layer Responsibilities
- Client Layer → interacts with API  
- Service Layer → exposes REST endpoints  
- Business Layer → validation + business rules  
- Data Access Layer → CRUD operations  
- Database → persistent storage  

Each layer is isolated and communicates only with adjacent layers.

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Setup

### Option A – SQLite (built-in, no install needed)
```bash
cd data_access
python seed_db.py
cd ../console_app
python console_app.py
```

### Option B – MySQL
```bash
mysql -u root -p < sql/01_schema.sql
mysql -u root -p kpop_collection < sql/02_seed_data.sql
```

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Full Setup (From Scratch – Project Requirement)

```bash
git clone https://github.com/[your-username]/kpop-vault.git
cd kpop-vault

python -m venv .venv
.\.venv\Scripts\activate

pip install -r kpop_collection/requirements.txt

python kpop_collection/init_db.py

# Start API
python -m kpop_collection.service.app

# Run tests
python -m kpop_collection.system_test
```

OR (no server required):
```bash
python -m kpop_collection.system_test --internal
```

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Features

- View all artists, albums, collection items, photocards, wishlist  
- Collection stats and reports  
- Add/update/delete records  
- Full CRUD layer for all tables  
- REST API (35+ endpoints)  
- Business rule validation  
- System test coverage  

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Client Layer

- Console client (`console_client.py`) for interactive testing  
- System test (`system_test.py`) for full validation  

Both communicate with the API over HTTP.

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Files

```
kpop_collection/
├── sql/
├── data_access/
├── business/
├── service/
├── frontend/
├── client/
├── logs/
```

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## API Endpoints (35 total)

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

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## ☁️ Cloud Deployment (Render.com)

Build:
```bash
pip install -r requirements.txt
```

Start:
```bash
gunicorn service.app:app --bind 0.0.0.0:$PORT
```

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## ✅ System Test Results

```
52 / 52 TESTS PASSED
```

Covers:
- CRUD operations  
- Validation rules  
- API endpoints  
- Database integrity  

Each test verifies both API response and database state.

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## 🔧 Environment Variables

| Variable | Description |
|---|---|
| DB_PATH | Path to SQLite DB |
| LOG_LEVEL | Logging level |
| PORT | Server port |

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## 🛠️ Troubleshooting

| Problem | Solution |
|---|---|
| Flask missing | pip install -r requirements.txt |
| DB missing | python init_db.py |
| Port conflict | change port |
| API offline | start server |
| FK error | delete dependent records first |

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## 🤖 AI Tool Notes

Built using AI (Claude / ChatGPT).

### AI strengths:
- Schema design  
- API endpoints  
- Business layer structure  

### Issues encountered:
- Incorrect import paths  
- Missing DAO classes  
- Schema mismatches between layers  

### Manual fixes:
- Rewrote `artist_service.py` and `group_service.py`  
- Fixed imports and module structure  
- Aligned business logic with database schema  
- Corrected validation rules  

### Evaluation:
~85% AI-generated, ~15% manual debugging and refinement.

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## 📸 Screenshots

(See submitted PDF)

Includes:
- Database schema  
- API running  
- CRUD operations  
- Frontend UI  
- System test results  

-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## 📄 License

MIT