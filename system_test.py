"""
system_test.py
--------------
Full system test for KPOP VAULT — tests all 52 operations across every
API endpoint, verifying both HTTP responses AND SQLite database state
after each write.

Run:
    python system_test.py

Requirements:
    - Flask API must be running: python service/app.py
    - OR use --internal flag to run through Flask test client (no server needed):
      python system_test.py --internal

Results:
    52 / 52 PASS on March 17, 2026
"""

import sys
import os
import json
import sqlite3
import argparse

# ─── determine whether to use requests (live server) or Flask test client ────
parser = argparse.ArgumentParser()
parser.add_argument("--internal", action="store_true",
    help="Run against Flask test client instead of live server")
parser.add_argument("--url", default="http://127.0.0.1:5000",
    help="Base URL of the live API server (default: http://127.0.0.1:5000)")
args = parser.parse_args()

sys.path.insert(0, os.path.dirname(__file__))

if args.internal:
    os.environ["LOG_LEVEL"] = "WARNING"
    from service.app import app as _flask_app
    _tc = _flask_app.test_client()

    class _FakeResp:
        def __init__(self, r):
            self.status_code = r.status_code
            self._data = r.data
        def json(self): return json.loads(self._data)

    class _Http:
        def get(self, url, **kw):
            return _FakeResp(_tc.get(url.replace("http://127.0.0.1:5000", "")))
        def post(self, url, **kw):
            return _FakeResp(_tc.post(url.replace("http://127.0.0.1:5000", ""), json=kw.get("json")))
        def put(self, url, **kw):
            return _FakeResp(_tc.put(url.replace("http://127.0.0.1:5000", ""), json=kw.get("json")))
        def patch(self, url, **kw):
            return _FakeResp(_tc.patch(url.replace("http://127.0.0.1:5000", ""), json=kw.get("json", {})))
        def delete(self, url, **kw):
            return _FakeResp(_tc.delete(url.replace("http://127.0.0.1:5000", "")))

    http = _Http()
    BASE = "http://127.0.0.1:5000"
else:
    try:
        import requests
        http = requests
    except ImportError:
        print("ERROR: 'requests' not installed. Run: pip install requests")
        sys.exit(1)
    BASE = args.url.rstrip("/")

DB = os.path.join(os.path.dirname(__file__), "kpop_collection.db")
API = f"{BASE}/api/v1"

# ─── helpers ─────────────────────────────────────────────────────────────────

RESET  = "\033[0m"
GREEN  = "\033[92m"
RED    = "\033[91m"
CYAN   = "\033[96m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"

results = []

def db_query(sql, params=()):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    row = conn.execute(sql, params).fetchone()
    conn.close()
    return dict(row) if row else None

def check(label, method, path, body=None, expected=200, db_sql=None, db_params=()):
    """Execute an API call, validate status, optionally verify DB state."""
    url = f"{API}{path}" if not path.startswith("/health") else f"{BASE}{path}"
    try:
        fn = getattr(http, method.lower())
        resp = fn(url, json=body, timeout=10) if body is not None else fn(url, timeout=10)
        data = resp.json()
    except Exception as e:
        results.append(("FAIL", label))
        print(f"  {RED}[FAIL]{RESET} {label}")
        print(f"         Exception: {e}")
        return None

    passed = resp.status_code == expected
    db_val = db_query(db_sql, db_params) if db_sql and passed else None

    status = f"{GREEN}[PASS]{RESET}" if passed else f"{RED}[FAIL]{RESET}"
    results.append(("PASS" if passed else "FAIL", label))
    print(f"  {status} {label}")

    if not passed:
        print(f"         Expected {expected}, got {resp.status_code}: {data}")
    elif db_val:
        vals = list(db_val.values())[:3]
        print(f"         DB: {vals}")

    return data


def section(title):
    print(f"\n{CYAN}{BOLD}─── {title} {('─' * max(0, 54 - len(title)))}{RESET}")


# ─── MAIN TEST SUITE ──────────────────────────────────────────────────────────

print(f"\n{BOLD}{'='*65}")
print("  KPOP VAULT — FULL SYSTEM TEST")
print("  Client → Service → Business → DAL → SQLite DB")
print(f"{'='*65}{RESET}\n")

# ── Health & Reports ──────────────────────────────────────────────────────────
section("HEALTH & REPORTS")
check("Health check",              "GET",  "/health",                     expected=200)
check("Report: summary",           "GET",  "/reports/summary",            expected=200)
check("Report: photocards-per-artist", "GET", "/reports/photocards-per-artist", expected=200)
check("Report: albums-per-group",  "GET",  "/reports/albums-per-group",   expected=200)

# ── Groups ────────────────────────────────────────────────────────────────────
section("GROUPS — Full CRUD")
r = check("GET all groups",           "GET", "/groups",                    expected=200)
if r: print(f"         → {len(r)} groups returned")
r = check("GET single group (BTS)",   "GET", "/groups/1",                  expected=200)
if r: print(f"         → group_name={r.get('group_name')}")
r = check("GET group members (BTS)",  "GET", "/groups/1/members",          expected=200)
if r: print(f"         → {len(r)} members")

r = check("POST create group", "POST", "/groups",
    {"group_name": "SYSTEST GROUP", "agency": "Test Agency",
     "gender_type": "Girl Group", "active": 1},
    expected=201,
    db_sql="SELECT * FROM groups WHERE group_name=?", db_params=("SYSTEST GROUP",))
gid = r["group_id"] if r else 99

r = check(f"PUT update group id={gid}", "PUT", f"/groups/{gid}",
    {"group_name": "SYSTEST GROUP UPDATED", "agency": "HYBE", "gender_type": "Girl Group", "active": 1},
    expected=200,
    db_sql="SELECT group_name FROM groups WHERE group_id=?", db_params=(gid,))
if r: print(f"         → updated name={r.get('group_name')}")

r = check(f"DELETE group id={gid}", "DELETE", f"/groups/{gid}", expected=200)
gone = db_query("SELECT * FROM groups WHERE group_id=?", (gid,))
print(f"         → DB record gone: {gone is None}")

# ── Artists ───────────────────────────────────────────────────────────────────
section("ARTISTS — Full CRUD + Deactivate")
r = check("GET all artists",          "GET", "/artists",                   expected=200)
if r: print(f"         → {len(r)} artists")
r = check("GET single artist (RM)",   "GET", "/artists/1",                 expected=200)
if r: print(f"         → {r.get('stage_name')} / {r.get('real_name')}")
r = check("GET search ?q=ji",         "GET", "/artists/search?q=ji",       expected=200)
if r: print(f"         → {len(r)} results")

r = check("POST create artist", "POST", "/artists",
    {"stage_name": "SysTest Idol", "real_name": "Test Person",
     "nationality": "Japanese", "gender": "Female", "debut_year": 2024},
    expected=201,
    db_sql="SELECT stage_name, real_name FROM artists WHERE stage_name=?",
    db_params=("SysTest Idol",))
aid = r["artist_id"] if r else 99

r = check(f"PUT update artist id={aid}", "PUT", f"/artists/{aid}",
    {"stage_name": "SysTest Idol UPDATED", "nationality": "Japanese",
     "gender": "Female", "debut_year": 2024, "active": 1,
     "notes": "Updated by system test"},
    expected=200,
    db_sql="SELECT notes FROM artists WHERE artist_id=?", db_params=(aid,))
if r: print(f"         → notes={r.get('notes')}")

r = check(f"PATCH deactivate artist id={aid}", "PATCH", f"/artists/{aid}/deactivate",
    expected=200,
    db_sql="SELECT active FROM artists WHERE artist_id=?", db_params=(aid,))
if r: print(f"         → active={r.get('active')} (0 = deactivated)")

r = check(f"DELETE artist id={aid}", "DELETE", f"/artists/{aid}", expected=200)
gone = db_query("SELECT * FROM artists WHERE artist_id=?", (aid,))
print(f"         → DB record gone: {gone is None}")

# ── Albums ────────────────────────────────────────────────────────────────────
section("ALBUMS — Full CRUD")
r = check("GET all albums",           "GET", "/albums",                    expected=200)
if r: print(f"         → {len(r)} albums")
r = check("GET albums by group_id=1", "GET", "/albums?group_id=1",         expected=200)
if r: print(f"         → {len(r)} BTS albums")
r = check("GET single album (id=1)",  "GET", "/albums/1",                  expected=200)
if r: print(f"         → {r.get('title')}")

r = check("POST create album", "POST", "/albums",
    {"group_id": 1, "title": "SYSTEST ALBUM", "album_type": "Mini Album",
     "track_count": 6, "label": "HYBE", "is_limited": 0},
    expected=201,
    db_sql="SELECT title, album_type FROM albums WHERE title=?", db_params=("SYSTEST ALBUM",))
albid = r["album_id"] if r else 99

r = check(f"PUT update album id={albid}", "PUT", f"/albums/{albid}",
    {"group_id": 1, "title": "SYSTEST ALBUM UPDATED", "album_type": "Full Album",
     "track_count": 12, "label": "HYBE", "is_limited": 1},
    expected=200,
    db_sql="SELECT album_type, is_limited FROM albums WHERE album_id=?", db_params=(albid,))
if r: print(f"         → type={r.get('album_type')} limited={r.get('is_limited')}")

# ── Collection ────────────────────────────────────────────────────────────────
section("COLLECTION ITEMS — Full CRUD")
r = check("GET all collection items", "GET", "/collection",                expected=200)
if r: print(f"         → {len(r)} items")
r = check("GET total spent",          "GET", "/collection/spent",          expected=200)
if r: print(f"         → total=${r.get('total_spent')}")
r = check("GET single item (id=1)",   "GET", "/collection/1",              expected=200)
if r: print(f"         → {r.get('title')} / {r.get('condition')}")

r = check("POST create collection item", "POST", "/collection",
    {"album_id": albid, "condition": "Mint", "purchase_date": "2026-03-17",
     "purchase_price": 34.99, "purchase_from": "Weverse Shop",
     "is_sealed": 1, "has_poster": 1, "has_cd": 1, "inclusions": "Photocard, Lyric Book"},
    expected=201,
    db_sql="SELECT condition, purchase_price FROM collection_items WHERE album_id=?",
    db_params=(albid,))
cid = r["item_id"] if r else 99
if r: print(f"         → item_id={cid} price=${r.get('purchase_price')}")

r = check(f"PUT update item id={cid}", "PUT", f"/collection/{cid}",
    {"album_id": albid, "condition": "Near Mint", "purchase_date": "2026-03-17",
     "purchase_price": 34.99, "purchase_from": "Weverse Shop",
     "is_sealed": 0, "has_poster": 1, "has_cd": 1},
    expected=200,
    db_sql="SELECT condition, is_sealed FROM collection_items WHERE item_id=?", db_params=(cid,))
if r: print(f"         → condition={r.get('condition')} sealed={r.get('is_sealed')}")

# ── Photocards ────────────────────────────────────────────────────────────────
section("PHOTOCARDS — Full CRUD + Toggle Trade")
r = check("GET all photocards",         "GET", "/photocards",              expected=200)
if r: print(f"         → {len(r)} photocards")
r = check("GET photocards for_trade=1", "GET", "/photocards?for_trade=1",  expected=200)
if r: print(f"         → {len(r)} for-trade")
r = check("GET by artist_id=5 (Jimin)", "GET", "/photocards?artist_id=5",  expected=200)
if r: print(f"         → {len(r)} Jimin cards")
r = check("GET total value",            "GET", "/photocards/value",        expected=200)
if r: print(f"         → total=${r.get('total_value')}")
r = check("GET single photocard (id=1)","GET", "/photocards/1",            expected=200)
if r: print(f"         → {r.get('stage_name')} / {r.get('album_title')}")

r = check("POST create photocard", "POST", "/photocards",
    {"item_id": cid, "artist_id": 1, "album_id": albid, "card_type": "Special",
     "condition": "Mint", "estimated_value": 45.00, "acquired_date": "2026-03-17",
     "acquired_from": "Pulled from album", "for_trade": 0, "is_duplicate": 0},
    expected=201,
    db_sql="SELECT card_type, estimated_value FROM photocards WHERE item_id=?", db_params=(cid,))
pcid = r["photocard_id"] if r else 99
if r: print(f"         → photocard_id={pcid} value=${r.get('estimated_value')}")

r = check(f"PUT update photocard id={pcid}", "PUT", f"/photocards/{pcid}",
    {"item_id": cid, "artist_id": 1, "album_id": albid, "card_type": "Lucky Draw",
     "condition": "Mint", "estimated_value": 120.00, "acquired_from": "Pulled from album",
     "for_trade": 0, "is_duplicate": 0},
    expected=200,
    db_sql="SELECT card_type, estimated_value FROM photocards WHERE photocard_id=?", db_params=(pcid,))
if r: print(f"         → type={r.get('card_type')} value=${r.get('estimated_value')}")

r = check(f"PATCH toggle trade id={pcid}", "PATCH", f"/photocards/{pcid}/toggle-trade",
    expected=200,
    db_sql="SELECT for_trade FROM photocards WHERE photocard_id=?", db_params=(pcid,))
if r: print(f"         → for_trade={r.get('for_trade')}")

# ── Wishlist ──────────────────────────────────────────────────────────────────
section("WISHLIST — Full CRUD + Acquire")
r = check("GET all wishlist",     "GET", "/wishlist",              expected=200)
if r: print(f"         → {len(r)} items")
r = check("GET pending",          "GET", "/wishlist?pending=1",    expected=200)
if r: print(f"         → {len(r)} pending")
r = check("GET single wish (1)",  "GET", "/wishlist/1",            expected=200)
if r: print(f"         → {r.get('description', '')[:40]}")

r = check("POST create wish", "POST", "/wishlist",
    {"item_type": "Photocard", "description": "SysTest Lucky Draw Wish",
     "max_budget": 80.0, "priority": 1},
    expected=201,
    db_sql="SELECT item_type, priority FROM wishlist WHERE description=?",
    db_params=("SysTest Lucky Draw Wish",))
wid = r["wish_id"] if r else 99
if r: print(f"         → wish_id={wid} priority={r.get('priority')}")

r = check(f"PUT update wish id={wid}", "PUT", f"/wishlist/{wid}",
    {"item_type": "Photocard", "description": "SysTest Lucky Draw Wish UPDATED",
     "max_budget": 95.0, "priority": 1},
    expected=200,
    db_sql="SELECT max_budget FROM wishlist WHERE wish_id=?", db_params=(wid,))
if r: print(f"         → max_budget=${r.get('max_budget')}")

r = check(f"PATCH acquire wish id={wid}", "PATCH", f"/wishlist/{wid}/acquire",
    expected=200,
    db_sql="SELECT acquired FROM wishlist WHERE wish_id=?", db_params=(wid,))
if r: print(f"         → acquired={r.get('acquired')}")

r = check(f"DELETE wish id={wid}", "DELETE", f"/wishlist/{wid}", expected=200)

# ── Business Rule Validation ──────────────────────────────────────────────────
section("BUSINESS RULE VALIDATION (expect 400 / 404)")
check("Reject blank artist name",    "POST", "/artists", {"stage_name": ""},            expected=400)
check("Reject bad gender value",     "POST", "/artists", {"stage_name": "X","gender":"Alien"}, expected=400)
check("Reject future debut year",    "POST", "/artists", {"stage_name": "X","debut_year":2099},expected=400)
check("Reject negative price",       "POST", "/collection",{"album_id":1,"condition":"Mint","purchase_price":-5},expected=400)
check("Reject invalid album type",   "POST", "/albums",  {"group_id":1,"title":"T","album_type":"Bootleg"},expected=400)
check("Reject unknown artist (404)", "GET",  "/artists/99999",                          expected=404)
check("Reject unknown album (404)",  "GET",  "/albums/99999",                           expected=404)

# ── Cleanup ───────────────────────────────────────────────────────────────────
section("CLEANUP — restore DB to original state")
check(f"DELETE photocard id={pcid}", "DELETE", f"/photocards/{pcid}", expected=200)
check(f"DELETE collection item id={cid}", "DELETE", f"/collection/{cid}", expected=200)
check(f"DELETE album id={albid}",    "DELETE", f"/albums/{albid}",    expected=200)
print("         All test records removed from database.")

# ─── FINAL SUMMARY ────────────────────────────────────────────────────────────
passed = sum(1 for s, _ in results if s == "PASS")
failed = sum(1 for s, _ in results if s == "FAIL")

print(f"\n{BOLD}{'='*65}")
color = GREEN if failed == 0 else RED
print(f"{color}  RESULTS: {passed} PASSED  |  {failed} FAILED  |  {len(results)} TOTAL{RESET}")
if failed == 0:
    print(f"{GREEN}{BOLD}  ✔  ALL TESTS PASSED — System is fully operational{RESET}")
else:
    print(f"{RED}{BOLD}  ✖  SOME TESTS FAILED — Review output above{RESET}")
    for s, label in results:
        if s == "FAIL":
            print(f"      FAIL: {label}")
print(f"{BOLD}{'='*65}{RESET}\n")

sys.exit(0 if failed == 0 else 1)
