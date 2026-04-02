"""
business/group_service.py
Clean business layer for groups, albums, collection items, photocards,
wishlist, and reports.

This version matches the schema in schema.sql and does not depend on
missing DAO/model classes like GroupDAO or Group objects.
"""

from __future__ import annotations

import sqlite3
from datetime import date
from typing import Any, Dict, List, Optional

from kpop_dal import get_connection
from business.exceptions import NotFoundError, ValidationError, DependencyError


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _row(row) -> Dict[str, Any]:
    return dict(row) if row else {}


def _rows(rows) -> List[Dict[str, Any]]:
    return [dict(r) for r in rows]


def _ensure_int(value, field_name: str) -> int:
    try:
        return int(value)
    except Exception as exc:
        raise ValidationError(f"{field_name} must be an integer.") from exc


def _ensure_float(value, field_name: str) -> float:
    try:
        return float(value)
    except Exception as exc:
        raise ValidationError(f"{field_name} must be a number.") from exc


def _exists(table: str, id_col: str, row_id: int) -> bool:
    conn = get_connection()
    try:
        row = conn.execute(
            f"SELECT 1 FROM {table} WHERE {id_col} = ?",
            (row_id,),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def _get_or_404(table: str, id_col: str, row_id: int, label: str):
    conn = get_connection()
    try:
        row = conn.execute(
            f"SELECT * FROM {table} WHERE {id_col} = ?",
            (row_id,),
        ).fetchone()
        if row is None:
            raise NotFoundError(f"{label} {row_id} not found")
        return row
    finally:
        conn.close()


def _delete_with_fk_map(fn, not_found_label: str, dependency_label: str):
    try:
        return fn()
    except sqlite3.IntegrityError as exc:
        raise DependencyError(dependency_label) from exc


# ─────────────────────────────────────────────────────────────
# Allowed values
# ─────────────────────────────────────────────────────────────

VALID_GENDER_TYPES = {"Boy Group", "Girl Group", "Co-ed", "Solo"}
VALID_ALBUM_TYPES = {
    "Mini Album",
    "Full Album",
    "Single Album",
    "Repackage",
    "Special Album",
    "OST",
    "Collaboration",
}
VALID_CONDITIONS = {"Mint", "Near Mint", "Very Good", "Good", "Fair", "Poor"}
VALID_CARD_TYPES = {"Standard", "Unit", "Solo", "Special", "Lucky Draw", "POB", "Pre-order"}
VALID_ITEM_TYPES = {"Album", "Photocard", "Merch"}


# ════════════════════════════════════════════════════════════════
# GROUP BUSINESS
# ════════════════════════════════════════════════════════════════

class GroupBusiness:
    def _validate(self, group_name: str, gender_type: Optional[str], active: int):
        if not group_name or not str(group_name).strip():
            raise ValidationError("group_name is required and cannot be blank.")
        if gender_type is not None and gender_type not in VALID_GENDER_TYPES:
            raise ValidationError(
                f"gender_type must be one of {sorted(VALID_GENDER_TYPES)}."
            )
        if int(active) not in (0, 1):
            raise ValidationError("active must be 0 or 1.")

    def list_groups(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM groups ORDER BY group_name"
            ).fetchall()
            return _rows(rows)
        finally:
            conn.close()

    def get_group(self, group_id: int) -> Dict[str, Any]:
        row = _get_or_404("groups", "group_id", group_id, "Group")
        return _row(row)

    def get_group_members(self, group_id: int) -> List[Dict[str, Any]]:
        _get_or_404("groups", "group_id", group_id, "Group")
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT
                    gm.member_id,
                    gm.artist_id,
                    a.stage_name,
                    a.real_name,
                    gm.position,
                    gm.join_date,
                    gm.leave_date
                FROM group_members gm
                JOIN artists a ON a.artist_id = gm.artist_id
                WHERE gm.group_id = ?
                ORDER BY a.stage_name
                """,
                (group_id,),
            ).fetchall()
            return _rows(rows)
        finally:
            conn.close()

    def add_group(
        self,
        group_name: str,
        agency: Optional[str] = None,
        debut_date: Optional[str] = None,
        fandom_name: Optional[str] = None,
        active: int = 1,
        gender_type: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._validate(group_name, gender_type, active)

        conn = get_connection()
        try:
            cur = conn.execute(
                """
                INSERT INTO groups
                (group_name, agency, debut_date, fandom_name, active, gender_type, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    group_name.strip(),
                    agency,
                    debut_date,
                    fandom_name,
                    int(active),
                    gender_type,
                    notes,
                ),
            )
            conn.commit()
            new_id = cur.lastrowid
        except sqlite3.IntegrityError as exc:
            raise ValidationError(f"Group '{group_name}' already exists or violates constraints.") from exc
        finally:
            conn.close()

        return self.get_group(new_id)

    def update_group(
        self,
        group_id: int,
        group_name: str,
        agency: Optional[str] = None,
        debut_date: Optional[str] = None,
        fandom_name: Optional[str] = None,
        active: int = 1,
        gender_type: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        _get_or_404("groups", "group_id", group_id, "Group")
        self._validate(group_name, gender_type, active)

        conn = get_connection()
        try:
            conn.execute(
                """
                UPDATE groups
                SET group_name = ?,
                    agency = ?,
                    debut_date = ?,
                    fandom_name = ?,
                    active = ?,
                    gender_type = ?,
                    notes = ?
                WHERE group_id = ?
                """,
                (
                    group_name.strip(),
                    agency,
                    debut_date,
                    fandom_name,
                    int(active),
                    gender_type,
                    notes,
                    group_id,
                ),
            )
            conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValidationError(f"Group '{group_name}' violates constraints.") from exc
        finally:
            conn.close()

        return self.get_group(group_id)

    def remove_group(self, group_id: int) -> bool:
        _get_or_404("groups", "group_id", group_id, "Group")

        def _do_delete():
            conn = get_connection()
            try:
                conn.execute("DELETE FROM groups WHERE group_id = ?", (group_id,))
                conn.commit()
                return True
            finally:
                conn.close()

        try:
            return _do_delete()
        except sqlite3.IntegrityError as exc:
            raise DependencyError(
                f"Cannot delete group {group_id}: albums or members still reference it."
            ) from exc


# ════════════════════════════════════════════════════════════════
# ALBUM BUSINESS
# ════════════════════════════════════════════════════════════════

class AlbumBusiness:
    def _validate(self, group_id: int, title: str, album_type: str, track_count=None, duration_mins=None):
        if not _exists("groups", "group_id", group_id):
            raise NotFoundError(f"Group {group_id} not found")
        if not title or not str(title).strip():
            raise ValidationError("title is required and cannot be blank.")
        if album_type not in VALID_ALBUM_TYPES:
            raise ValidationError(f"album_type must be one of {sorted(VALID_ALBUM_TYPES)}.")
        if track_count is not None and int(track_count) <= 0:
            raise ValidationError("track_count must be greater than 0.")
        if duration_mins is not None and float(duration_mins) <= 0:
            raise ValidationError("duration_mins must be greater than 0.")

    def list_albums(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT
                    a.*,
                    g.group_name
                FROM albums a
                JOIN groups g ON g.group_id = a.group_id
                ORDER BY a.release_date DESC, a.title
                """
            ).fetchall()
            return _rows(rows)
        finally:
            conn.close()

    def list_albums_by_group(self, group_id: int) -> List[Dict[str, Any]]:
        if not _exists("groups", "group_id", group_id):
            raise NotFoundError(f"Group {group_id} not found")
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT a.*, g.group_name
                FROM albums a
                JOIN groups g ON g.group_id = a.group_id
                WHERE a.group_id = ?
                ORDER BY a.release_date DESC, a.title
                """,
                (group_id,),
            ).fetchall()
            return _rows(rows)
        finally:
            conn.close()

    def get_album(self, album_id: int) -> Dict[str, Any]:
        conn = get_connection()
        try:
            row = conn.execute(
                """
                SELECT a.*, g.group_name
                FROM albums a
                JOIN groups g ON g.group_id = a.group_id
                WHERE a.album_id = ?
                """,
                (album_id,),
            ).fetchone()
            if row is None:
                raise NotFoundError(f"Album {album_id} not found")
            return _row(row)
        finally:
            conn.close()

    def add_album(
        self,
        group_id: int,
        title: str,
        album_type: str,
        release_date: Optional[str] = None,
        version_name: Optional[str] = None,
        track_count: Optional[int] = None,
        duration_mins: Optional[float] = None,
        label: Optional[str] = None,
        is_limited: int = 0,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._validate(group_id, title, album_type, track_count, duration_mins)
        release_date = release_date or date.today().isoformat()

        conn = get_connection()
        try:
            cur = conn.execute(
                """
                INSERT INTO albums
                (group_id, title, album_type, release_date, version_name, track_count,
                 duration_mins, label, is_limited, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    group_id,
                    title.strip(),
                    album_type,
                    release_date,
                    version_name,
                    track_count,
                    duration_mins,
                    label,
                    int(is_limited),
                    notes,
                ),
            )
            conn.commit()
            new_id = cur.lastrowid
        except sqlite3.IntegrityError as exc:
            raise ValidationError("Album violates database constraints.") from exc
        finally:
            conn.close()

        return self.get_album(new_id)

    def update_album(
        self,
        album_id: int,
        group_id: int,
        title: str,
        album_type: str,
        release_date: Optional[str] = None,
        version_name: Optional[str] = None,
        track_count: Optional[int] = None,
        duration_mins: Optional[float] = None,
        label: Optional[str] = None,
        is_limited: int = 0,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.get_album(album_id)
        self._validate(group_id, title, album_type, track_count, duration_mins)

        conn = get_connection()
        try:
            conn.execute(
                """
                UPDATE albums
                SET group_id = ?,
                    title = ?,
                    album_type = ?,
                    release_date = ?,
                    version_name = ?,
                    track_count = ?,
                    duration_mins = ?,
                    label = ?,
                    is_limited = ?,
                    notes = ?
                WHERE album_id = ?
                """,
                (
                    group_id,
                    title.strip(),
                    album_type,
                    release_date,
                    version_name,
                    track_count,
                    duration_mins,
                    label,
                    int(is_limited),
                    notes,
                    album_id,
                ),
            )
            conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValidationError("Album violates database constraints.") from exc
        finally:
            conn.close()

        return self.get_album(album_id)

    def remove_album(self, album_id: int) -> bool:
        self.get_album(album_id)

        def _do_delete():
            conn = get_connection()
            try:
                conn.execute("DELETE FROM albums WHERE album_id = ?", (album_id,))
                conn.commit()
                return True
            finally:
                conn.close()

        try:
            return _do_delete()
        except sqlite3.IntegrityError as exc:
            raise DependencyError(
                f"Cannot delete album {album_id}: collection items still reference it."
            ) from exc


# ════════════════════════════════════════════════════════════════
# COLLECTION ITEM BUSINESS
# ════════════════════════════════════════════════════════════════

class CollectionItemBusiness:
    def _validate(self, album_id: int, condition: str, purchase_price: Optional[float]):
        if not _exists("albums", "album_id", album_id):
            raise NotFoundError(f"Album {album_id} not found")
        if condition not in VALID_CONDITIONS:
            raise ValidationError(f"condition must be one of {sorted(VALID_CONDITIONS)}.")
        if purchase_price is not None and float(purchase_price) < 0:
            raise ValidationError("purchase_price cannot be negative.")

    def list_items(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT
                    ci.*,
                    a.title AS album_title,
                    g.group_name
                FROM collection_items ci
                JOIN albums a ON a.album_id = ci.album_id
                JOIN groups g ON g.group_id = a.group_id
                ORDER BY ci.purchase_date DESC, ci.item_id DESC
                """
            ).fetchall()
            return _rows(rows)
        finally:
            conn.close()

    def get_total_spent(self) -> float:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT COALESCE(SUM(purchase_price), 0) AS total_spent FROM collection_items"
            ).fetchone()
            return float(row["total_spent"] or 0)
        finally:
            conn.close()

    def get_item(self, item_id: int) -> Dict[str, Any]:
        conn = get_connection()
        try:
            row = conn.execute(
                """
                SELECT
                    ci.*,
                    a.title AS album_title,
                    g.group_name
                FROM collection_items ci
                JOIN albums a ON a.album_id = ci.album_id
                JOIN groups g ON g.group_id = a.group_id
                WHERE ci.item_id = ?
                """,
                (item_id,),
            ).fetchone()
            if row is None:
                raise NotFoundError(f"Collection item {item_id} not found")
            return _row(row)
        finally:
            conn.close()

    def add_item(
        self,
        album_id: int,
        condition: str = "Mint",
        purchase_date: Optional[str] = None,
        purchase_price: Optional[float] = None,
        purchase_from: Optional[str] = None,
        is_sealed: int = 0,
        has_poster: int = 0,
        has_cd: int = 1,
        inclusions: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._validate(album_id, condition, purchase_price)

        conn = get_connection()
        try:
            cur = conn.execute(
                """
                INSERT INTO collection_items
                (album_id, condition, purchase_date, purchase_price, purchase_from,
                 is_sealed, has_poster, has_cd, inclusions, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    album_id,
                    condition,
                    purchase_date,
                    purchase_price,
                    purchase_from,
                    int(is_sealed),
                    int(has_poster),
                    int(has_cd),
                    inclusions,
                    notes,
                ),
            )
            conn.commit()
            new_id = cur.lastrowid
        except sqlite3.IntegrityError as exc:
            raise ValidationError("Collection item violates database constraints.") from exc
        finally:
            conn.close()

        return self.get_item(new_id)

    def update_item(
        self,
        item_id: int,
        album_id: int,
        condition: str = "Mint",
        purchase_date: Optional[str] = None,
        purchase_price: Optional[float] = None,
        purchase_from: Optional[str] = None,
        is_sealed: int = 0,
        has_poster: int = 0,
        has_cd: int = 1,
        inclusions: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.get_item(item_id)
        self._validate(album_id, condition, purchase_price)

        conn = get_connection()
        try:
            conn.execute(
                """
                UPDATE collection_items
                SET album_id = ?,
                    condition = ?,
                    purchase_date = ?,
                    purchase_price = ?,
                    purchase_from = ?,
                    is_sealed = ?,
                    has_poster = ?,
                    has_cd = ?,
                    inclusions = ?,
                    notes = ?
                WHERE item_id = ?
                """,
                (
                    album_id,
                    condition,
                    purchase_date,
                    purchase_price,
                    purchase_from,
                    int(is_sealed),
                    int(has_poster),
                    int(has_cd),
                    inclusions,
                    notes,
                    item_id,
                ),
            )
            conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValidationError("Collection item violates database constraints.") from exc
        finally:
            conn.close()

        return self.get_item(item_id)

    def remove_item(self, item_id: int) -> bool:
        self.get_item(item_id)

        conn = get_connection()
        try:
            conn.execute("DELETE FROM collection_items WHERE item_id = ?", (item_id,))
            conn.commit()
            return True
        except sqlite3.IntegrityError as exc:
            raise DependencyError(
                f"Cannot delete collection item {item_id}: photocards still reference it."
            ) from exc
        finally:
            conn.close()


# ════════════════════════════════════════════════════════════════
# PHOTOCARD BUSINESS
# ════════════════════════════════════════════════════════════════

class PhotocardBusiness:
    def _validate(
        self,
        item_id: int,
        artist_id: int,
        album_id: int,
        card_type: str,
        condition: str,
        estimated_value: Optional[float],
    ):
        if not _exists("collection_items", "item_id", item_id):
            raise NotFoundError(f"Collection item {item_id} not found")
        if not _exists("artists", "artist_id", artist_id):
            raise NotFoundError(f"Artist {artist_id} not found")
        if not _exists("albums", "album_id", album_id):
            raise NotFoundError(f"Album {album_id} not found")
        if card_type not in VALID_CARD_TYPES:
            raise ValidationError(f"card_type must be one of {sorted(VALID_CARD_TYPES)}.")
        if condition not in VALID_CONDITIONS:
            raise ValidationError(f"condition must be one of {sorted(VALID_CONDITIONS)}.")
        if estimated_value is not None and float(estimated_value) < 0:
            raise ValidationError("estimated_value cannot be negative.")

    def list_photocards(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT
                    pc.*,
                    a.stage_name,
                    al.title AS album_title,
                    g.group_name
                FROM photocards pc
                JOIN artists a ON a.artist_id = pc.artist_id
                JOIN albums al ON al.album_id = pc.album_id
                JOIN groups g ON g.group_id = al.group_id
                ORDER BY a.stage_name, pc.photocard_id
                """
            ).fetchall()
            return _rows(rows)
        finally:
            conn.close()

    def list_for_trade(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT
                    pc.*,
                    a.stage_name,
                    al.title AS album_title,
                    g.group_name
                FROM photocards pc
                JOIN artists a ON a.artist_id = pc.artist_id
                JOIN albums al ON al.album_id = pc.album_id
                JOIN groups g ON g.group_id = al.group_id
                WHERE pc.for_trade = 1
                ORDER BY a.stage_name, pc.photocard_id
                """
            ).fetchall()
            return _rows(rows)
        finally:
            conn.close()

    def list_by_artist(self, artist_id: int) -> List[Dict[str, Any]]:
        if not _exists("artists", "artist_id", artist_id):
            raise NotFoundError(f"Artist {artist_id} not found")
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT
                    pc.*,
                    a.stage_name,
                    al.title AS album_title,
                    g.group_name
                FROM photocards pc
                JOIN artists a ON a.artist_id = pc.artist_id
                JOIN albums al ON al.album_id = pc.album_id
                JOIN groups g ON g.group_id = al.group_id
                WHERE pc.artist_id = ?
                ORDER BY pc.photocard_id
                """,
                (artist_id,),
            ).fetchall()
            return _rows(rows)
        finally:
            conn.close()

    def get_total_value(self) -> float:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT COALESCE(SUM(estimated_value), 0) AS total_value FROM photocards"
            ).fetchone()
            return float(row["total_value"] or 0)
        finally:
            conn.close()

    def get_photocard(self, photocard_id: int) -> Dict[str, Any]:
        conn = get_connection()
        try:
            row = conn.execute(
                """
                SELECT
                    pc.*,
                    a.stage_name,
                    al.title AS album_title,
                    g.group_name
                FROM photocards pc
                JOIN artists a ON a.artist_id = pc.artist_id
                JOIN albums al ON al.album_id = pc.album_id
                JOIN groups g ON g.group_id = al.group_id
                WHERE pc.photocard_id = ?
                """,
                (photocard_id,),
            ).fetchone()
            if row is None:
                raise NotFoundError(f"Photocard {photocard_id} not found")
            return _row(row)
        finally:
            conn.close()

    def add_photocard(
        self,
        item_id: int,
        artist_id: int,
        album_id: int,
        card_type: str = "Standard",
        condition: str = "Mint",
        acquired_date: Optional[str] = None,
        acquired_from: Optional[str] = None,
        estimated_value: Optional[float] = None,
        is_duplicate: int = 0,
        for_trade: int = 0,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._validate(item_id, artist_id, album_id, card_type, condition, estimated_value)

        conn = get_connection()
        try:
            cur = conn.execute(
                """
                INSERT INTO photocards
                (item_id, artist_id, album_id, card_type, condition,
                 acquired_date, acquired_from, estimated_value, is_duplicate, for_trade, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item_id,
                    artist_id,
                    album_id,
                    card_type,
                    condition,
                    acquired_date,
                    acquired_from,
                    estimated_value,
                    int(is_duplicate),
                    int(for_trade),
                    notes,
                ),
            )
            conn.commit()
            new_id = cur.lastrowid
        except sqlite3.IntegrityError as exc:
            raise ValidationError("Photocard violates database constraints.") from exc
        finally:
            conn.close()

        return self.get_photocard(new_id)

    def update_photocard(
        self,
        photocard_id: int,
        item_id: int,
        artist_id: int,
        album_id: int,
        card_type: str = "Standard",
        condition: str = "Mint",
        acquired_date: Optional[str] = None,
        acquired_from: Optional[str] = None,
        estimated_value: Optional[float] = None,
        is_duplicate: int = 0,
        for_trade: int = 0,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.get_photocard(photocard_id)
        self._validate(item_id, artist_id, album_id, card_type, condition, estimated_value)

        conn = get_connection()
        try:
            conn.execute(
                """
                UPDATE photocards
                SET item_id = ?,
                    artist_id = ?,
                    album_id = ?,
                    card_type = ?,
                    condition = ?,
                    acquired_date = ?,
                    acquired_from = ?,
                    estimated_value = ?,
                    is_duplicate = ?,
                    for_trade = ?,
                    notes = ?
                WHERE photocard_id = ?
                """,
                (
                    item_id,
                    artist_id,
                    album_id,
                    card_type,
                    condition,
                    acquired_date,
                    acquired_from,
                    estimated_value,
                    int(is_duplicate),
                    int(for_trade),
                    notes,
                    photocard_id,
                ),
            )
            conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValidationError("Photocard violates database constraints.") from exc
        finally:
            conn.close()

        return self.get_photocard(photocard_id)

    def toggle_trade_flag(self, photocard_id: int) -> Dict[str, Any]:
        pc = self.get_photocard(photocard_id)
        new_value = 0 if int(pc.get("for_trade", 0)) else 1

        conn = get_connection()
        try:
            conn.execute(
                "UPDATE photocards SET for_trade = ? WHERE photocard_id = ?",
                (new_value, photocard_id),
            )
            conn.commit()
        finally:
            conn.close()

        return self.get_photocard(photocard_id)

    def remove_photocard(self, photocard_id: int) -> bool:
        self.get_photocard(photocard_id)
        conn = get_connection()
        try:
            conn.execute("DELETE FROM photocards WHERE photocard_id = ?", (photocard_id,))
            conn.commit()
            return True
        finally:
            conn.close()


# ════════════════════════════════════════════════════════════════
# WISHLIST BUSINESS
# ════════════════════════════════════════════════════════════════

class WishlistBusiness:
    def _validate(self, item_type: str, description: str, priority: int, max_budget: Optional[float]):
        if item_type not in VALID_ITEM_TYPES:
            raise ValidationError(f"item_type must be one of {sorted(VALID_ITEM_TYPES)}.")
        if not description or not str(description).strip():
            raise ValidationError("description is required and cannot be blank.")
        if int(priority) < 1 or int(priority) > 5:
            raise ValidationError("priority must be between 1 and 5.")
        if max_budget is not None and float(max_budget) < 0:
            raise ValidationError("max_budget cannot be negative.")

    def list_wishes(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT
                    w.*,
                    a.title AS album_title,
                    ar.stage_name
                FROM wishlist w
                LEFT JOIN albums a ON a.album_id = w.album_id
                LEFT JOIN artists ar ON ar.artist_id = w.artist_id
                ORDER BY w.priority ASC, w.created_at DESC
                """
            ).fetchall()
            return _rows(rows)
        finally:
            conn.close()

    def list_pending(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT
                    w.*,
                    a.title AS album_title,
                    ar.stage_name
                FROM wishlist w
                LEFT JOIN albums a ON a.album_id = w.album_id
                LEFT JOIN artists ar ON ar.artist_id = w.artist_id
                WHERE w.acquired = 0
                ORDER BY w.priority ASC, w.created_at DESC
                """
            ).fetchall()
            return _rows(rows)
        finally:
            conn.close()

    def get_wish(self, wish_id: int) -> Dict[str, Any]:
        conn = get_connection()
        try:
            row = conn.execute(
                """
                SELECT
                    w.*,
                    a.title AS album_title,
                    ar.stage_name
                FROM wishlist w
                LEFT JOIN albums a ON a.album_id = w.album_id
                LEFT JOIN artists ar ON ar.artist_id = w.artist_id
                WHERE w.wish_id = ?
                """,
                (wish_id,),
            ).fetchone()
            if row is None:
                raise NotFoundError(f"Wish {wish_id} not found")
            return _row(row)
        finally:
            conn.close()

    def add_wish(
        self,
        item_type: str,
        description: str,
        album_id: Optional[int] = None,
        artist_id: Optional[int] = None,
        max_budget: Optional[float] = None,
        priority: int = 3,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._validate(item_type, description, priority, max_budget)

        if album_id is not None and not _exists("albums", "album_id", album_id):
            raise NotFoundError(f"Album {album_id} not found")
        if artist_id is not None and not _exists("artists", "artist_id", artist_id):
            raise NotFoundError(f"Artist {artist_id} not found")

        conn = get_connection()
        try:
            cur = conn.execute(
                """
                INSERT INTO wishlist
                (item_type, album_id, artist_id, description, max_budget, priority, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item_type,
                    album_id,
                    artist_id,
                    description.strip(),
                    max_budget,
                    int(priority),
                    notes,
                ),
            )
            conn.commit()
            new_id = cur.lastrowid
        except sqlite3.IntegrityError as exc:
            raise ValidationError("Wishlist item violates database constraints.") from exc
        finally:
            conn.close()

        return self.get_wish(new_id)

    def update_wish(
        self,
        wish_id: int,
        item_type: str,
        description: str,
        album_id: Optional[int] = None,
        artist_id: Optional[int] = None,
        max_budget: Optional[float] = None,
        priority: int = 3,
        acquired: int = 0,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.get_wish(wish_id)
        self._validate(item_type, description, priority, max_budget)

        if album_id is not None and not _exists("albums", "album_id", album_id):
            raise NotFoundError(f"Album {album_id} not found")
        if artist_id is not None and not _exists("artists", "artist_id", artist_id):
            raise NotFoundError(f"Artist {artist_id} not found")

        conn = get_connection()
        try:
            conn.execute(
                """
                UPDATE wishlist
                SET item_type = ?,
                    album_id = ?,
                    artist_id = ?,
                    description = ?,
                    max_budget = ?,
                    priority = ?,
                    acquired = ?,
                    notes = ?
                WHERE wish_id = ?
                """,
                (
                    item_type,
                    album_id,
                    artist_id,
                    description.strip(),
                    max_budget,
                    int(priority),
                    int(acquired),
                    notes,
                    wish_id,
                ),
            )
            conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValidationError("Wishlist item violates database constraints.") from exc
        finally:
            conn.close()

        return self.get_wish(wish_id)

    def mark_acquired(self, wish_id: int) -> Dict[str, Any]:
        self.get_wish(wish_id)
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE wishlist SET acquired = 1 WHERE wish_id = ?",
                (wish_id,),
            )
            conn.commit()
        finally:
            conn.close()
        return self.get_wish(wish_id)

    def remove_wish(self, wish_id: int) -> bool:
        self.get_wish(wish_id)
        conn = get_connection()
        try:
            conn.execute("DELETE FROM wishlist WHERE wish_id = ?", (wish_id,))
            conn.commit()
            return True
        finally:
            conn.close()


# ════════════════════════════════════════════════════════════════
# REPORT BUSINESS
# ════════════════════════════════════════════════════════════════

class ReportBusiness:
    def collection_summary(self) -> Dict[str, Any]:
        conn = get_connection()
        try:
            artists = conn.execute("SELECT COUNT(*) AS c FROM artists").fetchone()["c"]
            groups = conn.execute("SELECT COUNT(*) AS c FROM groups").fetchone()["c"]
            albums = conn.execute("SELECT COUNT(*) AS c FROM albums").fetchone()["c"]
            collection_items = conn.execute("SELECT COUNT(*) AS c FROM collection_items").fetchone()["c"]
            photocards = conn.execute("SELECT COUNT(*) AS c FROM photocards").fetchone()["c"]
            wishlist = conn.execute("SELECT COUNT(*) AS c FROM wishlist").fetchone()["c"]
            total_spent = conn.execute(
                "SELECT COALESCE(SUM(purchase_price), 0) AS total FROM collection_items"
            ).fetchone()["total"]
            total_value = conn.execute(
                "SELECT COALESCE(SUM(estimated_value), 0) AS total FROM photocards"
            ).fetchone()["total"]

            return {
                "artists": artists,
                "groups": groups,
                "albums": albums,
                "collection_items": collection_items,
                "photocards": photocards,
                "wishlist_items": wishlist,
                "total_spent": float(total_spent or 0),
                "photocard_value": float(total_value or 0),
            }
        finally:
            conn.close()

    def photocards_per_artist(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT
                    a.artist_id,
                    a.stage_name,
                    COUNT(pc.photocard_id) AS photocard_count,
                    COALESCE(SUM(pc.estimated_value), 0) AS total_value
                FROM artists a
                LEFT JOIN photocards pc ON pc.artist_id = a.artist_id
                GROUP BY a.artist_id, a.stage_name
                ORDER BY photocard_count DESC, a.stage_name
                """
            ).fetchall()
            return _rows(rows)
        finally:
            conn.close()

    def albums_per_group(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT
                    g.group_id,
                    g.group_name,
                    COUNT(a.album_id) AS album_count
                FROM groups g
                LEFT JOIN albums a ON a.group_id = g.group_id
                GROUP BY g.group_id, g.group_name
                ORDER BY album_count DESC, g.group_name
                """
            ).fetchall()
            return _rows(rows)
        finally:
            conn.close()