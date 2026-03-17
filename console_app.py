"""
console_app.py  –  K-Pop Collection Manager (console front end)
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data_access"))

from data_access import (
    init_db, get_connection,
    ArtistDAO, AlbumDAO, CollectionItemDAO, PhotocardDAO, WishlistDAO
)

# ─────────────────────────────────────────
# Formatting helpers
# ─────────────────────────────────────────

W = 72

def header(title: str):
    print("\n" + "═" * W)
    print(f"  ✦  {title}")
    print("═" * W)

def subheader(title: str):
    print(f"\n  ── {title} {'─' * (W - len(title) - 6)}")

def row_line(*cols, widths=None):
    if widths:
        parts = [str(c).ljust(w) for c, w in zip(cols, widths)]
    else:
        parts = [str(c) for c in cols]
    print("  " + "  ".join(parts))

def yn(val) -> str:
    return "Yes" if val else "No"

def money(val) -> str:
    return f"${val:.2f}" if val is not None else "—"

# ─────────────────────────────────────────
# Menu sections
# ─────────────────────────────────────────

def show_all_artists():
    header("ALL ARTISTS")
    artists = ArtistDAO.get_all()
    row_line("ID", "Name", "Debut", "Agency", "Fandom", "Active",
             widths=[4, 18, 6, 22, 12, 7])
    print("  " + "─" * (W - 2))
    for a in artists:
        row_line(a["artist_id"], a["name"], a["debut_year"] or "—",
                 a["agency"] or "—", a["fandom_name"] or "—",
                 yn(a["is_active"]),
                 widths=[4, 18, 6, 22, 12, 7])


def show_all_albums():
    header("ALL ALBUMS")
    albums = AlbumDAO.get_all()
    row_line("ID", "Artist", "Title", "Type", "Versions",
             widths=[4, 14, 30, 14, 9])
    print("  " + "─" * (W - 2))
    for al in albums:
        row_line(al["album_id"], al["artist_name"], al["title"][:28],
                 al["album_type"], al["num_versions"],
                 widths=[4, 14, 30, 14, 9])


def show_collection():
    header("MY COLLECTION")
    items = CollectionItemDAO.get_all()
    total = CollectionItemDAO.collection_value()
    row_line("ID", "Artist", "Album", "Version", "Cond.", "Paid",
             widths=[4, 14, 24, 16, 10, 8])
    print("  " + "─" * (W - 2))
    for it in items:
        row_line(it["item_id"], it["artist_name"], it["album_title"][:22],
                 (it["version_name"] or "—")[:14], it["condition_grade"],
                 money(it["purchase_price"]),
                 widths=[4, 14, 24, 16, 10, 8])
    print("  " + "─" * (W - 2))
    print(f"  Total spent: {money(total)}   |   Items owned: {len(items)}")


def show_photocards():
    header("MY PHOTOCARDS")
    cards = PhotocardDAO.get_all()
    row_line("ID", "Artist", "Member", "Type", "Dup?", "Trade?", "Value",
             widths=[4, 14, 14, 10, 5, 7, 8])
    print("  " + "─" * (W - 2))
    for pc in cards:
        row_line(pc["photocard_id"], pc["artist_name"], pc["member_name"],
                 pc["card_type"], yn(pc["is_duplicate"]), yn(pc["for_trade"]),
                 money(pc["estimated_value"]),
                 widths=[4, 14, 14, 10, 5, 7, 8])
    trade_cards = PhotocardDAO.get_for_trade()
    print(f"\n  Cards available for trade: {len(trade_cards)}")


def show_wishlist():
    header("WISHLIST  (pending)")
    items = WishlistDAO.get_all(include_acquired=False)
    row_line("ID", "Artist", "Album", "Version", "Priority", "Budget",
             widths=[4, 14, 24, 16, 10, 8])
    print("  " + "─" * (W - 2))
    for w in items:
        row_line(w["wish_id"], w["artist_name"], w["album_title"][:22],
                 (w["version_name"] or "—")[:14], w["priority"],
                 money(w["max_budget"]),
                 widths=[4, 14, 24, 16, 10, 8])


def show_stats():
    header("COLLECTION STATS")
    conn = get_connection()

    total_items  = conn.execute("SELECT COUNT(*) FROM collection_items").fetchone()[0]
    total_spent  = conn.execute("SELECT COALESCE(SUM(purchase_price),0) FROM collection_items").fetchone()[0]
    total_pcs    = conn.execute("SELECT COUNT(*) FROM photocards").fetchone()[0]
    trade_pcs    = conn.execute("SELECT COUNT(*) FROM photocards WHERE for_trade=1").fetchone()[0]
    rare_pcs     = conn.execute("SELECT COUNT(*) FROM photocards WHERE card_type IN ('Rare','POB','Special')").fetchone()[0]
    wish_pending = conn.execute("SELECT COUNT(*) FROM wishlist WHERE is_acquired=0").fetchone()[0]
    pc_value     = conn.execute("SELECT COALESCE(SUM(estimated_value),0) FROM photocards").fetchone()[0]

    print(f"\n  {'Albums owned:':<30} {total_items}")
    print(f"  {'Total spent on albums:':<30} {money(total_spent)}")
    print(f"  {'Photocards collected:':<30} {total_pcs}")
    print(f"  {'Rare/Special/POB cards:':<30} {rare_pcs}")
    print(f"  {'Cards up for trade:':<30} {trade_pcs}")
    print(f"  {'Estimated photocard value:':<30} {money(pc_value)}")
    print(f"  {'Wishlist items remaining:':<30} {wish_pending}")

    subheader("Photocards by Artist")
    rows = conn.execute(
        "SELECT ar.name, COUNT(*) cnt "
        "FROM photocards pc "
        "JOIN collection_items ci ON pc.item_id=ci.item_id "
        "JOIN albums al ON ci.album_id=al.album_id "
        "JOIN artists ar ON al.artist_id=ar.artist_id "
        "GROUP BY ar.name ORDER BY cnt DESC"
    ).fetchall()
    for r in rows:
        bar = "█" * r["cnt"]
        print(f"    {r['name']:<14} {bar} ({r['cnt']})")

    subheader("Wishlist by Priority")
    rows = conn.execute(
        "SELECT priority, COUNT(*) cnt FROM wishlist WHERE is_acquired=0 "
        "GROUP BY priority ORDER BY cnt DESC"
    ).fetchall()
    for r in rows:
        print(f"    {r['priority']:<12} {r['cnt']} items")

    conn.close()


def add_artist_prompt():
    header("ADD NEW ARTIST")
    name   = input("  Artist name: ").strip()
    debut  = input("  Debut year (or Enter to skip): ").strip()
    agency = input("  Agency (or Enter to skip): ").strip()
    fandom = input("  Fandom name (or Enter to skip): ").strip()
    debut  = int(debut) if debut.isdigit() else None
    new_id = ArtistDAO.create(name, debut, agency or None, fandom or None)
    print(f"\n  ✓ Artist '{name}' added with ID {new_id}")


def add_wishlist_prompt():
    header("ADD TO WISHLIST")
    show_all_albums()
    album_id = input("\n  Album ID to add: ").strip()
    version  = input("  Version name (or Enter to skip): ").strip()
    priority = input("  Priority [Low/Medium/High/Must Have] (default: Medium): ").strip() or "Medium"
    budget   = input("  Max budget $ (or Enter to skip): ").strip()
    budget   = float(budget) if budget else None
    new_id   = WishlistDAO.create(int(album_id), version or None, priority, budget)
    print(f"\n  ✓ Wish item added with ID {new_id}")


def mark_wish_acquired_prompt():
    header("MARK WISHLIST ITEM AS ACQUIRED")
    show_wishlist()
    wish_id = input("\n  Wish ID to mark acquired: ").strip()
    WishlistDAO.mark_acquired(int(wish_id))
    print(f"\n  ✓ Wish #{wish_id} marked as acquired!")


# ─────────────────────────────────────────
# Main menu
# ─────────────────────────────────────────

MENU = [
    ("1", "View all artists",               show_all_artists),
    ("2", "View all albums",                show_all_albums),
    ("3", "View my collection",             show_collection),
    ("4", "View my photocards",             show_photocards),
    ("5", "View wishlist",                  show_wishlist),
    ("6", "Collection stats & charts",      show_stats),
    ("7", "Add new artist",                 add_artist_prompt),
    ("8", "Add album to wishlist",          add_wishlist_prompt),
    ("9", "Mark wishlist item acquired",    mark_wish_acquired_prompt),
    ("0", "Exit",                           None),
]


def main():
    init_db()

    # auto-seed if empty
    conn = get_connection()
    cnt = conn.execute("SELECT COUNT(*) FROM artists").fetchone()[0]
    conn.close()
    if cnt == 0:
        print("  First run detected — seeding database…")
        from seed_db import seed
        seed()

    while True:
        header("K-POP COLLECTION MANAGER  ✦  Main Menu")
        for key, label, _ in MENU:
            print(f"    [{key}]  {label}")
        choice = input("\n  Enter choice: ").strip()
        for key, _, fn in MENU:
            if choice == key:
                if fn is None:
                    print("\n  Annyeong! 👋\n")
                    sys.exit(0)
                fn()
                input("\n  Press Enter to continue…")
                break
        else:
            print("  Invalid choice, try again.")


if __name__ == "__main__":
    main()
