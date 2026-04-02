"""
business/artist_service.py
---------------------------
Business layer for the 'artists' resource.

Sits between Flask (service/app.py) and the database, enforcing business
rules and returning plain dicts that JSON-serialize cleanly.

Business rules enforced:
  - stage_name must be non-empty
  - gender, if supplied, must be Male | Female | Non-binary | Mixed
  - debut_year, if supplied, must be 1990 – current year
  - active must be 0 or 1
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date
from typing   import Optional

from kpop_dal            import get_connection
from business.exceptions import NotFoundError, ValidationError, DependencyError

_VALID_GENDERS = {"Male", "Female", "Non-binary", "Mixed"}


def _row(r) -> dict:
    return dict(r) if r else {}

def _rows(rs) -> list:
    return [dict(r) for r in rs]


class ArtistBusiness:
    """Business logic for solo K-pop artists."""

    # ── validation ────────────────────────────────────────────────────────────

    def _validate(self, stage_name: str, gender, debut_year, active):
        if not stage_name or not stage_name.strip():
            raise ValidationError("stage_name is required and cannot be blank.")
        if gender is not None and gender not in _VALID_GENDERS:
            raise ValidationError(
                f"Invalid gender '{gender}'. "
                f"Allowed: {', '.join(sorted(_VALID_GENDERS))}."
            )
        if debut_year is not None:
            current_year = date.today().year
            if not (1990 <= int(debut_year) <= current_year):
                raise ValidationError(
                    f"debut_year must be between 1990 and {current_year}."
                )
        if int(active) not in (0, 1):
            raise ValidationError("active must be 0 or 1.")

    # ── helpers ───────────────────────────────────────────────────────────────

    def _get_raw(self, artist_id: int) -> dict:
        conn = get_connection()
        row  = conn.execute(
            "SELECT * FROM artists WHERE artist_id = ?", (artist_id,)
        ).fetchone()
        conn.close()
        if row is None:
            raise NotFoundError(f"Artist with id={artist_id} not found.")
        return _row(row)

    # ── public API (called by service layer) ──────────────────────────────────

    def list_artists(self) -> list:
        """Return all artists ordered by stage_name."""
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM artists ORDER BY stage_name"
        ).fetchall()
        conn.close()
        return _rows(rows)

    def search_artists(self, query: str) -> list:
        """Return artists whose stage_name or real_name contains the query."""
        q = f"%{query.lower().strip()}%"
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM artists "
            "WHERE LOWER(stage_name) LIKE ? OR LOWER(COALESCE(real_name,'')) LIKE ? "
            "ORDER BY stage_name",
            (q, q)
        ).fetchall()
        conn.close()
        return _rows(rows)

    def get_artist(self, artist_id: int) -> dict:
        """Return one artist by ID; raise NotFoundError if missing."""
        return self._get_raw(artist_id)

    def add_artist(self, stage_name: str, real_name=None, birthdate=None,
                   nationality: str = "South Korean", gender=None,
                   active: int = 1, debut_year=None, notes=None) -> dict:
        """Validate and create a new artist. Returns the created artist dict."""
        self._validate(stage_name, gender, debut_year, active)
        conn = get_connection()
        cur  = conn.execute(
            "INSERT INTO artists "
            "(stage_name, real_name, birthdate, nationality, gender, active, debut_year, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (stage_name.strip(), real_name, birthdate,
             nationality or "South Korean", gender, int(active),
             int(debut_year) if debut_year else None, notes)
        )
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return self.get_artist(new_id)

    def update_artist(self, artist_id: int, stage_name: str, real_name=None,
                      birthdate=None, nationality: str = "South Korean",
                      gender=None, active: int = 1, debut_year=None,
                      notes=None) -> dict:
        """Validate and fully update an existing artist."""
        self._get_raw(artist_id)  # raises NotFoundError if missing
        self._validate(stage_name, gender, debut_year, active)
        conn = get_connection()
        conn.execute(
            "UPDATE artists SET stage_name=?, real_name=?, birthdate=?, "
            "nationality=?, gender=?, active=?, debut_year=?, notes=? "
            "WHERE artist_id=?",
            (stage_name.strip(), real_name, birthdate,
             nationality or "South Korean", gender, int(active),
             int(debut_year) if debut_year else None, notes, artist_id)
        )
        conn.commit()
        conn.close()
        return self.get_artist(artist_id)

    def deactivate_artist(self, artist_id: int) -> dict:
        """Soft-delete: set active = 0."""
        self._get_raw(artist_id)  # raises NotFoundError if missing
        conn = get_connection()
        conn.execute("UPDATE artists SET active=0 WHERE artist_id=?", (artist_id,))
        conn.commit()
        conn.close()
        return self.get_artist(artist_id)

    def remove_artist(self, artist_id: int) -> None:
        """Hard-delete an artist. Raises DependencyError if albums still exist."""
        self._get_raw(artist_id)  # raises NotFoundError if missing
        conn = get_connection()
        try:
            conn.execute("DELETE FROM artists WHERE artist_id=?", (artist_id,))
            conn.commit()
        except Exception as e:
            if "FOREIGN KEY" in str(e).upper() or "RESTRICT" in str(e).upper():
                raise DependencyError(
                    f"Cannot delete artist {artist_id}: records still reference it."
                )
            raise
        finally:
            conn.close()