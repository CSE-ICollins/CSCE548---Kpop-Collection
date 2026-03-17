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
