"""
business/artist_service.py
--------------------------
Business layer for Artists.

Responsibilities
----------------
* Validate inputs before they reach the DAL (stage name required, debut year
  must be reasonable, gender must be one of the allowed values, etc.)
* Translate DAL sqlite3.Row objects into plain dicts for the service layer.
* Raise domain-specific exceptions instead of raw sqlite3 errors.
* Enforce business rules:
    - An artist cannot be deleted while they are still a member of a group
      (the DB cascade handles that, but we give a friendlier error here).
    - debut_year must be between 1990 and the current year.
    - gender must be one of: Male, Female, Non-binary  (or None).
"""

import logging
import sqlite3
from datetime import date
from typing import Optional, List, Dict, Any

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from kpop_dal import ArtistDAO, Artist
from business.exceptions import NotFoundError, ValidationError, DependencyError

logger = logging.getLogger(__name__)

# Allowed enum values (mirrors DB CHECK constraints)
VALID_GENDERS = {"Male", "Female", "Non-binary"}
MIN_DEBUT_YEAR = 1990


def _row_to_dict(row) -> Dict[str, Any]:
    """Convert a sqlite3.Row to a plain dict."""
    return dict(row) if row else {}


class ArtistBusiness:
    """
    Business-layer facade over ArtistDAO.

    All public methods return plain dicts (or lists of dicts) so the service
    layer never touches sqlite3.Row objects.
    """

    def __init__(self):
        self._dao = ArtistDAO()

    # ── helpers ───────────────────────────────────────────────────────────────

    def _validate(self, stage_name: str, gender: Optional[str],
                  debut_year: Optional[int]) -> None:
        """Apply business rules; raise ValidationError on any violation."""
        if not stage_name or not stage_name.strip():
            raise ValidationError("stage_name is required and cannot be blank.")
        if gender is not None and gender not in VALID_GENDERS:
            raise ValidationError(
                f"gender must be one of {sorted(VALID_GENDERS)} or null.")
        if debut_year is not None:
            current_year = date.today().year
            if debut_year < MIN_DEBUT_YEAR or debut_year > current_year:
                raise ValidationError(
                    f"debut_year must be between {MIN_DEBUT_YEAR} and {current_year}.")

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def add_artist(self, stage_name: str, real_name: Optional[str] = None,
                   birthdate: Optional[str] = None,
                   nationality: str = "South Korean",
                   gender: Optional[str] = None,
                   active: int = 1,
                   debut_year: Optional[int] = None,
                   notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new artist after validating inputs.

        Business rules enforced
        -----------------------
        * stage_name is mandatory.
        * gender (if provided) must be in VALID_GENDERS.
        * debut_year (if provided) must be >= 1990 and <= current year.

        Returns the newly created artist as a dict.
        """
        self._validate(stage_name, gender, debut_year)
        artist = Artist(
            stage_name=stage_name.strip(),
            real_name=real_name.strip() if real_name else None,
            birthdate=birthdate,
            nationality=nationality or "South Korean",
            gender=gender,
            active=active,
            debut_year=debut_year,
            notes=notes,
        )
        try:
            new_id = self._dao.create(artist)
            logger.info("Artist created: id=%s stage_name=%s", new_id, stage_name)
        except sqlite3.IntegrityError as exc:
            raise ValidationError(f"Database integrity error: {exc}") from exc

        return self.get_artist(new_id)

    def get_artist(self, artist_id: int) -> Dict[str, Any]:
        """Return a single artist by primary key or raise NotFoundError."""
        row = self._dao.get_by_id(artist_id)
        if not row:
            raise NotFoundError("Artist", artist_id)
        return _row_to_dict(row)

    def list_artists(self) -> List[Dict[str, Any]]:
        """Return all artists ordered by stage name."""
        return [_row_to_dict(r) for r in self._dao.get_all()]

    def search_artists(self, name: str) -> List[Dict[str, Any]]:
        """
        Search artists by stage name or real name (case-insensitive substring).

        Business rule: search term must be at least 1 character long.
        """
        if not name or not name.strip():
            raise ValidationError("Search term must be at least 1 character.")
        return [_row_to_dict(r) for r in self._dao.search_by_name(name.strip())]

    def update_artist(self, artist_id: int, stage_name: str,
                      real_name: Optional[str] = None,
                      birthdate: Optional[str] = None,
                      nationality: str = "South Korean",
                      gender: Optional[str] = None,
                      active: int = 1,
                      debut_year: Optional[int] = None,
                      notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Update an existing artist.

        Raises NotFoundError if the artist does not exist.
        Applies the same validation as add_artist.
        """
        # Ensure artist exists first
        self.get_artist(artist_id)
        self._validate(stage_name, gender, debut_year)

        artist = Artist(
            stage_name=stage_name.strip(),
            real_name=real_name.strip() if real_name else None,
            birthdate=birthdate,
            nationality=nationality or "South Korean",
            gender=gender,
            active=active,
            debut_year=debut_year,
            notes=notes,
            artist_id=artist_id,
        )
        self._dao.update(artist)
        logger.info("Artist updated: id=%s", artist_id)
        return self.get_artist(artist_id)

    def deactivate_artist(self, artist_id: int) -> Dict[str, Any]:
        """
        Business rule: soft-delete by setting active=0.
        Preferred over hard delete when the artist has photocards in the system.
        """
        existing = self.get_artist(artist_id)
        existing_obj = Artist(**{k: existing[k] for k in existing
                                 if k in Artist.__dataclass_fields__})
        existing_obj.active = 0
        self._dao.update(existing_obj)
        logger.info("Artist deactivated: id=%s", artist_id)
        return self.get_artist(artist_id)

    def remove_artist(self, artist_id: int) -> bool:
        """
        Hard-delete an artist.

        Business rule: if the artist has photocards in the system, raise
        DependencyError (the DAL FK constraint would catch it, but we give
        a clearer message).
        """
        self.get_artist(artist_id)  # raises NotFoundError if missing
        try:
            result = self._dao.delete(artist_id)
            logger.info("Artist deleted: id=%s", artist_id)
            return result
        except sqlite3.IntegrityError as exc:
            raise DependencyError(
                f"Cannot delete artist {artist_id}: they have associated photocards "
                f"or group memberships. Deactivate instead."
            ) from exc
