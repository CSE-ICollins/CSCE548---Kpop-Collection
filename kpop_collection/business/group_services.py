"""
business/group_service.py
--------------------------
Business layer for groups, albums, collection items, photocards,
wishlist, and reports.  All classes are imported by service/app.py.

Business rules enforced
-----------------------
GroupBusiness
  - group_name must be non-empty
  - gender_type must be one of the allowed values (if supplied)
  - active must be 0 or 1

AlbumBusiness
  - title must be non-empty
  - album_type must be a recognised enum value
  - group_id must reference an existing artist/group

CollectionItemBusiness
  - album_id must reference an existing album
  - condition must be a recognised grade
  - purchase_price, if supplied, must be >= 0

PhotocardBusiness
  - item_id must reference an existing collection item
  - card_type must be a recognised value
  - estimated_value, if supplied, must be >= 0

WishlistBusiness
  - description must be non-empty
  - item_type must be Album | Photocard | Merch | Other
  - priority must be an integer 1-5
  - max_budget, if supplied, must be >= 0

ReportBusiness
  - Aggregation queries only; no write operations.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date
from typing   import Optional

from kpop_dal            import get_connection
from business.exceptions import NotFoundError, ValidationError, DependencyError


# ── small helpers ─────────────────────────────────────────────────────────────

def _row(r) -> dict:
    return dict(r) if r else {}

def _rows(rs) -> list:
    return [dict(r) for r in rs]


# ── allowed values ────────────────────────────────────────────────────────────

_VALID_ALBUM_TYPES  = {"Mini Album", "Full Album", "Single", "Repackage", "Special Album"}
_VALID_CONDITIONS   = {"Mint", "Near Mint", "Very Good", "Good", "Fair"}
_VALID_CARD_TYPES   = {"Standard", "Rare", "Unit", "Special", "POB"}
_VALID_GENDER_TYPES = {"Boy Group", "Girl Group", "Co-ed", "Solo", "Unit"}
_VALID_ITEM_TYPES   = {"Album", "Photocard", "Merch", "Other"}


# ══════════════════════════════════════════════════════════════════════════════
# GROUP BUSINESS
# Groups are stored in the artists table.
# ══════════════════════════════════════════════════════════════════════════════

class GroupBusiness:
    """Business logic for K-pop groups (stored in the artists table)."""

    def _validate(self, group_name: str, gender_type, active: int):
        if not group_name or not group_name.strip():
            raise ValidationError("group_name is required and cannot be blank.")
        if gender_type is not None and gender_type not in _VALID_GENDER_TYPES:
            raise ValidationError(
                f"Invalid gender_type '{gender_type}'. "
                f"Allowed: {', '.join(sorted(_VALID_GENDER_TYPES))}."
            )
        if int(active) not in (0, 1):
            raise ValidationError("active must be 0 or 1.")

    def _get_raw(self, group_id: int) -> dict:
        conn = get_connection()
        row  = conn.execute(
            "SELECT * FROM artists WHERE artist_id=?", (group_id,)
        ).fetchone()
        conn.close()
        if row is None:
            raise NotFoundError(f"Group with id={group_id} not found.")
        return _row(row)

    def list_groups(self) -> list:
        conn  = get_connection()
        rows  = conn.execute(
            "SELECT * FROM artists ORDER BY stage_name"
        ).fetchall()
        conn.close()
        result = []
        for r in rows:
            d = _row(r)
            d["group_id"]   = d["artist_id"]
            d["group_name"] = d["stage_name"]
            result.append(d)
        return result

    def get_group(self, group_id: int) -> dict:
        d = self._get_raw(group_id)
        d["group_id"]   = d["artist_id"]
        d["group_name"] = d["stage_name"]
        return d

    def get_group_members(self, group_id: int) -> list:
        """Return artists list for a group (the group itself in this schema)."""
        group = self.get_group(group_id)
        return [{
            "artist_id":  group["artist_id"],
            "stage_name": group["stage_name"],
            "real_name":  group.get("real_name"),
            "position":   "Member",
        }]

    def add_group(self, group_name: str, agency=None, debut_date=None,
                  fandom_name=None, active: int = 1, gender_type=None,
                  notes=None) -> dict:
        self._validate(group_name, gender_type, active)
        debut_year = int(debut_date[:4]) if debut_date else None
        conn = get_connection()
        cur  = conn.execute(
            "INSERT INTO artists "
            "(stage_name, nationality, active, debut_year, notes) "
            "VALUES (?, ?, ?, ?, ?)",
            (group_name.strip(), agency, int(active), debut_year, notes)
        )
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return self.get_group(new_id)

    def update_group(self, group_id: int, group_name: str, agency=None,
                     debut_date=None, fandom_name=None, active: int = 1,
                     gender_type=None, notes=None) -> dict:
        self._get_raw(group_id)  # raises NotFoundError if missing
        self._validate(group_name, gender_type, active)
        debut_year = int(debut_date[:4]) if debut_date else None
        conn = get_connection()
        conn.execute(
            "UPDATE artists SET stage_name=?, nationality=?, active=?, "
            "debut_year=?, notes=? WHERE artist_id=?",
            (group_name.strip(), agency, int(active), debut_year, notes, group_id)
        )
        conn.commit()
        conn.close()
        return self.get_group(group_id)

    def remove_group(self, group_id: int) -> None:
        self._get_raw(group_id)  # raises NotFoundError if missing
        conn = get_connection()
        try:
            conn.execute("DELETE FROM artists WHERE artist_id=?", (group_id,))
            conn.commit()
        except Exception as e:
            if "FOREIGN KEY" in str(e).upper() or "RESTRICT" in str(e).upper():
                raise DependencyError(
                    f"Cannot delete group {group_id}: albums still reference it."
                )
            raise
        finally:
            conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# ALBUM BUSINESS
# ══════════════════════════════════════════════════════════════════════════════

class AlbumBusiness:
    """Business logic for album records."""

    def _validate(self, title: str, album_type: str, group_id: int,
                  track_count, duration_mins):
        if not title or not title.strip():
            raise ValidationError("title is required and cannot be blank.")
        if album_type not in _VALID_ALBUM_TYPES:
            raise ValidationError(
                f"Invalid album_type '{album_type}'. "
                f"Allowed: {', '.join(sorted(_VALID_ALBUM_TYPES))}."
            )
        if not group_id:
            raise ValidationError("group_id is required.")
        conn = get_connection()
        exists = conn.execute(
            "SELECT 1 FROM artists WHERE artist_id=?", (group_id,)
        ).fetchone()
        conn.close()
        if not exists:
            raise NotFoundError(f"Group/Artist with id={group_id} not found.")
        if track_count is not None and int(track_count) < 1:
            raise ValidationError("track_count must be at least 1.")
        if duration_mins is not None and float(duration_mins) < 0:
            raise ValidationError("duration_mins cannot be negative.")

    def _get_raw(self, album_id: int) -> dict:
        conn = get_connection()
        row  = conn.execute(
            "SELECT al.*, ar.stage_name AS artist_name "
            "FROM albums al JOIN artists ar ON al.group_id = ar.artist_id "
            "WHERE al.album_id=?", (album_id,)
        ).fetchone()
        conn.close()
        if row is None:
            raise NotFoundError(f"Album with id={album_id} not found.")
        return _row(row)

    def list_albums(self) -> list:
        conn = get_connection()
        rows = conn.execute(
            "SELECT al.*, ar.stage_name AS artist_name "
            "FROM albums al JOIN artists ar ON al.group_id = ar.artist_id "
            "ORDER BY al.release_date DESC"
        ).fetchall()
        conn.close()
        return _rows(rows)

    def list_albums_by_group(self, group_id: int) -> list:
        conn = get_connection()
        rows = conn.execute(
            "SELECT al.*, ar.stage_name AS artist_name "
            "FROM albums al JOIN artists ar ON al.group_id = ar.artist_id "
            "WHERE al.group_id=? ORDER BY al.release_date",
            (group_id,)
        ).fetchall()
        conn.close()
        return _rows(rows)

    def get_album(self, album_id: int) -> dict:
        return self._get_raw(album_id)

    def add_album(self, group_id: int, title: str, album_type: str,
                  release_date=None, version_name=None, track_count=None,
                  duration_mins=None, label=None, is_limited: int = 0,
                  notes=None) -> dict:
        self._validate(title, album_type, group_id, track_count, duration_mins)
        release_date = release_date or date.today().isoformat()
        conn = get_connection()
        cur  = conn.execute(
            "INSERT INTO albums "
            "(group_id, title, album_type, release_date, version_name, "
            "track_count, duration_mins, label, is_limited, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (group_id, title.strip(), album_type, release_date, version_name,
             track_count, duration_mins, label, int(is_limited), notes)
        )
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return self.get_album(new_id)

    def update_album(self, album_id: int, group_id: int, title: str,
                     album_type: str, release_date=None, version_name=None,
                     track_count=None, duration_mins=None, label=None,
                     is_limited: int = 0, notes=None) -> dict:
        self._get_raw(album_id)  # raises NotFoundError if missing
        self._validate(title, album_type, group_id, track_count, duration_mins)
        release_date = release_date or date.today().isoformat()
        conn = get_connection()
        conn.execute(
            "UPDATE albums SET group_id=?, title=?, album_type=?, release_date=?, "
            "version_name=?, track_count=?, duration_mins=?, label=?, "
            "is_limited=?, notes=? WHERE album_id=?",
            (group_id, title.strip(), album_type, release_date, version_name,
             track_count, duration_mins, label, int(is_limited), notes, album_id)
        )
        conn.commit()
        conn.close()
        return self.get_album(album_id)

    def remove_album(self, album_id: int) -> None:
        self._get_raw(album_id)  # raises NotFoundError if missing
        conn = get_connection()
        try:
            conn.execute("DELETE FROM albums WHERE album_id=?", (album_id,))
            conn.commit()
        except Exception as e:
            if "FOREIGN KEY" in str(e).upper() or "RESTRICT" in str(e).upper():
                raise DependencyError(
                    f"Cannot delete album {album_id}: collection items still reference it."
                )
            raise
        finally:
            conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# COLLECTION ITEM BUSINESS
# ══════════════════════════════════════════════════════════════════════════════

class CollectionItemBusiness:
    """Business logic for physical album copies owned by the collector."""

    def _validate(self, album_id: int, condition: str, purchase_price):
        if not album_id:
            raise ValidationError("album_id is required.")
        conn = get_connection()
        exists = conn.execute(
            "SELECT 1 FROM albums WHERE album_id=?", (album_id,)
        ).fetchone()
        conn.close()
        if not exists:
            raise NotFoundError(f"Album with id={album_id} not found.")
        if condition not in _VALID_CONDITIONS:
            raise ValidationError(
                f"Invalid condition '{condition}'. "
                f"Allowed: {', '.join(sorted(_VALID_CONDITIONS))}."
            )
        if purchase_price is not None and float(purchase_price) < 0:
            raise ValidationError("purchase_price cannot be negative.")

    def _get_raw(self, item_id: int) -> dict:
        conn = get_connection()
        row  = conn.execute(
            "SELECT ci.*, al.title AS album_title, ar.stage_name AS artist_name "
            "FROM collection_items ci "
            "JOIN albums al  ON ci.album_id  = al.album_id "
            "JOIN artists ar ON al.group_id   = ar.artist_id "
            "WHERE ci.item_id=?", (item_id,)
        ).fetchone()
        conn.close()
        if row is None:
            raise NotFoundError(f"Collection item with id={item_id} not found.")
        return _row(row)

    def list_items(self) -> list:
        conn = get_connection()
        rows = conn.execute(
            "SELECT ci.*, al.title AS album_title, ar.stage_name AS artist_name "
            "FROM collection_items ci "
            "JOIN albums al  ON ci.album_id = al.album_id "
            "JOIN artists ar ON al.group_id  = ar.artist_id "
            "ORDER BY ci.purchase_date DESC"
        ).fetchall()
        conn.close()
        return _rows(rows)

    def get_item(self, item_id: int) -> dict:
        return self._get_raw(item_id)

    def get_total_spent(self) -> float:
        conn = get_connection()
        row  = conn.execute(
            "SELECT COALESCE(SUM(purchase_price), 0) AS total FROM collection_items"
        ).fetchone()
        conn.close()
        return round(row["total"], 2)

    def add_item(self, album_id: int, condition: str = "Mint",
                 purchase_date=None, purchase_price=None, purchase_from=None,
                 is_sealed: int = 0, has_poster: int = 0, has_cd: int = 1,
                 inclusions=None, notes=None) -> dict:
        self._validate(album_id, condition, purchase_price)
        conn = get_connection()
        cur  = conn.execute(
            "INSERT INTO collection_items "
            "(album_id, condition, purchase_date, purchase_price, purchase_from, "
            "is_sealed, has_poster, has_cd, inclusions, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (album_id, condition, purchase_date,
             float(purchase_price) if purchase_price is not None else None,
             purchase_from, int(is_sealed), int(has_poster), int(has_cd),
             inclusions, notes)
        )
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return self.get_item(new_id)

    def update_item(self, item_id: int, album_id: int, condition: str = "Mint",
                    purchase_date=None, purchase_price=None, purchase_from=None,
                    is_sealed: int = 0, has_poster: int = 0, has_cd: int = 1,
                    inclusions=None, notes=None) -> dict:
        self._get_raw(item_id)  # raises NotFoundError if missing
        self._validate(album_id, condition, purchase_price)
        conn = get_connection()
        conn.execute(
            "UPDATE collection_items SET album_id=?, condition=?, purchase_date=?, "
            "purchase_price=?, purchase_from=?, is_sealed=?, has_poster=?, "
            "has_cd=?, inclusions=?, notes=? WHERE item_id=?",
            (album_id, condition, purchase_date,
             float(purchase_price) if purchase_price is not None else None,
             purchase_from, int(is_sealed), int(has_poster), int(has_cd),
             inclusions, notes, item_id)
        )
        conn.commit()
        conn.close()
        return self.get_item(item_id)

    def remove_item(self, item_id: int) -> None:
        self._get_raw(item_id)  # raises NotFoundError if missing
        conn = get_connection()
        try:
            conn.execute("DELETE FROM collection_items WHERE item_id=?", (item_id,))
            conn.commit()
        except Exception as e:
            if "FOREIGN KEY" in str(e).upper() or "RESTRICT" in str(e).upper():
                raise DependencyError(
                    f"Cannot delete item {item_id}: photocards still reference it."
                )
            raise
        finally:
            conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# PHOTOCARD BUSINESS
# ══════════════════════════════════════════════════════════════════════════════

class PhotocardBusiness:
    """Business logic for photocards."""

    def _validate(self, item_id: int, card_type: str, estimated_value):
        if not item_id:
            raise ValidationError("item_id is required.")
        conn = get_connection()
        exists = conn.execute(
            "SELECT 1 FROM collection_items WHERE item_id=?", (item_id,)
        ).fetchone()
        conn.close()
        if not exists:
            raise NotFoundError(f"Collection item with id={item_id} not found.")
        if card_type not in _VALID_CARD_TYPES:
            raise ValidationError(
                f"Invalid card_type '{card_type}'. "
                f"Allowed: {', '.join(sorted(_VALID_CARD_TYPES))}."
            )
        if estimated_value is not None and float(estimated_value) < 0:
            raise ValidationError("estimated_value cannot be negative.")

    def _get_raw(self, photocard_id: int) -> dict:
        conn = get_connection()
        row  = conn.execute(
            "SELECT pc.*, ar.stage_name AS artist_name, al.title AS album_title "
            "FROM photocards pc "
            "LEFT JOIN artists ar ON pc.artist_id = ar.artist_id "
            "LEFT JOIN albums  al ON pc.album_id  = al.album_id "
            "WHERE pc.photocard_id=?", (photocard_id,)
        ).fetchone()
        conn.close()
        if row is None:
            raise NotFoundError(f"Photocard with id={photocard_id} not found.")
        return _row(row)

    def list_photocards(self) -> list:
        conn = get_connection()
        rows = conn.execute(
            "SELECT pc.*, ar.stage_name AS artist_name, al.title AS album_title "
            "FROM photocards pc "
            "LEFT JOIN artists ar ON pc.artist_id = ar.artist_id "
            "LEFT JOIN albums  al ON pc.album_id  = al.album_id "
            "ORDER BY ar.stage_name, pc.card_type"
        ).fetchall()
        conn.close()
        return _rows(rows)

    def list_for_trade(self) -> list:
        conn = get_connection()
        rows = conn.execute(
            "SELECT pc.*, ar.stage_name AS artist_name, al.title AS album_title "
            "FROM photocards pc "
            "LEFT JOIN artists ar ON pc.artist_id = ar.artist_id "
            "LEFT JOIN albums  al ON pc.album_id  = al.album_id "
            "WHERE pc.for_trade=1"
        ).fetchall()
        conn.close()
        return _rows(rows)

    def list_by_artist(self, artist_id: int) -> list:
        conn = get_connection()
        rows = conn.execute(
            "SELECT pc.*, ar.stage_name AS artist_name, al.title AS album_title "
            "FROM photocards pc "
            "LEFT JOIN artists ar ON pc.artist_id = ar.artist_id "
            "LEFT JOIN albums  al ON pc.album_id  = al.album_id "
            "WHERE pc.artist_id=?",
            (artist_id,)
        ).fetchall()
        conn.close()
        return _rows(rows)

    def get_photocard(self, photocard_id: int) -> dict:
        return self._get_raw(photocard_id)

    def get_total_value(self) -> float:
        conn = get_connection()
        row  = conn.execute(
            "SELECT COALESCE(SUM(estimated_value), 0) AS total FROM photocards"
        ).fetchone()
        conn.close()
        return round(row["total"], 2)

    def add_photocard(self, item_id: int, artist_id: int = 0,
                      album_id: int = 0, card_type: str = "Standard",
                      condition: str = "Mint", acquired_date=None,
                      acquired_from=None, estimated_value=None,
                      is_duplicate: int = 0, for_trade: int = 0,
                      notes=None) -> dict:
        self._validate(item_id, card_type, estimated_value)
        conn = get_connection()
        cur  = conn.execute(
            "INSERT INTO photocards "
            "(item_id, artist_id, album_id, card_type, condition, "
            "acquired_date, acquired_from, estimated_value, "
            "is_duplicate, for_trade, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (item_id, artist_id or None, album_id or None,
             card_type, condition, acquired_date, acquired_from,
             float(estimated_value) if estimated_value is not None else None,
             int(is_duplicate), int(for_trade), notes)
        )
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return self.get_photocard(new_id)

    def update_photocard(self, photocard_id: int, item_id: int = 0,
                         artist_id: int = 0, album_id: int = 0,
                         card_type: str = "Standard", condition: str = "Mint",
                         acquired_date=None, acquired_from=None,
                         estimated_value=None, is_duplicate: int = 0,
                         for_trade: int = 0, notes=None) -> dict:
        existing = self._get_raw(photocard_id)  # raises NotFoundError if missing
        resolved_item_id = item_id or existing["item_id"]
        self._validate(resolved_item_id, card_type, estimated_value)
        conn = get_connection()
        conn.execute(
            "UPDATE photocards SET item_id=?, artist_id=?, album_id=?, "
            "card_type=?, condition=?, acquired_date=?, acquired_from=?, "
            "estimated_value=?, is_duplicate=?, for_trade=?, notes=? "
            "WHERE photocard_id=?",
            (resolved_item_id, artist_id or None, album_id or None,
             card_type, condition, acquired_date, acquired_from,
             float(estimated_value) if estimated_value is not None else None,
             int(is_duplicate), int(for_trade), notes, photocard_id)
        )
        conn.commit()
        conn.close()
        return self.get_photocard(photocard_id)

    def toggle_trade_flag(self, photocard_id: int) -> dict:
        """Flip the for_trade boolean."""
        pc      = self._get_raw(photocard_id)
        current = bool(pc.get("for_trade", 0))
        conn    = get_connection()
        conn.execute(
            "UPDATE photocards SET for_trade=? WHERE photocard_id=?",
            (int(not current), photocard_id)
        )
        conn.commit()
        conn.close()
        return self.get_photocard(photocard_id)

    def remove_photocard(self, photocard_id: int) -> None:
        self._get_raw(photocard_id)  # raises NotFoundError if missing
        conn = get_connection()
        conn.execute("DELETE FROM photocards WHERE photocard_id=?", (photocard_id,))
        conn.commit()
        conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# WISHLIST BUSINESS
# ══════════════════════════════════════════════════════════════════════════════

class WishlistBusiness:
    """Business logic for the wishlist."""

    # Numeric priority (1=highest) used by service layer
    _P_TO_INT  = {"Must Have": 1, "High": 2, "Medium": 3, "Low": 4}

    def _validate(self, description: str, item_type: str,
                  priority: int, max_budget):
        if not description or not description.strip():
            raise ValidationError("description is required and cannot be blank.")
        if item_type and item_type not in _VALID_ITEM_TYPES:
            raise ValidationError(
                f"Invalid item_type '{item_type}'. "
                f"Allowed: {', '.join(sorted(_VALID_ITEM_TYPES))}."
            )
        try:
            p = int(priority)
        except (TypeError, ValueError):
            raise ValidationError("priority must be an integer.")
        if not (1 <= p <= 5):
            raise ValidationError("priority must be between 1 and 5.")
        if max_budget is not None and float(max_budget) < 0:
            raise ValidationError("max_budget cannot be negative.")

    def _get_raw(self, wish_id: int) -> dict:
        conn = get_connection()
        row  = conn.execute(
            "SELECT w.*, al.title AS album_title, ar.stage_name AS artist_name "
            "FROM wishlist w "
            "LEFT JOIN albums  al ON w.album_id  = al.album_id "
            "LEFT JOIN artists ar ON w.artist_id = ar.artist_id "
            "WHERE w.wish_id=?", (wish_id,)
        ).fetchone()
        conn.close()
        if row is None:
            raise NotFoundError(f"Wish with id={wish_id} not found.")
        return _row(row)

    def list_wishes(self) -> list:
        conn = get_connection()
        rows = conn.execute(
            "SELECT w.*, al.title AS album_title, ar.stage_name AS artist_name "
            "FROM wishlist w "
            "LEFT JOIN albums  al ON w.album_id  = al.album_id "
            "LEFT JOIN artists ar ON w.artist_id = ar.artist_id "
            "ORDER BY w.priority ASC"
        ).fetchall()
        conn.close()
        return _rows(rows)

    def list_pending(self) -> list:
        conn = get_connection()
        rows = conn.execute(
            "SELECT w.*, al.title AS album_title, ar.stage_name AS artist_name "
            "FROM wishlist w "
            "LEFT JOIN albums  al ON w.album_id  = al.album_id "
            "LEFT JOIN artists ar ON w.artist_id = ar.artist_id "
            "WHERE w.acquired=0 ORDER BY w.priority ASC"
        ).fetchall()
        conn.close()
        return _rows(rows)

    def get_wish(self, wish_id: int) -> dict:
        return self._get_raw(wish_id)

    def add_wish(self, item_type: str, description: str, album_id=None,
                 artist_id=None, max_budget=None, priority: int = 3,
                 notes=None) -> dict:
        self._validate(description, item_type, priority, max_budget)
        conn = get_connection()
        cur  = conn.execute(
            "INSERT INTO wishlist "
            "(item_type, album_id, artist_id, description, max_budget, priority, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (item_type or "Album",
             int(album_id)  if album_id  else None,
             int(artist_id) if artist_id else None,
             description.strip(),
             float(max_budget) if max_budget is not None else None,
             int(priority), notes)
        )
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return self.get_wish(new_id)

    def update_wish(self, wish_id: int, item_type: str, description: str,
                    album_id=None, artist_id=None, max_budget=None,
                    priority: int = 3, acquired: int = 0,
                    notes=None) -> dict:
        self._get_raw(wish_id)  # raises NotFoundError if missing
        self._validate(description, item_type, priority, max_budget)
        conn = get_connection()
        conn.execute(
            "UPDATE wishlist SET item_type=?, album_id=?, artist_id=?, "
            "description=?, max_budget=?, priority=?, acquired=?, notes=? "
            "WHERE wish_id=?",
            (item_type or "Album",
             int(album_id)  if album_id  else None,
             int(artist_id) if artist_id else None,
             description.strip(),
             float(max_budget) if max_budget is not None else None,
             int(priority), int(acquired), notes, wish_id)
        )
        conn.commit()
        conn.close()
        return self.get_wish(wish_id)

    def mark_acquired(self, wish_id: int) -> dict:
        """Mark a wish as obtained."""
        self._get_raw(wish_id)  # raises NotFoundError if missing
        conn = get_connection()
        conn.execute("UPDATE wishlist SET acquired=1 WHERE wish_id=?", (wish_id,))
        conn.commit()
        conn.close()
        return self.get_wish(wish_id)

    def remove_wish(self, wish_id: int) -> None:
        self._get_raw(wish_id)  # raises NotFoundError if missing
        conn = get_connection()
        conn.execute("DELETE FROM wishlist WHERE wish_id=?", (wish_id,))
        conn.commit()
        conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# REPORT BUSINESS
# ══════════════════════════════════════════════════════════════════════════════

class ReportBusiness:
    """Read-only aggregation queries for dashboard reports."""

    def collection_summary(self) -> dict:
        """Return high-level stats: totals, averages, derived values."""
        conn = get_connection()
        total_albums     = conn.execute(
            "SELECT COUNT(*) FROM collection_items"
        ).fetchone()[0]
        total_spent      = conn.execute(
            "SELECT COALESCE(SUM(purchase_price), 0) FROM collection_items"
        ).fetchone()[0]
        avg_cost         = (total_spent / total_albums) if total_albums else 0.0
        total_photocards = conn.execute(
            "SELECT COUNT(*) FROM photocards"
        ).fetchone()[0]
        pc_value         = conn.execute(
            "SELECT COALESCE(SUM(estimated_value), 0) FROM photocards"
        ).fetchone()[0]
        wish_pending     = conn.execute(
            "SELECT COUNT(*) FROM wishlist WHERE acquired=0"
        ).fetchone()[0]
        conn.close()

        return {
            "total_albums":         total_albums,
            "total_spent":          round(total_spent, 2),
            "average_album_cost":   round(avg_cost, 2),
            "total_photocards":     total_photocards,
            "photocard_value":      round(pc_value, 2),
            "net_collection_value": round(total_spent + pc_value, 2),
            "wishlist_pending":     wish_pending,
        }

    def photocards_per_artist(self) -> list:
        """Count of photocards and total estimated value, grouped by artist."""
        conn = get_connection()
        rows = conn.execute("""
            SELECT
                ar.stage_name                          AS stage_name,
                COUNT(pc.photocard_id)                 AS card_count,
                COALESCE(SUM(pc.estimated_value), 0)   AS total_value
            FROM photocards pc
            JOIN artists ar ON pc.artist_id = ar.artist_id
            GROUP BY ar.artist_id, ar.stage_name
            ORDER BY card_count DESC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def albums_per_group(self) -> list:
        """Count of owned copies and total spend, grouped by group/artist."""
        conn = get_connection()
        rows = conn.execute("""
            SELECT
                ar.stage_name                          AS group_name,
                COUNT(ci.item_id)                      AS owned_copies,
                COALESCE(SUM(ci.purchase_price), 0)    AS total_spent
            FROM collection_items ci
            JOIN albums  al ON ci.album_id = al.album_id
            JOIN artists ar ON al.group_id = ar.artist_id
            GROUP BY ar.artist_id, ar.stage_name
            ORDER BY owned_copies DESC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]