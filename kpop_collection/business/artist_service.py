"""
business/artist_service.py
Clean business layer for artists.

This version matches the actual artists table in schema.sql:
- artist_id
- stage_name
- real_name
- birthdate
- nationality
- gender
- active
- debut_year
- notes
- created_at

It does NOT depend on an Artist model class.
"""

from __future__ import annotations

import sqlite3
from datetime import date
from typing import Any, Dict, List, Optional

from kpop_dal import get_connection
from business.exceptions import NotFoundError, ValidationError, DependencyError


VALID_GENDERS = {"Male", "Female", "Non-binary"}
MIN_DEBUT_YEAR = 1990


def _row_to_dict(row) -> Dict[str, Any]:
    return dict(row) if row else {}


class ArtistBusiness:
    def _validate(
        self,
        stage_name: str,
        gender: Optional[str],
        debut_year: Optional[int],
        active: int,
    ) -> None:
        if not stage_name or not str(stage_name).strip():
            raise ValidationError("stage_name is required and cannot be blank.")

        if gender is not None and gender not in VALID_GENDERS:
            raise ValidationError(
                f"gender must be one of {sorted(VALID_GENDERS)} or null."
            )

        if debut_year is not None:
            current_year = date.today().year
            if debut_year < MIN_DEBUT_YEAR or debut_year > current_year:
                raise ValidationError(
                    f"debut_year must be between {MIN_DEBUT_YEAR} and {current_year}."
                )

        if int(active) not in (0, 1):
            raise ValidationError("active must be 0 or 1.")

    def list_artists(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM artists ORDER BY stage_name"
            ).fetchall()
            return [_row_to_dict(r) for r in rows]
        finally:
            conn.close()

    def get_artist(self, artist_id: int) -> Dict[str, Any]:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM artists WHERE artist_id = ?",
                (artist_id,),
            ).fetchone()
            if row is None:
                raise NotFoundError(f"Artist {artist_id} not found")
            return _row_to_dict(row)
        finally:
            conn.close()

    def search_artists(self, query: str) -> List[Dict[str, Any]]:
        if not query or not query.strip():
            return []

        like = f"%{query.strip()}%"
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT *
                FROM artists
                WHERE LOWER(stage_name) LIKE LOWER(?)
                   OR LOWER(COALESCE(real_name, '')) LIKE LOWER(?)
                ORDER BY stage_name
                """,
                (like, like),
            ).fetchall()
            return [_row_to_dict(r) for r in rows]
        finally:
            conn.close()

    def add_artist(
        self,
        stage_name: str,
        real_name: Optional[str] = None,
        birthdate: Optional[str] = None,
        nationality: str = "South Korean",
        gender: Optional[str] = None,
        active: int = 1,
        debut_year: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._validate(stage_name, gender, debut_year, active)

        conn = get_connection()
        try:
            cur = conn.execute(
                """
                INSERT INTO artists
                (stage_name, real_name, birthdate, nationality, gender, active, debut_year, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    stage_name.strip(),
                    real_name.strip() if real_name and real_name.strip() else None,
                    birthdate,
                    nationality or "South Korean",
                    gender,
                    int(active),
                    debut_year,
                    notes,
                ),
            )
            conn.commit()
            new_id = cur.lastrowid
        except sqlite3.IntegrityError as exc:
            raise ValidationError(f"Database integrity error: {exc}") from exc
        finally:
            conn.close()

        return self.get_artist(new_id)

    def update_artist(
        self,
        artist_id: int,
        stage_name: str,
        real_name: Optional[str] = None,
        birthdate: Optional[str] = None,
        nationality: str = "South Korean",
        gender: Optional[str] = None,
        active: int = 1,
        debut_year: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.get_artist(artist_id)
        self._validate(stage_name, gender, debut_year, active)

        conn = get_connection()
        try:
            conn.execute(
                """
                UPDATE artists
                SET stage_name = ?,
                    real_name = ?,
                    birthdate = ?,
                    nationality = ?,
                    gender = ?,
                    active = ?,
                    debut_year = ?,
                    notes = ?
                WHERE artist_id = ?
                """,
                (
                    stage_name.strip(),
                    real_name.strip() if real_name and real_name.strip() else None,
                    birthdate,
                    nationality or "South Korean",
                    gender,
                    int(active),
                    debut_year,
                    notes,
                    artist_id,
                ),
            )
            conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValidationError(f"Database integrity error: {exc}") from exc
        finally:
            conn.close()

        return self.get_artist(artist_id)

    def deactivate_artist(self, artist_id: int) -> Dict[str, Any]:
        artist = self.get_artist(artist_id)

        conn = get_connection()
        try:
            conn.execute(
                "UPDATE artists SET active = 0 WHERE artist_id = ?",
                (artist_id,),
            )
            conn.commit()
        finally:
            conn.close()

        artist["active"] = 0
        return artist

    def remove_artist(self, artist_id: int) -> Dict[str, Any]:
        self.get_artist(artist_id)

        conn = get_connection()
        try:
            conn.execute("DELETE FROM artists WHERE artist_id = ?", (artist_id,))
            conn.commit()
        except sqlite3.IntegrityError as exc:
            raise DependencyError(
                f"Cannot delete artist {artist_id}: they are still referenced by photocards, wishlist items, or group memberships."
            ) from exc
        finally:
            conn.close()

        return {"deleted": True, "artist_id": artist_id}