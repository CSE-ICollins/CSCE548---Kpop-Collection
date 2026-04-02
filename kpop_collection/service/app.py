"""
service/app.py
--------------
K-Pop Collection REST API — Service Layer
Hosted with: Flask (Python built-in WSGI)

HOW TO HOST
-----------
Local development (this file's directory):
    cd /path/to/kpop_project
    python service/app.py
    # API available at http://127.0.0.1:5000

Production (example — Render.com free tier):
    1. Push project to GitHub.
    2. Create a new "Web Service" on https://render.com
    3. Build command : pip install flask gunicorn
    4. Start command : gunicorn --chdir service app:app
    5. Set env var   : DB_PATH=/opt/render/project/src/kpop_collection.db

Production (example — Railway.app):
    1. Push to GitHub.
    2. New project → Deploy from GitHub repo.
    3. Set start command: gunicorn --chdir service app:app --bind 0.0.0.0:$PORT
    4. Set env var DB_PATH as needed.

Production (example — local with Gunicorn):
    pip install gunicorn
    gunicorn "service.app:create_app()" --bind 0.0.0.0:5000

Environment variables:
    DB_PATH   - absolute path to kpop_collection.db  (optional; defaults to
                ../kpop_collection.db relative to this file)
    LOG_LEVEL - DEBUG | INFO | WARNING  (default: INFO)
    PORT      - port to listen on when run directly (default: 5000)

API Base URL: /api/v1

Resources
---------
  /artists
  /groups
  /albums
  /collection
  /photocards
  /wishlist
  /reports

HTTP Methods used: GET, POST, PUT, DELETE
Response format  : JSON
Error format     : {"error": "<message>", "status": <http_code>}
"""

import os
import sys
import logging
from functools import wraps

# ── path setup so we can import from the project root ────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FRONTEND = os.path.join(_ROOT, "frontend")
sys.path.insert(0, _ROOT)

# Point the DAL at the right DB file (can be overridden by env var)
_db_path = os.environ.get("DB_PATH", os.path.join(_ROOT, "kpop_collection.db"))

# Patch the DAL module's DB_PATH before importing anything else
import kpop_dal as kpop_dal
kpop_dal.DB_PATH = _db_path

from flask import Flask, jsonify, request, Response
from business.artist_service import ArtistBusiness
from business.group_service import (
    GroupBusiness,
    AlbumBusiness,
    CollectionItemBusiness,
    PhotocardBusiness,
    WishlistBusiness,
    ReportBusiness,
)
from business.exceptions import (
    NotFoundError,
    ValidationError,
    DependencyError,
    KpopBusinessError,
)

# ── logging setup ─────────────────────────────────────────────────────────────
_log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(_ROOT, "logs", "api.log"), encoding="utf-8"),
    ],
)
logger = logging.getLogger("kpop.api")

# ── business layer singletons ─────────────────────────────────────────────────
_artist_biz = ArtistBusiness()
_group_biz = GroupBusiness()
_album_biz = AlbumBusiness()
_item_biz = CollectionItemBusiness()
_pc_biz = PhotocardBusiness()
_wish_biz = WishlistBusiness()
_report_biz = ReportBusiness()


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder=_FRONTEND, static_url_path="/static/frontend")

    @app.after_request
    def add_cors(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,PATCH,OPTIONS"
        return response

    @app.route("/api/v1/<path:ignored>", methods=["OPTIONS"])
    def options_handler(ignored=None):
        from flask import make_response
        r = make_response("", 204)
        r.headers["Access-Control-Allow-Origin"] = "*"
        r.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        r.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,PATCH,OPTIONS"
        return r

    def ok(data, status: int = 200) -> Response:
        return jsonify(data), status

    def err(message: str, status: int) -> Response:
        logger.warning("API error %s: %s", status, message)
        return jsonify({"error": message, "status": status}), status

    def handle_biz(func):
        """Decorator: map business exceptions → HTTP error responses."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except NotFoundError as e:
                return err(str(e), 404)
            except ValidationError as e:
                return err(str(e), 400)
            except DependencyError as e:
                return err(str(e), 409)
            except KpopBusinessError as e:
                return err(str(e), 400)
            except Exception as e:
                logger.exception("Unhandled error in %s", func.__name__)
                return err(f"Internal server error: {e}", 500)
        return wrapper

    def jbody() -> dict:
        """Parse JSON body; return empty dict on failure."""
        return request.get_json(silent=True) or {}

    # ══════════════════════════════════════════════════════════════════════════
    # ARTISTS   /api/v1/artists
    # ══════════════════════════════════════════════════════════════════════════

    @app.route("/api/v1/artists", methods=["GET"])
    @handle_biz
    def list_artists():
        return ok(_artist_biz.list_artists())

    @app.route("/api/v1/artists/search", methods=["GET"])
    @handle_biz
    def search_artists():
        q = request.args.get("q", "")
        return ok(_artist_biz.search_artists(q))

    @app.route("/api/v1/artists/<int:artist_id>", methods=["GET"])
    @handle_biz
    def get_artist(artist_id):
        return ok(_artist_biz.get_artist(artist_id))

    @app.route("/api/v1/artists", methods=["POST"])
    @handle_biz
    def create_artist():
        b = jbody()
        result = _artist_biz.add_artist(
            stage_name=b.get("stage_name", ""),
            real_name=b.get("real_name"),
            birthdate=b.get("birthdate"),
            nationality=b.get("nationality", "South Korean"),
            gender=b.get("gender"),
            active=b.get("active", 1),
            debut_year=b.get("debut_year"),
            notes=b.get("notes"),
        )
        return ok(result, 201)

    @app.route("/api/v1/artists/<int:artist_id>", methods=["PUT"])
    @handle_biz
    def update_artist(artist_id):
        b = jbody()
        result = _artist_biz.update_artist(
            artist_id=artist_id,
            stage_name=b.get("stage_name", ""),
            real_name=b.get("real_name"),
            birthdate=b.get("birthdate"),
            nationality=b.get("nationality", "South Korean"),
            gender=b.get("gender"),
            active=b.get("active", 1),
            debut_year=b.get("debut_year"),
            notes=b.get("notes"),
        )
        return ok(result)

    @app.route("/api/v1/artists/<int:artist_id>/deactivate", methods=["PATCH"])
    @handle_biz
    def deactivate_artist(artist_id):
        return ok(_artist_biz.deactivate_artist(artist_id))

    @app.route("/api/v1/artists/<int:artist_id>", methods=["DELETE"])
    @handle_biz
    def delete_artist(artist_id):
        _artist_biz.remove_artist(artist_id)
        return ok({"deleted": True, "artist_id": artist_id})

    # ══════════════════════════════════════════════════════════════════════════
    # GROUPS   /api/v1/groups
    # ══════════════════════════════════════════════════════════════════════════

    @app.route("/api/v1/groups", methods=["GET"])
    @handle_biz
    def list_groups():
        return ok(_group_biz.list_groups())

    @app.route("/api/v1/groups/<int:group_id>", methods=["GET"])
    @handle_biz
    def get_group(group_id):
        return ok(_group_biz.get_group(group_id))

    @app.route("/api/v1/groups/<int:group_id>/members", methods=["GET"])
    @handle_biz
    def get_group_members(group_id):
        return ok(_group_biz.get_group_members(group_id))

    @app.route("/api/v1/groups", methods=["POST"])
    @handle_biz
    def create_group():
        b = jbody()
        result = _group_biz.add_group(
            group_name=b.get("group_name", ""),
            agency=b.get("agency"),
            debut_date=b.get("debut_date"),
            fandom_name=b.get("fandom_name"),
            active=b.get("active", 1),
            gender_type=b.get("gender_type"),
            notes=b.get("notes"),
        )
        return ok(result, 201)

    @app.route("/api/v1/groups/<int:group_id>", methods=["PUT"])
    @handle_biz
    def update_group(group_id):
        b = jbody()
        result = _group_biz.update_group(
            group_id=group_id,
            group_name=b.get("group_name", ""),
            agency=b.get("agency"),
            debut_date=b.get("debut_date"),
            fandom_name=b.get("fandom_name"),
            active=b.get("active", 1),
            gender_type=b.get("gender_type"),
            notes=b.get("notes"),
        )
        return ok(result)

    @app.route("/api/v1/groups/<int:group_id>", methods=["DELETE"])
    @handle_biz
    def delete_group(group_id):
        _group_biz.remove_group(group_id)
        return ok({"deleted": True, "group_id": group_id})

    # ══════════════════════════════════════════════════════════════════════════
    # ALBUMS   /api/v1/albums
    # ══════════════════════════════════════════════════════════════════════════

    @app.route("/api/v1/albums", methods=["GET"])
    @handle_biz
    def list_albums():
        group_id = request.args.get("group_id")
        if group_id:
            return ok(_album_biz.list_albums_by_group(int(group_id)))
        return ok(_album_biz.list_albums())

    @app.route("/api/v1/albums/<int:album_id>", methods=["GET"])
    @handle_biz
    def get_album(album_id):
        return ok(_album_biz.get_album(album_id))

    @app.route("/api/v1/albums", methods=["POST"])
    @handle_biz
    def create_album():
        b = jbody()
        result = _album_biz.add_album(
            group_id=b.get("group_id", 0),
            title=b.get("title", ""),
            album_type=b.get("album_type", ""),
            release_date=b.get("release_date"),
            version_name=b.get("version_name"),
            track_count=b.get("track_count"),
            duration_mins=b.get("duration_mins"),
            label=b.get("label"),
            is_limited=b.get("is_limited", 0),
            notes=b.get("notes"),
        )
        return ok(result, 201)

    @app.route("/api/v1/albums/<int:album_id>", methods=["PUT"])
    @handle_biz
    def update_album(album_id):
        b = jbody()
        result = _album_biz.update_album(
            album_id=album_id,
            group_id=b.get("group_id", 0),
            title=b.get("title", ""),
            album_type=b.get("album_type", ""),
            release_date=b.get("release_date"),
            version_name=b.get("version_name"),
            track_count=b.get("track_count"),
            duration_mins=b.get("duration_mins"),
            label=b.get("label"),
            is_limited=b.get("is_limited", 0),
            notes=b.get("notes"),
        )
        return ok(result)

    @app.route("/api/v1/albums/<int:album_id>", methods=["DELETE"])
    @handle_biz
    def delete_album(album_id):
        _album_biz.remove_album(album_id)
        return ok({"deleted": True, "album_id": album_id})

    # ══════════════════════════════════════════════════════════════════════════
    # COLLECTION ITEMS   /api/v1/collection
    # ══════════════════════════════════════════════════════════════════════════

    @app.route("/api/v1/collection", methods=["GET"])
    @handle_biz
    def list_collection():
        return ok(_item_biz.list_items())

    @app.route("/api/v1/collection/spent", methods=["GET"])
    @handle_biz
    def total_spent():
        return ok({"total_spent": _item_biz.get_total_spent()})

    @app.route("/api/v1/collection/<int:item_id>", methods=["GET"])
    @handle_biz
    def get_collection_item(item_id):
        return ok(_item_biz.get_item(item_id))

    @app.route("/api/v1/collection", methods=["POST"])
    @handle_biz
    def create_collection_item():
        b = jbody()
        result = _item_biz.add_item(
            album_id=b.get("album_id", 0),
            condition=b.get("condition", "Mint"),
            purchase_date=b.get("purchase_date"),
            purchase_price=b.get("purchase_price"),
            purchase_from=b.get("purchase_from"),
            is_sealed=b.get("is_sealed", 0),
            has_poster=b.get("has_poster", 0),
            has_cd=b.get("has_cd", 1),
            inclusions=b.get("inclusions"),
            notes=b.get("notes"),
        )
        return ok(result, 201)

    @app.route("/api/v1/collection/<int:item_id>", methods=["PUT"])
    @handle_biz
    def update_collection_item(item_id):
        b = jbody()
        result = _item_biz.update_item(
            item_id=item_id,
            album_id=b.get("album_id", 0),
            condition=b.get("condition", "Mint"),
            purchase_date=b.get("purchase_date"),
            purchase_price=b.get("purchase_price"),
            purchase_from=b.get("purchase_from"),
            is_sealed=b.get("is_sealed", 0),
            has_poster=b.get("has_poster", 0),
            has_cd=b.get("has_cd", 1),
            inclusions=b.get("inclusions"),
            notes=b.get("notes"),
        )
        return ok(result)

    @app.route("/api/v1/collection/<int:item_id>", methods=["DELETE"])
    @handle_biz
    def delete_collection_item(item_id):
        _item_biz.remove_item(item_id)
        return ok({"deleted": True, "item_id": item_id})

    # ══════════════════════════════════════════════════════════════════════════
    # PHOTOCARDS   /api/v1/photocards
    # ══════════════════════════════════════════════════════════════════════════

    @app.route("/api/v1/photocards", methods=["GET"])
    @handle_biz
    def list_photocards():
        artist_id = request.args.get("artist_id")
        trade_only = request.args.get("for_trade")
        if artist_id:
            return ok(_pc_biz.list_by_artist(int(artist_id)))
        if trade_only:
            return ok(_pc_biz.list_for_trade())
        return ok(_pc_biz.list_photocards())

    @app.route("/api/v1/photocards/value", methods=["GET"])
    @handle_biz
    def total_photocard_value():
        return ok({"total_value": _pc_biz.get_total_value()})

    @app.route("/api/v1/photocards/<int:photocard_id>", methods=["GET"])
    @handle_biz
    def get_photocard(photocard_id):
        return ok(_pc_biz.get_photocard(photocard_id))

    @app.route("/api/v1/photocards", methods=["POST"])
    @handle_biz
    def create_photocard():
        b = jbody()
        result = _pc_biz.add_photocard(
            item_id=b.get("item_id", 0),
            artist_id=b.get("artist_id", 0),
            album_id=b.get("album_id", 0),
            card_type=b.get("card_type", "Standard"),
            condition=b.get("condition", "Mint"),
            acquired_date=b.get("acquired_date"),
            acquired_from=b.get("acquired_from"),
            estimated_value=b.get("estimated_value"),
            is_duplicate=b.get("is_duplicate", 0),
            for_trade=b.get("for_trade", 0),
            notes=b.get("notes"),
        )
        return ok(result, 201)

    @app.route("/api/v1/photocards/<int:photocard_id>", methods=["PUT"])
    @handle_biz
    def update_photocard(photocard_id):
        b = jbody()
        result = _pc_biz.update_photocard(
            photocard_id=photocard_id,
            item_id=b.get("item_id", 0),
            artist_id=b.get("artist_id", 0),
            album_id=b.get("album_id", 0),
            card_type=b.get("card_type", "Standard"),
            condition=b.get("condition", "Mint"),
            acquired_date=b.get("acquired_date"),
            acquired_from=b.get("acquired_from"),
            estimated_value=b.get("estimated_value"),
            is_duplicate=b.get("is_duplicate", 0),
            for_trade=b.get("for_trade", 0),
            notes=b.get("notes"),
        )
        return ok(result)

    @app.route("/api/v1/photocards/<int:photocard_id>/toggle-trade", methods=["PATCH"])
    @handle_biz
    def toggle_trade(photocard_id):
        return ok(_pc_biz.toggle_trade_flag(photocard_id))

    @app.route("/api/v1/photocards/<int:photocard_id>", methods=["DELETE"])
    @handle_biz
    def delete_photocard(photocard_id):
        _pc_biz.remove_photocard(photocard_id)
        return ok({"deleted": True, "photocard_id": photocard_id})

    # ══════════════════════════════════════════════════════════════════════════
    # WISHLIST   /api/v1/wishlist
    # ══════════════════════════════════════════════════════════════════════════

    @app.route("/api/v1/wishlist", methods=["GET"])
    @handle_biz
    def list_wishlist():
        pending_only = request.args.get("pending")
        if pending_only:
            return ok(_wish_biz.list_pending())
        return ok(_wish_biz.list_wishes())

    @app.route("/api/v1/wishlist/<int:wish_id>", methods=["GET"])
    @handle_biz
    def get_wish(wish_id):
        return ok(_wish_biz.get_wish(wish_id))

    @app.route("/api/v1/wishlist", methods=["POST"])
    @handle_biz
    def create_wish():
        b = jbody()
        result = _wish_biz.add_wish(
            item_type=b.get("item_type", ""),
            description=b.get("description", ""),
            album_id=b.get("album_id"),
            artist_id=b.get("artist_id"),
            max_budget=b.get("max_budget"),
            priority=b.get("priority", 3),
            notes=b.get("notes"),
        )
        return ok(result, 201)

    @app.route("/api/v1/wishlist/<int:wish_id>", methods=["PUT"])
    @handle_biz
    def update_wish(wish_id):
        b = jbody()
        result = _wish_biz.update_wish(
            wish_id=wish_id,
            item_type=b.get("item_type", ""),
            description=b.get("description", ""),
            album_id=b.get("album_id"),
            artist_id=b.get("artist_id"),
            max_budget=b.get("max_budget"),
            priority=b.get("priority", 3),
            acquired=b.get("acquired", 0),
            notes=b.get("notes"),
        )
        return ok(result)

    @app.route("/api/v1/wishlist/<int:wish_id>/acquire", methods=["PATCH"])
    @handle_biz
    def acquire_wish(wish_id):
        return ok(_wish_biz.mark_acquired(wish_id))

    @app.route("/api/v1/wishlist/<int:wish_id>", methods=["DELETE"])
    @handle_biz
    def delete_wish(wish_id):
        _wish_biz.remove_wish(wish_id)
        return ok({"deleted": True, "wish_id": wish_id})

    # ══════════════════════════════════════════════════════════════════════════
    # REPORTS   /api/v1/reports
    # ══════════════════════════════════════════════════════════════════════════

    @app.route("/api/v1/reports/summary", methods=["GET"])
    @handle_biz
    def report_summary():
        return ok(_report_biz.collection_summary())

    @app.route("/api/v1/reports/photocards-per-artist", methods=["GET"])
    @handle_biz
    def report_pcs_per_artist():
        return ok(_report_biz.photocards_per_artist())

    @app.route("/api/v1/reports/albums-per-group", methods=["GET"])
    @handle_biz
    def report_albums_per_group():
        return ok(_report_biz.albums_per_group())

    # ── health check ──────────────────────────────────────────────────────────
    @app.route("/health", methods=["GET"])
    def health():
        return ok({"status": "ok", "service": "kpop-collection-api", "version": "1.0"})

    # ── Serve the web frontend ─────────────────────────────────────────────────
    @app.route("/")
    def index():
        from flask import send_from_directory
        return send_from_directory(_FRONTEND, "index.html")

    @app.route("/app")
    def frontend_app():
        from flask import send_from_directory
        return send_from_directory(_FRONTEND, "index.html")

    logger.info("K-Pop Collection API initialized. DB: %s", _db_path)
    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("Starting Flask dev server on port %s", port)
    app.run(host="0.0.0.0", port=port, debug=False)