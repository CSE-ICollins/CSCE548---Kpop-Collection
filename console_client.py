"""
client/console_client.py
------------------------
Console-based front end for the K-Pop Collection REST API.

This client communicates ONLY through HTTP calls to the service layer —
it never imports the DAL or business layer directly.

Usage
-----
    # Make sure the API server is running first:
    #   python service/app.py          (or gunicorn service.app:app)

    python client/console_client.py [--base-url http://127.0.0.1:5000]

Arguments
---------
    --base-url   Base URL of the API  (default: http://127.0.0.1:5000)
    --demo       Run the automated CRUD demo and exit (no interactive menu)
"""

import sys
import os
import json
import argparse

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library not found. Install with: pip install requests")
    sys.exit(1)

try:
    from tabulate import tabulate
except ImportError:
    def tabulate(rows, headers=(), tablefmt="simple"):
        lines = [" | ".join(str(h) for h in headers),
                 "-" * 60] if headers else []
        for row in rows:
            lines.append(" | ".join(str(c) for c in row))
        return "\n".join(lines)

# ── colour helpers ────────────────────────────────────────────────────────────
PINK  = "\033[95m"
CYAN  = "\033[96m"
GREEN = "\033[92m"
YELLOW= "\033[93m"
RED   = "\033[91m"
BOLD  = "\033[1m"
RESET = "\033[0m"

BASE_URL = "http://127.0.0.1:5000"


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _url(path: str) -> str:
    return f"{BASE_URL}/api/v1{path}"


def _handle(resp: requests.Response) -> dict:
    """Parse response; raise RuntimeError with message on non-2xx."""
    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}
    if not resp.ok:
        msg = data.get("error", str(data))
        raise RuntimeError(f"HTTP {resp.status_code}: {msg}")
    return data


def GET(path: str, params: dict = None) -> dict:
    return _handle(requests.get(_url(path), params=params, timeout=10))

def POST(path: str, body: dict) -> dict:
    return _handle(requests.post(_url(path), json=body, timeout=10))

def PUT(path: str, body: dict) -> dict:
    return _handle(requests.put(_url(path), json=body, timeout=10))

def PATCH(path: str, body: dict = None) -> dict:
    return _handle(requests.patch(_url(path), json=body or {}, timeout=10))

def DELETE(path: str) -> dict:
    return _handle(requests.delete(_url(path), timeout=10))


# ── display helpers ───────────────────────────────────────────────────────────

def banner():
    print(f"""
{PINK}{BOLD}╔══════════════════════════════════════════════════════╗
║   🎵  K-POP COLLECTION  —  API CONSOLE CLIENT  🎵   ║
║         Talking to: {BASE_URL:<32}║
╚══════════════════════════════════════════════════════╝{RESET}
""")

def header(text: str):
    print(f"\n{CYAN}{BOLD}{'─'*56}\n  {text}\n{'─'*56}{RESET}")

def ok(msg: str): print(f"  {GREEN}✔  {msg}{RESET}")
def err(msg: str): print(f"  {RED}✖  {msg}{RESET}")
def info(msg: str): print(f"  {YELLOW}ℹ  {msg}{RESET}")
def pause(): input(f"\n{YELLOW}  Press Enter to continue...{RESET}")

def print_json(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))

def print_table(rows: list, keys: list, headers: list = None):
    if not rows:
        info("No records found.")
        return
    headers = headers or keys
    data = [[r.get(k, "—") for k in keys] for r in rows]
    print(tabulate(data, headers=headers, tablefmt="rounded_outline"))
    info(f"{len(rows)} record(s).")


# ══════════════════════════════════════════════════════════════════════════════
# AUTOMATED CRUD DEMO
# ══════════════════════════════════════════════════════════════════════════════

def run_demo():
    """
    Demonstrates the full Create → Read → Update → Delete cycle for
    each resource type via the REST API.
    """
    print(f"\n{PINK}{BOLD}{'═'*60}")
    print("  AUTOMATED CRUD DEMO — K-Pop Collection API")
    print(f"{'═'*60}{RESET}\n")

    # ── 1. Health check ───────────────────────────────────────────────────────
    header("Step 0: Health Check")
    h = _handle(requests.get(f"{BASE_URL}/health", timeout=10))
    ok(f"API status: {h.get('status')}  version: {h.get('version')}")

    # ── 2. ARTISTS ────────────────────────────────────────────────────────────
    header("Step 1: Artists — Full CRUD")

    print(f"\n  {BOLD}[CREATE]{RESET} Adding new artist 'Chaewon'...")
    artist = POST("/artists", {
        "stage_name": "Chaewon",
        "real_name": "Kim Chae-won",
        "nationality": "South Korean",
        "gender": "Female",
        "debut_year": 2019,
        "notes": "Added via API demo"
    })
    ok(f"Created artist id={artist['artist_id']} stage_name={artist['stage_name']}")

    a_id = artist["artist_id"]
    print(f"\n  {BOLD}[READ]{RESET} Fetching artist id={a_id}...")
    fetched = GET(f"/artists/{a_id}")
    ok(f"stage_name={fetched['stage_name']}  nationality={fetched['nationality']}")

    print(f"\n  {BOLD}[UPDATE]{RESET} Updating artist id={a_id}...")
    updated = PUT(f"/artists/{a_id}", {
        "stage_name": "Chaewon",
        "real_name": "Kim Chae-won",
        "nationality": "South Korean",
        "gender": "Female",
        "debut_year": 2019,
        "active": 1,
        "notes": "Updated via API demo — LE SSERAFIM member"
    })
    ok(f"Updated notes: {updated['notes']}")

    print(f"\n  {BOLD}[READ AGAIN]{RESET} Confirming update...")
    confirm = GET(f"/artists/{a_id}")
    ok(f"notes now: {confirm['notes']}")

    print(f"\n  {BOLD}[DELETE]{RESET} Deleting artist id={a_id}...")
    del_resp = DELETE(f"/artists/{a_id}")
    ok(f"Deleted: {del_resp['deleted']}")

    print(f"\n  {BOLD}[READ AFTER DELETE]{RESET} Expecting 404...")
    try:
        GET(f"/artists/{a_id}")
        err("Expected 404 but got a response!")
    except RuntimeError as e:
        ok(f"Got expected error → {e}")

    # ── 3. GROUPS ─────────────────────────────────────────────────────────────
    header("Step 2: Groups — Full CRUD")

    print(f"\n  {BOLD}[CREATE]{RESET} Adding group 'LE SSERAFIM'...")
    group = POST("/groups", {
        "group_name": "LE SSERAFIM",
        "agency": "Source Music / HYBE",
        "debut_date": "2022-05-02",
        "fandom_name": "FEARNOT",
        "active": 1,
        "gender_type": "Girl Group"
    })
    ok(f"Created group id={group['group_id']} name={group['group_name']}")
    g_id = group["group_id"]

    fetched_g = GET(f"/groups/{g_id}")
    ok(f"Fetched: {fetched_g['group_name']}  fandom={fetched_g['fandom_name']}")

    updated_g = PUT(f"/groups/{g_id}", {
        "group_name": "LE SSERAFIM",
        "agency": "Source Music / HYBE Labels",
        "debut_date": "2022-05-02",
        "fandom_name": "FEARNOT",
        "active": 1,
        "gender_type": "Girl Group",
        "notes": "5-member girl group"
    })
    ok(f"Updated agency → {updated_g['agency']}")

    DELETE(f"/groups/{g_id}")
    ok(f"Group {g_id} deleted.")
    try:
        GET(f"/groups/{g_id}")
        err("Expected 404!")
    except RuntimeError as e:
        ok(f"Confirmed deletion → {e}")

    # ── 4. WISHLIST ───────────────────────────────────────────────────────────
    header("Step 3: Wishlist — Full CRUD + Acquire Action")

    wish = POST("/wishlist", {
        "item_type": "Album",
        "description": "LE SSERAFIM EASY Mini Album (Standard Ver.)",
        "max_budget": 35.0,
        "priority": 1,
        "notes": "Top priority for next haul"
    })
    ok(f"Created wish id={wish['wish_id']} priority={wish['priority']}")
    w_id = wish["wish_id"]

    GET(f"/wishlist/{w_id}")
    ok("Read wish OK")

    updated_w = PUT(f"/wishlist/{w_id}", {
        "item_type": "Album",
        "description": "LE SSERAFIM EASY Mini Album (Standard Ver.)",
        "max_budget": 40.0,
        "priority": 1,
        "notes": "Budget bumped to $40"
    })
    ok(f"Updated budget → ${updated_w['max_budget']}")

    acquired = PATCH(f"/wishlist/{w_id}/acquire")
    ok(f"Marked acquired → acquired={acquired['acquired']}")

    DELETE(f"/wishlist/{w_id}")
    ok("Wish deleted.")

    # ── 5. COLLECTION ─────────────────────────────────────────────────────────
    header("Step 4: Collection Item — Full CRUD")

    item = POST("/collection", {
        "album_id": 1,
        "condition": "Mint",
        "purchase_date": "2026-03-17",
        "purchase_price": 32.99,
        "purchase_from": "Weverse Shop",
        "is_sealed": 1,
        "has_poster": 1,
        "inclusions": "Photocard, Poster, Lyric Book"
    })
    ok(f"Created collection item id={item['item_id']}")
    ci_id = item["item_id"]

    GET(f"/collection/{ci_id}")
    ok("Read item OK")

    updated_ci = PUT(f"/collection/{ci_id}", {
        "album_id": 1,
        "condition": "Near Mint",
        "purchase_date": "2026-03-17",
        "purchase_price": 32.99,
        "purchase_from": "Weverse Shop",
        "is_sealed": 0,
        "has_poster": 1,
        "inclusions": "Photocard, Poster, Lyric Book"
    })
    ok(f"Updated condition → {updated_ci['condition']}")

    DELETE(f"/collection/{ci_id}")
    ok("Collection item deleted.")

    # ── 6. Validation errors ──────────────────────────────────────────────────
    header("Step 5: Business Rule Validation")

    tests = [
        ("Blank artist name", lambda: POST("/artists", {"stage_name": ""})),
        ("Bad gender value",  lambda: POST("/artists", {"stage_name": "X", "gender": "Robot"})),
        ("Future debut year", lambda: POST("/artists", {"stage_name": "X", "debut_year": 2099})),
        ("Negative price",    lambda: POST("/collection", {"album_id": 1, "condition": "Mint", "purchase_price": -5})),
        ("Bad priority",      lambda: POST("/wishlist", {"item_type": "Album", "description": "X", "priority": 0})),
        ("Nonexistent artist",lambda: GET("/artists/99999")),
    ]

    for label, fn in tests:
        try:
            fn()
            err(f"{label} → SHOULD HAVE FAILED")
        except RuntimeError as e:
            ok(f"{label} → correctly rejected: {str(e)[:70]}")

    # ── 7. Reports ────────────────────────────────────────────────────────────
    header("Step 6: Reports")

    summary = GET("/reports/summary")
    print(f"""
  {BOLD}Collection Summary{RESET}
  ─────────────────────────────────
  Albums owned         : {summary['total_albums']}
  Total spent          : ${summary['total_spent']:.2f}
  Avg album cost       : ${summary['average_album_cost']:.2f}
  Photocards owned     : {summary['total_photocards']}
  Photocard value      : ${summary['photocard_value']:.2f}
  Net collection value : ${summary['net_collection_value']:.2f}
  Wishlist pending     : {summary['wishlist_pending']}
""")

    print(f"\n  {BOLD}Photocards per Artist (top 5):{RESET}")
    pca = GET("/reports/photocards-per-artist")[:5]
    print_table(pca, ["stage_name", "card_count", "total_value"],
                ["Artist", "Cards", "Total Value $"])

    print(f"\n  {BOLD}Albums per Group (top 5):{RESET}")
    apg = GET("/reports/albums-per-group")[:5]
    print_table(apg, ["group_name", "owned_copies", "total_spent"],
                ["Group", "Copies", "Spent $"])

    print(f"\n{GREEN}{BOLD}{'═'*60}")
    print("  ✅  DEMO COMPLETE — All CRUD operations verified!")
    print(f"{'═'*60}{RESET}\n")


# ══════════════════════════════════════════════════════════════════════════════
# INTERACTIVE MENUS
# ══════════════════════════════════════════════════════════════════════════════

def menu_artists():
    while True:
        header("ARTISTS")
        print("  1. List all artists")
        print("  2. Search artists")
        print("  3. Get artist by ID")
        print("  4. Add artist")
        print("  5. Update artist")
        print("  6. Deactivate artist (soft delete)")
        print("  7. Delete artist")
        print("  0. Back")
        c = input("\n  Choice: ").strip()

        if c == "1":
            artists = GET("/artists")
            print_table(artists,
                ["artist_id","stage_name","real_name","nationality","gender","debut_year","active"],
                ["ID","Stage","Real Name","Nationality","Gender","Debut","Active"])
            pause()
        elif c == "2":
            q = input("  Search term: ").strip()
            try:
                results = GET("/artists/search", {"q": q})
                print_table(results,
                    ["artist_id","stage_name","real_name","nationality"],
                    ["ID","Stage Name","Real Name","Nationality"])
            except RuntimeError as e: err(str(e))
            pause()
        elif c == "3":
            aid = input("  Artist ID: ").strip()
            try: print_json(GET(f"/artists/{aid}"))
            except RuntimeError as e: err(str(e))
            pause()
        elif c == "4":
            try:
                result = POST("/artists", {
                    "stage_name": input("  Stage name: ").strip(),
                    "real_name":  input("  Real name (optional): ").strip() or None,
                    "nationality":input("  Nationality [South Korean]: ").strip() or "South Korean",
                    "gender":     input("  Gender (Male/Female/Non-binary): ").strip() or None,
                    "debut_year": int(d) if (d := input("  Debut year (optional): ").strip()) else None,
                    "notes":      input("  Notes (optional): ").strip() or None,
                })
                ok(f"Artist created with id={result['artist_id']}")
            except (RuntimeError, ValueError) as e: err(str(e))
            pause()
        elif c == "5":
            try:
                aid = input("  Artist ID to update: ").strip()
                current = GET(f"/artists/{aid}")
                ok(f"Editing: {current['stage_name']}")
                result = PUT(f"/artists/{aid}", {
                    "stage_name":  input(f"  Stage name [{current['stage_name']}]: ").strip() or current["stage_name"],
                    "real_name":   input(f"  Real name [{current.get('real_name')}]: ").strip() or current.get("real_name"),
                    "nationality": input(f"  Nationality [{current['nationality']}]: ").strip() or current["nationality"],
                    "gender":      current.get("gender"),
                    "debut_year":  current.get("debut_year"),
                    "active":      current.get("active", 1),
                    "notes":       input(f"  Notes [{current.get('notes')}]: ").strip() or current.get("notes"),
                })
                ok(f"Updated: {result['stage_name']}")
            except RuntimeError as e: err(str(e))
            pause()
        elif c == "6":
            aid = input("  Artist ID to deactivate: ").strip()
            try:
                r = PATCH(f"/artists/{aid}/deactivate")
                ok(f"Artist {aid} active={r['active']}")
            except RuntimeError as e: err(str(e))
            pause()
        elif c == "7":
            aid = input("  Artist ID to DELETE: ").strip()
            if input("  Confirm delete? (yes/no): ").strip().lower() == "yes":
                try:
                    DELETE(f"/artists/{aid}")
                    ok("Deleted.")
                except RuntimeError as e: err(str(e))
            pause()
        elif c == "0":
            break


def menu_groups():
    while True:
        header("GROUPS")
        print("  1. List all groups")
        print("  2. Get group by ID")
        print("  3. Get group members")
        print("  4. Add group")
        print("  5. Delete group")
        print("  0. Back")
        c = input("\n  Choice: ").strip()

        if c == "1":
            groups = GET("/groups")
            print_table(groups,
                ["group_id","group_name","agency","fandom_name","gender_type","active"],
                ["ID","Group","Agency","Fandom","Type","Active"])
            pause()
        elif c == "2":
            gid = input("  Group ID: ").strip()
            try: print_json(GET(f"/groups/{gid}"))
            except RuntimeError as e: err(str(e))
            pause()
        elif c == "3":
            gid = input("  Group ID: ").strip()
            try:
                members = GET(f"/groups/{gid}/members")
                print_table(members,
                    ["artist_id","stage_name","real_name","position"],
                    ["ID","Stage Name","Real Name","Position"])
            except RuntimeError as e: err(str(e))
            pause()
        elif c == "4":
            try:
                result = POST("/groups", {
                    "group_name":  input("  Group name: ").strip(),
                    "agency":      input("  Agency (optional): ").strip() or None,
                    "debut_date":  input("  Debut date YYYY-MM-DD (optional): ").strip() or None,
                    "fandom_name": input("  Fandom name (optional): ").strip() or None,
                    "gender_type": input("  Type (Boy Group/Girl Group/Co-ed/Solo): ").strip() or None,
                })
                ok(f"Group created: id={result['group_id']} name={result['group_name']}")
            except RuntimeError as e: err(str(e))
            pause()
        elif c == "5":
            gid = input("  Group ID to DELETE: ").strip()
            if input("  Confirm? (yes/no): ").strip().lower() == "yes":
                try: ok(str(DELETE(f"/groups/{gid}")))
                except RuntimeError as e: err(str(e))
            pause()
        elif c == "0":
            break


def menu_wishlist():
    while True:
        header("WISHLIST")
        print("  1. View pending wishlist")
        print("  2. View all wishlist items")
        print("  3. Add wish")
        print("  4. Mark as acquired")
        print("  5. Delete wish")
        print("  0. Back")
        c = input("\n  Choice: ").strip()

        if c in ("1", "2"):
            items = GET("/wishlist", {"pending": "1"} if c == "1" else None)
            print_table(items,
                ["wish_id","item_type","description","max_budget","priority","acquired"],
                ["ID","Type","Description","Budget","Priority","Got"])
            pause()
        elif c == "3":
            try:
                result = POST("/wishlist", {
                    "item_type":   input("  Type (Album/Photocard/Merch): ").strip(),
                    "description": input("  Description: ").strip(),
                    "max_budget":  float(b) if (b := input("  Budget $ (optional): ").strip()) else None,
                    "priority":    int(input("  Priority 1-5 [3]: ").strip() or "3"),
                })
                ok(f"Wish added: id={result['wish_id']}")
            except (RuntimeError, ValueError) as e: err(str(e))
            pause()
        elif c == "4":
            wid = input("  Wish ID to mark acquired: ").strip()
            try:
                r = PATCH(f"/wishlist/{wid}/acquire")
                ok(f"Acquired! wish_id={r['wish_id']} acquired={r['acquired']}")
            except RuntimeError as e: err(str(e))
            pause()
        elif c == "5":
            wid = input("  Wish ID to delete: ").strip()
            if input("  Confirm? (yes/no): ").strip().lower() == "yes":
                try: ok(str(DELETE(f"/wishlist/{wid}")))
                except RuntimeError as e: err(str(e))
            pause()
        elif c == "0":
            break


def menu_reports():
    header("REPORTS")
    try:
        summary = GET("/reports/summary")
        print(f"""
  {BOLD}Collection Summary{RESET}
  ────────────────────────────────────────
  Albums owned          : {GREEN}{summary['total_albums']}{RESET}
  Total spent           : {GREEN}${summary['total_spent']:.2f}{RESET}
  Average album cost    : {GREEN}${summary['average_album_cost']:.2f}{RESET}
  Photocards owned      : {GREEN}{summary['total_photocards']}{RESET}
  Photocard value       : {GREEN}${summary['photocard_value']:.2f}{RESET}
  Net collection value  : {GREEN}${summary['net_collection_value']:.2f}{RESET}
  Wishlist pending      : {YELLOW}{summary['wishlist_pending']}{RESET}
""")
        print(f"  {BOLD}Photocards per Artist:{RESET}")
        pca = GET("/reports/photocards-per-artist")
        print_table(pca, ["stage_name", "card_count", "total_value"],
                    ["Artist", "Cards", "Total Value $"])

        print(f"\n  {BOLD}Albums per Group:{RESET}")
        apg = GET("/reports/albums-per-group")
        print_table(apg, ["group_name", "owned_copies", "total_spent"],
                    ["Group", "Copies Owned", "Spent $"])
    except RuntimeError as e:
        err(str(e))
    pause()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    global BASE_URL

    parser = argparse.ArgumentParser(description="K-Pop Collection API Console Client")
    parser.add_argument("--base-url", default="http://127.0.0.1:5000",
                        help="API base URL (default: http://127.0.0.1:5000)")
    parser.add_argument("--demo", action="store_true",
                        help="Run automated CRUD demo and exit")
    args = parser.parse_args()
    BASE_URL = args.base_url.rstrip("/")

    # Verify server is reachable
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        resp.raise_for_status()
    except Exception as e:
        print(f"\n{RED}Cannot reach API at {BASE_URL}{RESET}")
        print(f"  Make sure the server is running: python service/app.py")
        print(f"  Error: {e}\n")
        sys.exit(1)

    os.system("cls" if os.name == "nt" else "clear")
    banner()

    if args.demo:
        run_demo()
        return

    # Interactive menu
    while True:
        print(f"  {BOLD}1.{RESET} 🎤  Artists")
        print(f"  {BOLD}2.{RESET} 👥  Groups")
        print(f"  {BOLD}3.{RESET} 📊  Reports")
        print(f"  {BOLD}4.{RESET} ⭐  Wishlist")
        print(f"  {BOLD}5.{RESET} 🔁  Run Automated CRUD Demo")
        print(f"  {BOLD}0.{RESET} 🚪  Exit")
        c = input(f"\n{PINK}  Choose:{RESET} ").strip()

        if   c == "1": menu_artists()
        elif c == "2": menu_groups()
        elif c == "3": menu_reports()
        elif c == "4": menu_wishlist()
        elif c == "5": run_demo()
        elif c == "0":
            print(f"\n{PINK}  Annyeong! 안녕! 👋{RESET}\n")
            break


if __name__ == "__main__":
    main()
