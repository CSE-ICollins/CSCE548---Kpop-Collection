"""
data_access.py
K-Pop Collection - Data Access Layer
Full CRUD for all 5 tables: artists, albums, collection_items, photocards, wishlist
"""

import sqlite3
import os
from datetime import date
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "kpop_collection.db")


# ─────────────────────────────────────────
# Connection helper
# ─────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ─────────────────────────────────────────
# Schema bootstrap  (creates DB if missing)
# ─────────────────────────────────────────

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS artists (
        artist_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT NOT NULL,
        debut_year  INTEGER CHECK(debut_year >= 1990),
        agency      TEXT,
        fandom_name TEXT,
        is_active   INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
        created_at  TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS albums (
        album_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        artist_id    INTEGER NOT NULL REFERENCES artists(artist_id)
                         ON DELETE RESTRICT ON UPDATE CASCADE,
        title        TEXT NOT NULL,
        release_date TEXT NOT NULL,
        album_type   TEXT NOT NULL CHECK(album_type IN
                         ('Mini Album','Full Album','Single','Repackage','Special Album')),
        num_versions INTEGER NOT NULL DEFAULT 1 CHECK(num_versions >= 1),
        created_at   TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS collection_items (
        item_id         INTEGER PRIMARY KEY AUTOINCREMENT,
        album_id        INTEGER NOT NULL REFERENCES albums(album_id)
                            ON DELETE RESTRICT ON UPDATE CASCADE,
        version_name    TEXT,
        condition_grade TEXT NOT NULL DEFAULT 'Mint'
                            CHECK(condition_grade IN ('Mint','Near Mint','Very Good','Good','Fair')),
        purchase_price  REAL CHECK(purchase_price IS NULL OR purchase_price >= 0),
        purchase_date   TEXT,
        purchase_source TEXT,
        notes           TEXT,
        created_at      TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS photocards (
        photocard_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id         INTEGER NOT NULL REFERENCES collection_items(item_id)
                            ON DELETE RESTRICT ON UPDATE CASCADE,
        member_name     TEXT NOT NULL,
        card_type       TEXT NOT NULL DEFAULT 'Standard'
                            CHECK(card_type IN ('Standard','Rare','Unit','Special','POB')),
        is_duplicate    INTEGER NOT NULL DEFAULT 0 CHECK(is_duplicate IN (0,1)),
        for_trade       INTEGER NOT NULL DEFAULT 0 CHECK(for_trade IN (0,1)),
        estimated_value REAL CHECK(estimated_value IS NULL OR estimated_value >= 0),
        created_at      TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS wishlist (
        wish_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        album_id     INTEGER NOT NULL REFERENCES albums(album_id)
                         ON DELETE CASCADE ON UPDATE CASCADE,
        version_name TEXT,
        priority     TEXT NOT NULL DEFAULT 'Medium'
                         CHECK(priority IN ('Low','Medium','High','Must Have')),
        max_budget   REAL CHECK(max_budget IS NULL OR max_budget >= 0),
        notes        TEXT,
        is_acquired  INTEGER NOT NULL DEFAULT 0 CHECK(is_acquired IN (0,1)),
        added_at     TEXT DEFAULT (datetime('now'))
    );

    CREATE INDEX IF NOT EXISTS idx_albums_artist  ON albums(artist_id);
    CREATE INDEX IF NOT EXISTS idx_items_album    ON collection_items(album_id);
    CREATE INDEX IF NOT EXISTS idx_pc_item        ON photocards(item_id);
    CREATE INDEX IF NOT EXISTS idx_pc_member      ON photocards(member_name);
    CREATE INDEX IF NOT EXISTS idx_wishlist_album ON wishlist(album_id);
    """)

    conn.commit()
    conn.close()


# ════════════════════════════════════════════════════════════════
# ARTISTS
# ════════════════════════════════════════════════════════════════

class ArtistDAO:

    # CREATE
    @staticmethod
    def create(name: str, debut_year: Optional[int] = None,
               agency: Optional[str] = None, fandom_name: Optional[str] = None,
               is_active: bool = True) -> int:
        conn = get_connection()
        cur = conn.execute(
            "INSERT INTO artists (name, debut_year, agency, fandom_name, is_active) "
            "VALUES (?, ?, ?, ?, ?)",
            (name, debut_year, agency, fandom_name, int(is_active))
        )
        conn.commit()
        row_id = cur.lastrowid
        conn.close()
        return row_id

    # READ one
    @staticmethod
    def get_by_id(artist_id: int) -> Optional[sqlite3.Row]:
        conn = get_connection()
        row = conn.execute("SELECT * FROM artists WHERE artist_id = ?", (artist_id,)).fetchone()
        conn.close()
        return row

    # READ all
    @staticmethod
    def get_all() -> list:
        conn = get_connection()
        rows = conn.execute("SELECT * FROM artists ORDER BY name").fetchall()
        conn.close()
        return rows

    # UPDATE
    @staticmethod
    def update(artist_id: int, name: Optional[str] = None,
               debut_year: Optional[int] = None, agency: Optional[str] = None,
               fandom_name: Optional[str] = None, is_active: Optional[bool] = None):
        fields, params = [], []
        if name        is not None: fields.append("name = ?");        params.append(name)
        if debut_year  is not None: fields.append("debut_year = ?");  params.append(debut_year)
        if agency      is not None: fields.append("agency = ?");      params.append(agency)
        if fandom_name is not None: fields.append("fandom_name = ?"); params.append(fandom_name)
        if is_active   is not None: fields.append("is_active = ?");   params.append(int(is_active))
        if not fields:
            return
        params.append(artist_id)
        conn = get_connection()
        conn.execute(f"UPDATE artists SET {', '.join(fields)} WHERE artist_id = ?", params)
        conn.commit()
        conn.close()

    # DELETE
    @staticmethod
    def delete(artist_id: int):
        conn = get_connection()
        conn.execute("DELETE FROM artists WHERE artist_id = ?", (artist_id,))
        conn.commit()
        conn.close()


# ════════════════════════════════════════════════════════════════
# ALBUMS
# ════════════════════════════════════════════════════════════════

class AlbumDAO:

    @staticmethod
    def create(artist_id: int, title: str, release_date: str,
               album_type: str, num_versions: int = 1) -> int:
        conn = get_connection()
        cur = conn.execute(
            "INSERT INTO albums (artist_id, title, release_date, album_type, num_versions) "
            "VALUES (?, ?, ?, ?, ?)",
            (artist_id, title, release_date, album_type, num_versions)
        )
        conn.commit()
        row_id = cur.lastrowid
        conn.close()
        return row_id

    @staticmethod
    def get_by_id(album_id: int) -> Optional[sqlite3.Row]:
        conn = get_connection()
        row = conn.execute(
            "SELECT a.*, ar.name AS artist_name FROM albums a "
            "JOIN artists ar ON a.artist_id = ar.artist_id "
            "WHERE a.album_id = ?", (album_id,)
        ).fetchone()
        conn.close()
        return row

    @staticmethod
    def get_all() -> list:
        conn = get_connection()
        rows = conn.execute(
            "SELECT a.*, ar.name AS artist_name FROM albums a "
            "JOIN artists ar ON a.artist_id = ar.artist_id "
            "ORDER BY a.release_date DESC"
        ).fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_by_artist(artist_id: int) -> list:
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM albums WHERE artist_id = ? ORDER BY release_date", (artist_id,)
        ).fetchall()
        conn.close()
        return rows

    @staticmethod
    def update(album_id: int, title: Optional[str] = None,
               release_date: Optional[str] = None, album_type: Optional[str] = None,
               num_versions: Optional[int] = None):
        fields, params = [], []
        if title        is not None: fields.append("title = ?");        params.append(title)
        if release_date is not None: fields.append("release_date = ?"); params.append(release_date)
        if album_type   is not None: fields.append("album_type = ?");   params.append(album_type)
        if num_versions is not None: fields.append("num_versions = ?"); params.append(num_versions)
        if not fields: return
        params.append(album_id)
        conn = get_connection()
        conn.execute(f"UPDATE albums SET {', '.join(fields)} WHERE album_id = ?", params)
        conn.commit()
        conn.close()

    @staticmethod
    def delete(album_id: int):
        conn = get_connection()
        conn.execute("DELETE FROM albums WHERE album_id = ?", (album_id,))
        conn.commit()
        conn.close()


# ════════════════════════════════════════════════════════════════
# COLLECTION ITEMS
# ════════════════════════════════════════════════════════════════

class CollectionItemDAO:

    @staticmethod
    def create(album_id: int, version_name: Optional[str] = None,
               condition_grade: str = 'Mint', purchase_price: Optional[float] = None,
               purchase_date: Optional[str] = None, purchase_source: Optional[str] = None,
               notes: Optional[str] = None) -> int:
        conn = get_connection()
        cur = conn.execute(
            "INSERT INTO collection_items "
            "(album_id, version_name, condition_grade, purchase_price, purchase_date, purchase_source, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (album_id, version_name, condition_grade, purchase_price, purchase_date, purchase_source, notes)
        )
        conn.commit()
        row_id = cur.lastrowid
        conn.close()
        return row_id

    @staticmethod
    def get_by_id(item_id: int) -> Optional[sqlite3.Row]:
        conn = get_connection()
        row = conn.execute(
            "SELECT ci.*, al.title AS album_title, ar.name AS artist_name "
            "FROM collection_items ci "
            "JOIN albums al ON ci.album_id = al.album_id "
            "JOIN artists ar ON al.artist_id = ar.artist_id "
            "WHERE ci.item_id = ?", (item_id,)
        ).fetchone()
        conn.close()
        return row

    @staticmethod
    def get_all() -> list:
        conn = get_connection()
        rows = conn.execute(
            "SELECT ci.*, al.title AS album_title, ar.name AS artist_name "
            "FROM collection_items ci "
            "JOIN albums al ON ci.album_id = al.album_id "
            "JOIN artists ar ON al.artist_id = ar.artist_id "
            "ORDER BY ci.purchase_date DESC"
        ).fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_by_album(album_id: int) -> list:
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM collection_items WHERE album_id = ?", (album_id,)
        ).fetchall()
        conn.close()
        return rows

    @staticmethod
    def update(item_id: int, version_name: Optional[str] = None,
               condition_grade: Optional[str] = None, purchase_price: Optional[float] = None,
               purchase_date: Optional[str] = None, purchase_source: Optional[str] = None,
               notes: Optional[str] = None):
        fields, params = [], []
        if version_name    is not None: fields.append("version_name = ?");    params.append(version_name)
        if condition_grade is not None: fields.append("condition_grade = ?"); params.append(condition_grade)
        if purchase_price  is not None: fields.append("purchase_price = ?");  params.append(purchase_price)
        if purchase_date   is not None: fields.append("purchase_date = ?");   params.append(purchase_date)
        if purchase_source is not None: fields.append("purchase_source = ?"); params.append(purchase_source)
        if notes           is not None: fields.append("notes = ?");           params.append(notes)
        if not fields: return
        params.append(item_id)
        conn = get_connection()
        conn.execute(f"UPDATE collection_items SET {', '.join(fields)} WHERE item_id = ?", params)
        conn.commit()
        conn.close()

    @staticmethod
    def delete(item_id: int):
        conn = get_connection()
        conn.execute("DELETE FROM collection_items WHERE item_id = ?", (item_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def collection_value() -> float:
        conn = get_connection()
        row = conn.execute(
            "SELECT COALESCE(SUM(purchase_price), 0) AS total FROM collection_items"
        ).fetchone()
        conn.close()
        return row["total"]


# ════════════════════════════════════════════════════════════════
# PHOTOCARDS
# ════════════════════════════════════════════════════════════════

class PhotocardDAO:

    @staticmethod
    def create(item_id: int, member_name: str, card_type: str = 'Standard',
               is_duplicate: bool = False, for_trade: bool = False,
               estimated_value: Optional[float] = None) -> int:
        conn = get_connection()
        cur = conn.execute(
            "INSERT INTO photocards (item_id, member_name, card_type, is_duplicate, for_trade, estimated_value) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (item_id, member_name, card_type, int(is_duplicate), int(for_trade), estimated_value)
        )
        conn.commit()
        row_id = cur.lastrowid
        conn.close()
        return row_id

    @staticmethod
    def get_by_id(photocard_id: int) -> Optional[sqlite3.Row]:
        conn = get_connection()
        row = conn.execute(
            "SELECT pc.*, ci.version_name, al.title AS album_title, ar.name AS artist_name "
            "FROM photocards pc "
            "JOIN collection_items ci ON pc.item_id = ci.item_id "
            "JOIN albums al ON ci.album_id = al.album_id "
            "JOIN artists ar ON al.artist_id = ar.artist_id "
            "WHERE pc.photocard_id = ?", (photocard_id,)
        ).fetchone()
        conn.close()
        return row

    @staticmethod
    def get_all() -> list:
        conn = get_connection()
        rows = conn.execute(
            "SELECT pc.*, ci.version_name, al.title AS album_title, ar.name AS artist_name "
            "FROM photocards pc "
            "JOIN collection_items ci ON pc.item_id = ci.item_id "
            "JOIN albums al ON ci.album_id = al.album_id "
            "JOIN artists ar ON al.artist_id = ar.artist_id "
            "ORDER BY ar.name, pc.member_name"
        ).fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_for_trade() -> list:
        conn = get_connection()
        rows = conn.execute(
            "SELECT pc.*, al.title AS album_title, ar.name AS artist_name "
            "FROM photocards pc "
            "JOIN collection_items ci ON pc.item_id = ci.item_id "
            "JOIN albums al ON ci.album_id = al.album_id "
            "JOIN artists ar ON al.artist_id = ar.artist_id "
            "WHERE pc.for_trade = 1"
        ).fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_by_member(member_name: str) -> list:
        conn = get_connection()
        rows = conn.execute(
            "SELECT pc.*, al.title AS album_title "
            "FROM photocards pc "
            "JOIN collection_items ci ON pc.item_id = ci.item_id "
            "JOIN albums al ON ci.album_id = al.album_id "
            "WHERE LOWER(pc.member_name) = LOWER(?)", (member_name,)
        ).fetchall()
        conn.close()
        return rows

    @staticmethod
    def update(photocard_id: int, member_name: Optional[str] = None,
               card_type: Optional[str] = None, is_duplicate: Optional[bool] = None,
               for_trade: Optional[bool] = None, estimated_value: Optional[float] = None):
        fields, params = [], []
        if member_name      is not None: fields.append("member_name = ?");      params.append(member_name)
        if card_type        is not None: fields.append("card_type = ?");        params.append(card_type)
        if is_duplicate     is not None: fields.append("is_duplicate = ?");     params.append(int(is_duplicate))
        if for_trade        is not None: fields.append("for_trade = ?");        params.append(int(for_trade))
        if estimated_value  is not None: fields.append("estimated_value = ?");  params.append(estimated_value)
        if not fields: return
        params.append(photocard_id)
        conn = get_connection()
        conn.execute(f"UPDATE photocards SET {', '.join(fields)} WHERE photocard_id = ?", params)
        conn.commit()
        conn.close()

    @staticmethod
    def delete(photocard_id: int):
        conn = get_connection()
        conn.execute("DELETE FROM photocards WHERE photocard_id = ?", (photocard_id,))
        conn.commit()
        conn.close()


# ════════════════════════════════════════════════════════════════
# WISHLIST
# ════════════════════════════════════════════════════════════════

class WishlistDAO:

    @staticmethod
    def create(album_id: int, version_name: Optional[str] = None,
               priority: str = 'Medium', max_budget: Optional[float] = None,
               notes: Optional[str] = None) -> int:
        conn = get_connection()
        cur = conn.execute(
            "INSERT INTO wishlist (album_id, version_name, priority, max_budget, notes) "
            "VALUES (?, ?, ?, ?, ?)",
            (album_id, version_name, priority, max_budget, notes)
        )
        conn.commit()
        row_id = cur.lastrowid
        conn.close()
        return row_id

    @staticmethod
    def get_by_id(wish_id: int) -> Optional[sqlite3.Row]:
        conn = get_connection()
        row = conn.execute(
            "SELECT w.*, al.title AS album_title, ar.name AS artist_name "
            "FROM wishlist w "
            "JOIN albums al ON w.album_id = al.album_id "
            "JOIN artists ar ON al.artist_id = ar.artist_id "
            "WHERE w.wish_id = ?", (wish_id,)
        ).fetchone()
        conn.close()
        return row

    @staticmethod
    def get_all(include_acquired: bool = False) -> list:
        conn = get_connection()
        sql = (
            "SELECT w.*, al.title AS album_title, ar.name AS artist_name "
            "FROM wishlist w "
            "JOIN albums al ON w.album_id = al.album_id "
            "JOIN artists ar ON al.artist_id = ar.artist_id "
        )
        if not include_acquired:
            sql += "WHERE w.is_acquired = 0 "
        sql += "ORDER BY CASE w.priority WHEN 'Must Have' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END"
        rows = conn.execute(sql).fetchall()
        conn.close()
        return rows

    @staticmethod
    def mark_acquired(wish_id: int):
        conn = get_connection()
        conn.execute("UPDATE wishlist SET is_acquired = 1 WHERE wish_id = ?", (wish_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def update(wish_id: int, version_name: Optional[str] = None,
               priority: Optional[str] = None, max_budget: Optional[float] = None,
               notes: Optional[str] = None):
        fields, params = [], []
        if version_name is not None: fields.append("version_name = ?"); params.append(version_name)
        if priority     is not None: fields.append("priority = ?");     params.append(priority)
        if max_budget   is not None: fields.append("max_budget = ?");   params.append(max_budget)
        if notes        is not None: fields.append("notes = ?");        params.append(notes)
        if not fields: return
        params.append(wish_id)
        conn = get_connection()
        conn.execute(f"UPDATE wishlist SET {', '.join(fields)} WHERE wish_id = ?", params)
        conn.commit()
        conn.close()

    @staticmethod
    def delete(wish_id: int):
        conn = get_connection()
        conn.execute("DELETE FROM wishlist WHERE wish_id = ?", (wish_id,))
        conn.commit()
        conn.close()
