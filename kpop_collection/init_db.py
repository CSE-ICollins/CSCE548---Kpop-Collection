"""
init_db.py
----------
Creates and seeds the K-Pop Collection database.
Run this once before starting the application.

Usage:
    python init_db.py

What it does:
    1. Deletes any existing kpop_collection.db
    2. Runs schema.sql to create all 7 tables
    3. Runs seed_data.sql to insert 114 rows of test data
    4. Prints a row count summary to confirm success
"""

import sqlite3
import os

# ── paths ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "kpop_collection.db")
SCHEMA   = os.path.join(BASE_DIR, "schema.sql")
SEED     = os.path.join(BASE_DIR, "seed_data.sql")


def init():
    # Remove existing database so we always start fresh
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    # Create schema
    with open(SCHEMA, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    print("✔ Schema created.")

    # Insert seed data
    with open(SEED, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    print("✔ Seed data inserted.")

    # Print row counts
    cur = conn.cursor()
    tables = [
        "artists",
        "groups",
        "group_members",
        "albums",
        "collection_items",
        "photocards",
        "wishlist",
    ]
    total = 0
    print("\nRow counts:")
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        n = cur.fetchone()[0]
        total += n
        print(f"  {table:20} {n:>4} rows")
    print(f"  {'TOTAL':20} {total:>4} rows")

    conn.close()
    print(f"\nDatabase ready: {DB_PATH}")


if __name__ == "__main__":
    init()