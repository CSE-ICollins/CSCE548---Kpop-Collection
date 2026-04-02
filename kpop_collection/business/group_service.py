"""
business/group_service.py
-------------------------
Business layer for Groups, Albums, Collection Items, Photocards, Wishlist, and Reports.

Each *Business class:
  * Validates inputs against business rules (not just DB constraints).
  * Translates sqlite3.Row → plain dict before returning to callers.
  * Raises domain exceptions (NotFoundError, ValidationError, DependencyError).
  * Logs significant operations for auditability.

Business Rules Enforced
-----------------------
GroupBusiness
  - group_name is required.
  - gender_type must be one of allowed values if provided.

AlbumBusiness
  - title and album_type are required.
  - album_type must be one of the allowed values.
  - group_id must reference an existing group.

CollectionItemBusiness
  - album_id must reference an existing album.
  - condition must be one of the allowed values.
  - purchase_price cannot be negative.

PhotocardBusiness
  - item_id, artist_id, album_id are all required and must reference existing rows.
  - estimated_value cannot be negative.
  - card_type and condition must be within allowed values.

WishlistBusiness
  - description is required.
  - item_type must be one of: Album, Photocard, Merch.
  - priority must be between 1 and 5.
  - max_budget cannot be negative.

ReportBusiness
  - Thin wrapper; no input to validate, but returns enriched summary data.
"""

import logging
import sqlite3
from typing import Optional, List, Dict, Any

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from kpop_collection.kpop_dal import (
    GroupDAO, Group,
    AlbumDAO, Album,
    CollectionItemDAO, CollectionItem,
    PhotocardDAO, Photocard,
    WishlistDAO, WishlistItem,
    ReportDAO,
)
from business.exceptions import NotFoundError, ValidationError, DependencyError

logger = logging.getLogger(__name__)

# ── enum allowed values (mirror DB CHECK constraints) ────────────────────────
VALID_GENDER_TYPES = {"Boy Group", "Girl Group", "Co-ed", "Solo"}
VALID_ALBUM_TYPES  = {"Mini Album", "Full Album", "Single Album",
                      "Repackage", "Special Album", "OST", "Collaboration"}
VALID_CONDITIONS   = {"Mint", "Near Mint", "Very Good", "Good", "Fair", "Poor"}
VALID_CARD_TYPES   = {"Standard", "Unit", "Solo", "Special",
                      "Lucky Draw", "POB", "Pre-order"}
VALID_WISH_TYPES   = {"Album", "Photocard", "Merch"}


def _row(row) -> Dict[str, Any]:
    return dict(row) if row else {}


def _rows(rows) -> List[Dict[str, Any]]:
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# GROUP BUSINESS
# ═══════════════════════════════════════════════════════════════════════════════

class GroupBusiness:
    """Business facade over GroupDAO."""

    def __init__(self):
        self._dao = GroupDAO()

    def _validate(self, group_name: str, gender_type: Optional[str]):
        if not group_name or not group_name.strip():
            raise ValidationError("group_name is required.")
        if gender_type and gender_type not in VALID_GENDER_TYPES:
            raise ValidationError(
                f"gender_type must be one of {sorted(VALID_GENDER_TYPES)} or null.")

    # CRUD ────────────────────────────────────────────────────────────────────

    def add_group(self, group_name: str, agency: Optional[str] = None,
                  debut_date: Optional[str] = None, fandom_name: Optional[str] = None,
                  active: int = 1, gender_type: Optional[str] = None,
                  notes: Optional[str] = None) -> Dict[str, Any]:
        """Create a new group. Returns the created group dict."""
        self._validate(group_name, gender_type)
        g = Group(group_name=group_name.strip(), agency=agency, debut_date=debut_date,
                  fandom_name=fandom_name, active=active, gender_type=gender_type,
                  notes=notes)
        try:
            new_id = self._dao.create(g)
            logger.info("Group created: id=%s name=%s", new_id, group_name)
        except sqlite3.IntegrityError as exc:
            raise ValidationError(f"Group name already exists: {group_name}") from exc
        return self.get_group(new_id)

    def get_group(self, group_id: int) -> Dict[str, Any]:
        row = self._dao.get_by_id(group_id)
        if not row:
            raise NotFoundError("Group", group_id)
        return _row(row)

    def list_groups(self) -> List[Dict[str, Any]]:
        return _rows(self._dao.get_all())

    def get_group_members(self, group_id: int) -> List[Dict[str, Any]]:
        """Return member list; raises NotFoundError if group is unknown."""
        self.get_group(group_id)  # existence check
        return _rows(self._dao.get_members(group_id))

    def update_group(self, group_id: int, group_name: str,
                     agency: Optional[str] = None, debut_date: Optional[str] = None,
                     fandom_name: Optional[str] = None, active: int = 1,
                     gender_type: Optional[str] = None,
                     notes: Optional[str] = None) -> Dict[str, Any]:
        self.get_group(group_id)
        self._validate(group_name, gender_type)
        g = Group(group_name=group_name.strip(), agency=agency, debut_date=debut_date,
                  fandom_name=fandom_name, active=active, gender_type=gender_type,
                  notes=notes, group_id=group_id)
        self._dao.update(g)
        logger.info("Group updated: id=%s", group_id)
        return self.get_group(group_id)

    def remove_group(self, group_id: int) -> bool:
        """
        Hard-delete a group.
        Business rule: cannot delete a group that has albums in the DB.
        """
        self.get_group(group_id)
        try:
            result = self._dao.delete(group_id)
            logger.info("Group deleted: id=%s", group_id)
            return result
        except sqlite3.IntegrityError as exc:
            raise DependencyError(
                f"Cannot delete group {group_id}: it has associated albums."
            ) from exc


# ═══════════════════════════════════════════════════════════════════════════════
# ALBUM BUSINESS
# ═══════════════════════════════════════════════════════════════════════════════

class AlbumBusiness:
    """Business facade over AlbumDAO."""

    def __init__(self):
        self._dao   = AlbumDAO()
        self._grp   = GroupDAO()

    def _validate(self, group_id: int, title: str, album_type: str):
        if not title or not title.strip():
            raise ValidationError("title is required.")
        if album_type not in VALID_ALBUM_TYPES:
            raise ValidationError(
                f"album_type must be one of {sorted(VALID_ALBUM_TYPES)}.")
        if not self._grp.get_by_id(group_id):
            raise NotFoundError("Group", group_id)

    def add_album(self, group_id: int, title: str, album_type: str,
                  release_date: Optional[str] = None,
                  version_name: Optional[str] = None,
                  track_count: Optional[int] = None,
                  duration_mins: Optional[float] = None,
                  label: Optional[str] = None,
                  is_limited: int = 0,
                  notes: Optional[str] = None) -> Dict[str, Any]:
        """Add an album to the catalog."""
        self._validate(group_id, title, album_type)
        if track_count is not None and track_count <= 0:
            raise ValidationError("track_count must be a positive integer.")
        a = Album(group_id=group_id, title=title.strip(), album_type=album_type,
                  release_date=release_date, version_name=version_name,
                  track_count=track_count, duration_mins=duration_mins,
                  label=label, is_limited=is_limited, notes=notes)
        new_id = self._dao.create(a)
        logger.info("Album created: id=%s title=%s", new_id, title)
        return self.get_album(new_id)

    def get_album(self, album_id: int) -> Dict[str, Any]:
        row = self._dao.get_by_id(album_id)
        if not row:
            raise NotFoundError("Album", album_id)
        return _row(row)

    def list_albums(self) -> List[Dict[str, Any]]:
        return _rows(self._dao.get_all())

    def list_albums_by_group(self, group_id: int) -> List[Dict[str, Any]]:
        """Return albums for a specific group (group must exist)."""
        if not self._grp.get_by_id(group_id):
            raise NotFoundError("Group", group_id)
        return _rows(self._dao.get_by_group(group_id))

    def update_album(self, album_id: int, group_id: int, title: str,
                     album_type: str, release_date: Optional[str] = None,
                     version_name: Optional[str] = None,
                     track_count: Optional[int] = None,
                     duration_mins: Optional[float] = None,
                     label: Optional[str] = None,
                     is_limited: int = 0,
                     notes: Optional[str] = None) -> Dict[str, Any]:
        self.get_album(album_id)
        self._validate(group_id, title, album_type)
        a = Album(group_id=group_id, title=title.strip(), album_type=album_type,
                  release_date=release_date, version_name=version_name,
                  track_count=track_count, duration_mins=duration_mins,
                  label=label, is_limited=is_limited, notes=notes,
                  album_id=album_id)
        self._dao.update(a)
        logger.info("Album updated: id=%s", album_id)
        return self.get_album(album_id)

    def remove_album(self, album_id: int) -> bool:
        """Business rule: cannot delete album if collection items reference it."""
        self.get_album(album_id)
        try:
            result = self._dao.delete(album_id)
            logger.info("Album deleted: id=%s", album_id)
            return result
        except sqlite3.IntegrityError as exc:
            raise DependencyError(
                f"Cannot delete album {album_id}: it has collection items."
            ) from exc


# ═══════════════════════════════════════════════════════════════════════════════
# COLLECTION ITEM BUSINESS
# ═══════════════════════════════════════════════════════════════════════════════

class CollectionItemBusiness:
    """Business facade over CollectionItemDAO."""

    def __init__(self):
        self._dao = CollectionItemDAO()
        self._alb = AlbumDAO()

    def _validate(self, album_id: int, condition: str,
                  purchase_price: Optional[float]):
        if not self._alb.get_by_id(album_id):
            raise NotFoundError("Album", album_id)
        if condition not in VALID_CONDITIONS:
            raise ValidationError(
                f"condition must be one of {sorted(VALID_CONDITIONS)}.")
        if purchase_price is not None and purchase_price < 0:
            raise ValidationError("purchase_price cannot be negative.")

    def add_item(self, album_id: int, condition: str = "Mint",
                 purchase_date: Optional[str] = None,
                 purchase_price: Optional[float] = None,
                 purchase_from: Optional[str] = None,
                 is_sealed: int = 0, has_poster: int = 0, has_cd: int = 1,
                 inclusions: Optional[str] = None,
                 notes: Optional[str] = None) -> Dict[str, Any]:
        """Add a physical album copy to the collection."""
        self._validate(album_id, condition, purchase_price)
        c = CollectionItem(album_id=album_id, condition=condition,
                           purchase_date=purchase_date, purchase_price=purchase_price,
                           purchase_from=purchase_from, is_sealed=is_sealed,
                           has_poster=has_poster, has_cd=has_cd,
                           inclusions=inclusions, notes=notes)
        new_id = self._dao.create(c)
        logger.info("CollectionItem created: id=%s album_id=%s", new_id, album_id)
        return self.get_item(new_id)

    def get_item(self, item_id: int) -> Dict[str, Any]:
        row = self._dao.get_by_id(item_id)
        if not row:
            raise NotFoundError("CollectionItem", item_id)
        return _row(row)

    def list_items(self) -> List[Dict[str, Any]]:
        return _rows(self._dao.get_all())

    def get_total_spent(self) -> float:
        return self._dao.get_total_spent()

    def update_item(self, item_id: int, album_id: int, condition: str,
                    purchase_date: Optional[str] = None,
                    purchase_price: Optional[float] = None,
                    purchase_from: Optional[str] = None,
                    is_sealed: int = 0, has_poster: int = 0, has_cd: int = 1,
                    inclusions: Optional[str] = None,
                    notes: Optional[str] = None) -> Dict[str, Any]:
        self.get_item(item_id)
        self._validate(album_id, condition, purchase_price)
        c = CollectionItem(album_id=album_id, condition=condition,
                           purchase_date=purchase_date, purchase_price=purchase_price,
                           purchase_from=purchase_from, is_sealed=is_sealed,
                           has_poster=has_poster, has_cd=has_cd,
                           inclusions=inclusions, notes=notes, item_id=item_id)
        self._dao.update(c)
        logger.info("CollectionItem updated: id=%s", item_id)
        return self.get_item(item_id)

    def remove_item(self, item_id: int) -> bool:
        """Business rule: removing an item cascades to its photocards (by DB design)."""
        self.get_item(item_id)
        result = self._dao.delete(item_id)
        logger.info("CollectionItem deleted: id=%s", item_id)
        return result


# ═══════════════════════════════════════════════════════════════════════════════
# PHOTOCARD BUSINESS
# ═══════════════════════════════════════════════════════════════════════════════

class PhotocardBusiness:
    """Business facade over PhotocardDAO."""

    def __init__(self):
        self._dao  = PhotocardDAO()
        self._item = CollectionItemDAO()
        from kpop_collection.kpop_dal import ArtistDAO
        self._art  = ArtistDAO()
        self._alb  = AlbumDAO()

    def _validate(self, item_id: int, artist_id: int, album_id: int,
                  card_type: str, condition: str,
                  estimated_value: Optional[float]):
        if not self._item.get_by_id(item_id):
            raise NotFoundError("CollectionItem", item_id)
        if not self._art.get_by_id(artist_id):
            raise NotFoundError("Artist", artist_id)
        if not self._alb.get_by_id(album_id):
            raise NotFoundError("Album", album_id)
        if card_type not in VALID_CARD_TYPES:
            raise ValidationError(
                f"card_type must be one of {sorted(VALID_CARD_TYPES)}.")
        if condition not in VALID_CONDITIONS:
            raise ValidationError(
                f"condition must be one of {sorted(VALID_CONDITIONS)}.")
        if estimated_value is not None and estimated_value < 0:
            raise ValidationError("estimated_value cannot be negative.")

    def add_photocard(self, item_id: int, artist_id: int, album_id: int,
                      card_type: str = "Standard", condition: str = "Mint",
                      acquired_date: Optional[str] = None,
                      acquired_from: Optional[str] = None,
                      estimated_value: Optional[float] = None,
                      is_duplicate: int = 0, for_trade: int = 0,
                      notes: Optional[str] = None) -> Dict[str, Any]:
        """Add a photocard to the collection."""
        self._validate(item_id, artist_id, album_id, card_type,
                       condition, estimated_value)
        p = Photocard(item_id=item_id, artist_id=artist_id, album_id=album_id,
                      card_type=card_type, condition=condition,
                      acquired_date=acquired_date, acquired_from=acquired_from,
                      estimated_value=estimated_value, is_duplicate=is_duplicate,
                      for_trade=for_trade, notes=notes)
        new_id = self._dao.create(p)
        logger.info("Photocard created: id=%s artist_id=%s", new_id, artist_id)
        return self.get_photocard(new_id)

    def get_photocard(self, photocard_id: int) -> Dict[str, Any]:
        row = self._dao.get_by_id(photocard_id)
        if not row:
            raise NotFoundError("Photocard", photocard_id)
        return _row(row)

    def list_photocards(self) -> List[Dict[str, Any]]:
        return _rows(self._dao.get_all())

    def list_for_trade(self) -> List[Dict[str, Any]]:
        """Business query: return cards currently marked for trade."""
        return _rows(self._dao.get_for_trade())

    def list_by_artist(self, artist_id: int) -> List[Dict[str, Any]]:
        if not self._art.get_by_id(artist_id):
            raise NotFoundError("Artist", artist_id)
        return _rows(self._dao.get_by_artist(artist_id))

    def get_total_value(self) -> float:
        return self._dao.get_total_value()

    def toggle_trade_flag(self, photocard_id: int) -> Dict[str, Any]:
        """
        Business action: flip the for_trade flag.
        Returns the updated photocard dict.
        """
        existing = self.get_photocard(photocard_id)
        p = Photocard(
            item_id=existing["item_id"],
            artist_id=existing["artist_id"],
            album_id=existing["album_id"],
            card_type=existing["card_type"],
            condition=existing["condition"],
            acquired_date=existing.get("acquired_date"),
            acquired_from=existing.get("acquired_from"),
            estimated_value=existing.get("estimated_value"),
            is_duplicate=existing["is_duplicate"],
            for_trade=0 if existing["for_trade"] else 1,
            notes=existing.get("notes"),
            photocard_id=photocard_id,
        )
        self._dao.update(p)
        logger.info("Photocard trade-flag toggled: id=%s new_flag=%s",
                    photocard_id, p.for_trade)
        return self.get_photocard(photocard_id)

    def update_photocard(self, photocard_id: int, item_id: int, artist_id: int,
                         album_id: int, card_type: str = "Standard",
                         condition: str = "Mint",
                         acquired_date: Optional[str] = None,
                         acquired_from: Optional[str] = None,
                         estimated_value: Optional[float] = None,
                         is_duplicate: int = 0, for_trade: int = 0,
                         notes: Optional[str] = None) -> Dict[str, Any]:
        self.get_photocard(photocard_id)
        self._validate(item_id, artist_id, album_id, card_type,
                       condition, estimated_value)
        p = Photocard(item_id=item_id, artist_id=artist_id, album_id=album_id,
                      card_type=card_type, condition=condition,
                      acquired_date=acquired_date, acquired_from=acquired_from,
                      estimated_value=estimated_value, is_duplicate=is_duplicate,
                      for_trade=for_trade, notes=notes,
                      photocard_id=photocard_id)
        self._dao.update(p)
        logger.info("Photocard updated: id=%s", photocard_id)
        return self.get_photocard(photocard_id)

    def remove_photocard(self, photocard_id: int) -> bool:
        self.get_photocard(photocard_id)
        result = self._dao.delete(photocard_id)
        logger.info("Photocard deleted: id=%s", photocard_id)
        return result


# ═══════════════════════════════════════════════════════════════════════════════
# WISHLIST BUSINESS
# ═══════════════════════════════════════════════════════════════════════════════

class WishlistBusiness:
    """Business facade over WishlistDAO."""

    def __init__(self):
        self._dao = WishlistDAO()

    def _validate(self, item_type: str, description: str,
                  priority: int, max_budget: Optional[float]):
        if not description or not description.strip():
            raise ValidationError("description is required.")
        if item_type not in VALID_WISH_TYPES:
            raise ValidationError(
                f"item_type must be one of {sorted(VALID_WISH_TYPES)}.")
        if not (1 <= priority <= 5):
            raise ValidationError("priority must be between 1 (highest) and 5 (lowest).")
        if max_budget is not None and max_budget < 0:
            raise ValidationError("max_budget cannot be negative.")

    def add_wish(self, item_type: str, description: str,
                 album_id: Optional[int] = None,
                 artist_id: Optional[int] = None,
                 max_budget: Optional[float] = None,
                 priority: int = 3,
                 notes: Optional[str] = None) -> Dict[str, Any]:
        """Add an item to the wishlist."""
        self._validate(item_type, description, priority, max_budget)
        w = WishlistItem(item_type=item_type, description=description.strip(),
                         album_id=album_id, artist_id=artist_id,
                         max_budget=max_budget, priority=priority, notes=notes)
        new_id = self._dao.create(w)
        logger.info("Wishlist item created: id=%s", new_id)
        return self.get_wish(new_id)

    def get_wish(self, wish_id: int) -> Dict[str, Any]:
        row = self._dao.get_by_id(wish_id)
        if not row:
            raise NotFoundError("WishlistItem", wish_id)
        return _row(row)

    def list_wishes(self) -> List[Dict[str, Any]]:
        return _rows(self._dao.get_all())

    def list_pending(self) -> List[Dict[str, Any]]:
        """Business query: return only items not yet acquired, sorted by priority."""
        return _rows(self._dao.get_pending())

    def mark_acquired(self, wish_id: int) -> Dict[str, Any]:
        """Business action: mark a wishlist item as obtained."""
        self.get_wish(wish_id)
        self._dao.mark_acquired(wish_id)
        logger.info("Wishlist item marked acquired: id=%s", wish_id)
        return self.get_wish(wish_id)

    def update_wish(self, wish_id: int, item_type: str, description: str,
                    album_id: Optional[int] = None,
                    artist_id: Optional[int] = None,
                    max_budget: Optional[float] = None,
                    priority: int = 3, acquired: int = 0,
                    notes: Optional[str] = None) -> Dict[str, Any]:
        self.get_wish(wish_id)
        self._validate(item_type, description, priority, max_budget)
        w = WishlistItem(item_type=item_type, description=description.strip(),
                         album_id=album_id, artist_id=artist_id,
                         max_budget=max_budget, priority=priority,
                         acquired=acquired, notes=notes, wish_id=wish_id)
        self._dao.update(w)
        logger.info("Wishlist item updated: id=%s", wish_id)
        return self.get_wish(wish_id)

    def remove_wish(self, wish_id: int) -> bool:
        self.get_wish(wish_id)
        result = self._dao.delete(wish_id)
        logger.info("Wishlist item deleted: id=%s", wish_id)
        return result


# ═══════════════════════════════════════════════════════════════════════════════
# REPORT BUSINESS
# ═══════════════════════════════════════════════════════════════════════════════

class ReportBusiness:
    """Business facade over ReportDAO — adds computed/derived fields."""

    def __init__(self):
        self._dao = ReportDAO()

    def collection_summary(self) -> Dict[str, Any]:
        """
        Return a summary enriched with derived fields:
        - average_album_cost  (business-derived)
        - net_collection_value (photocards + albums)
        """
        raw = self._dao.collection_summary()
        avg = (raw["total_spent"] / raw["total_albums"]
               if raw["total_albums"] > 0 else 0.0)
        net = raw["total_spent"] + raw["photocard_value"]
        raw["average_album_cost"]   = round(avg, 2)
        raw["net_collection_value"] = round(net, 2)
        return raw

    def photocards_per_artist(self) -> List[Dict[str, Any]]:
        return _rows(self._dao.photocards_per_artist())

    def albums_per_group(self) -> List[Dict[str, Any]]:
        return _rows(self._dao.albums_per_group())
