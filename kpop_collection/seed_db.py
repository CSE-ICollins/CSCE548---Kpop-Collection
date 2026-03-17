"""
seed_db.py  –  Populate the K-Pop collection database with sample data.
Run this ONCE after init_db() to get the full 50+ row dataset.
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from data_access import (
    init_db,
    ArtistDAO, AlbumDAO, CollectionItemDAO, PhotocardDAO, WishlistDAO
)


def seed():
    init_db()

    # ── ARTISTS ──────────────────────────────────────────────────
    a = {}
    a["BTS"]       = ArtistDAO.create("BTS",       2013, "HYBE",             "ARMY")
    a["BLACKPINK"] = ArtistDAO.create("BLACKPINK", 2016, "YG Entertainment", "BLINK")
    a["EXO"]       = ArtistDAO.create("EXO",       2012, "SM Entertainment", "EXO-L")
    a["TWICE"]     = ArtistDAO.create("TWICE",     2015, "JYP Entertainment","ONCE")
    a["SKZ"]       = ArtistDAO.create("Stray Kids",2018, "JYP Entertainment","STAY")
    a["aespa"]     = ArtistDAO.create("aespa",     2020, "SM Entertainment", "MY")
    a["NJ"]        = ArtistDAO.create("NewJeans",  2022, "ADOR/HYBE",        "Bunnies")
    a["SVT"]       = ArtistDAO.create("SEVENTEEN", 2015, "PLEDIS/HYBE",      "Carat")

    # ── ALBUMS ───────────────────────────────────────────────────
    al = {}
    al["persona"]  = AlbumDAO.create(a["BTS"],       "Map of the Soul: Persona", "2019-04-12", "Mini Album",   4)
    al["be"]       = AlbumDAO.create(a["BTS"],       "BE",                       "2020-11-20", "Full Album",   2)
    al["proof"]    = AlbumDAO.create(a["BTS"],       "Proof",                    "2022-06-10", "Full Album",   3)
    al["the_alb"]  = AlbumDAO.create(a["BLACKPINK"], "THE ALBUM",                "2020-10-02", "Full Album",   4)
    al["bornpink"] = AlbumDAO.create(a["BLACKPINK"], "Born Pink",                "2022-09-16", "Full Album",   2)
    al["exist"]    = AlbumDAO.create(a["EXO"],       "EXIST",                    "2023-07-10", "Full Album",   5)
    al["formula"]  = AlbumDAO.create(a["TWICE"],     "Formula of Love",          "2021-11-12", "Full Album",   3)
    al["rtb"]      = AlbumDAO.create(a["TWICE"],     "READY TO BE",              "2023-03-10", "Mini Album",   4)
    al["odd"]      = AlbumDAO.create(a["SKZ"],       "ODDINARY",                 "2022-03-18", "Mini Album",   3)
    al["maxi"]     = AlbumDAO.create(a["SKZ"],       "MAXIDENT",                 "2022-10-07", "Mini Album",   2)
    al["myworld"]  = AlbumDAO.create(a["aespa"],     "MY WORLD",                 "2023-05-08", "Mini Album",   3)
    al["getup"]    = AlbumDAO.create(a["NJ"],        "Get Up",                   "2023-07-21", "Mini Album",   2)

    # ── COLLECTION ITEMS ─────────────────────────────────────────
    it = {}
    it["p_v1"]    = CollectionItemDAO.create(al["persona"],  "Ver. 1",           "Mint",      22.99, "2023-01-15", "Weverse Shop",  "Sealed")
    it["p_v3"]    = CollectionItemDAO.create(al["persona"],  "Ver. 3",           "Near Mint", 18.50, "2023-03-02", "eBay",          "Minor corner dent")
    it["p_v4"]    = CollectionItemDAO.create(al["persona"],  "Ver. 4",           "Mint",      24.00, "2023-05-10", "Weverse Shop",  None)
    it["be_ess"]  = CollectionItemDAO.create(al["be"],       "Essential Edition","Mint",      27.99, "2022-11-20", "Ktown4u",       "Holiday gift")
    it["pf_std"]  = CollectionItemDAO.create(al["proof"],    "Standard Edition", "Mint",      35.00, "2022-06-12", "Weverse Shop",  "Pre-ordered")
    it["pf_col"]  = CollectionItemDAO.create(al["proof"],    "Collector Edition","Mint",      65.00, "2022-06-12", "Weverse Shop",  "Includes extra disc")
    it["ta_jen"]  = CollectionItemDAO.create(al["the_alb"],  "Ver. 1 (Jennie)", "Mint",      19.99, "2021-08-14", "Amazon",        None)
    it["ta_jis"]  = CollectionItemDAO.create(al["the_alb"],  "Ver. 2 (Jisoo)",  "Near Mint", 17.50, "2021-09-01", "eBay",          "Small scuff")
    it["bp_std"]  = CollectionItemDAO.create(al["bornpink"], "Standard",         "Mint",      21.99, "2022-09-20", "YG Select",     None)
    it["tw_set"]  = CollectionItemDAO.create(al["formula"],  "Set",              "Mint",      30.00, "2021-12-01", "JYP Shop",      "Full set of 3")
    it["rtb_r"]   = CollectionItemDAO.create(al["rtb"],      "READY",            "Mint",      18.99, "2023-03-15", "Ktown4u",       None)
    it["odd_mor"] = CollectionItemDAO.create(al["odd"],      "Morass",           "Near Mint", 16.50, "2022-04-10", "eBay",          None)
    it["odd_std"] = CollectionItemDAO.create(al["odd"],      "Standard",         "Mint",      19.99, "2022-04-01", "Weverse Shop",  None)
    it["maxi_s"]  = CollectionItemDAO.create(al["maxi"],     "Standard",         "Mint",      21.00, "2022-10-10", "Weverse Shop",  None)
    it["ae_rw"]   = CollectionItemDAO.create(al["myworld"],  "Real World Ver.",  "Mint",      22.99, "2023-05-15", "SM Store",      None)
    it["nj_bb"]   = CollectionItemDAO.create(al["getup"],    "Bluebook",         "Mint",      17.99, "2023-08-01", "Ktown4u",       "First NJ purchase!")

    # ── PHOTOCARDS ───────────────────────────────────────────────
    PhotocardDAO.create(it["p_v1"],    "Jimin",     "Standard", False, False, 12.00)
    PhotocardDAO.create(it["p_v1"],    "V",         "Standard", False, False, 15.00)
    PhotocardDAO.create(it["p_v3"],    "Jungkook",  "Standard", False, False, 18.00)
    PhotocardDAO.create(it["p_v3"],    "RM",        "Standard", True,  True,   8.00)
    PhotocardDAO.create(it["p_v4"],    "Jin",       "Standard", False, False, 10.00)
    PhotocardDAO.create(it["p_v4"],    "SUGA",      "Standard", False, False, 14.00)
    PhotocardDAO.create(it["be_ess"],  "j-hope",    "Rare",     False, False, 25.00)
    PhotocardDAO.create(it["be_ess"],  "Jimin",     "Standard", True,  True,   9.00)
    PhotocardDAO.create(it["pf_std"],  "V",         "Special",  False, False, 30.00)
    PhotocardDAO.create(it["pf_std"],  "Jungkook",  "Rare",     False, False, 28.00)
    PhotocardDAO.create(it["ta_jen"],  "Jennie",    "POB",      False, False, 45.00)
    PhotocardDAO.create(it["ta_jen"],  "Lisa",      "Standard", False, False, 16.00)
    PhotocardDAO.create(it["bp_std"],  "Rosé",      "Unit",     False, False, 20.00)
    PhotocardDAO.create(it["bp_std"],  "Jisoo",     "Standard", False, False, 13.00)
    PhotocardDAO.create(it["rtb_r"],   "Nayeon",    "Standard", False, False,  8.00)
    PhotocardDAO.create(it["rtb_r"],   "Tzuyu",     "Rare",     False, False, 22.00)
    PhotocardDAO.create(it["maxi_s"],  "Felix",     "POB",      False, False, 40.00)
    PhotocardDAO.create(it["maxi_s"],  "Han",       "Standard", True,  True,   7.00)

    # ── WISHLIST ─────────────────────────────────────────────────
    WishlistDAO.create(al["persona"],  "Ver. 2",         "High",      25.00, "Complete the set")
    WishlistDAO.create(al["proof"],    "Weverse Edition","Must Have", 80.00, "Exclusive photocards")
    WishlistDAO.create(al["the_alb"],  "Ver. 3 (Rosé)",  "Medium",    20.00, None)
    WishlistDAO.create(al["the_alb"],  "Ver. 4 (Lisa)",  "Medium",    20.00, None)
    WishlistDAO.create(al["exist"],    "Digipack Ver.",  "High",      40.00, "EXO fan goal 2024")
    WishlistDAO.create(al["rtb"],      "TO BE",          "Medium",    20.00, None)
    WishlistDAO.create(al["odd"],      "Halazia",        "Low",       18.00, None)
    WishlistDAO.create(al["myworld"],  "MY Ver.",        "High",      25.00, "Want all 3 versions")
    WishlistDAO.create(al["getup"],    "Woodbook",       "Must Have", 20.00, "Complete the Get Up set")
    WishlistDAO.create(al["bornpink"], "Limited Box",    "Low",       60.00, "Watch Mercari for drop")

    # Print row counts
    from data_access import get_connection
    conn = get_connection()
    for tbl in ("artists","albums","collection_items","photocards","wishlist"):
        cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"  {tbl:20s} → {cnt:3d} rows")
    total = conn.execute(
        "SELECT SUM(c) FROM ("
        "  SELECT COUNT(*) c FROM artists UNION ALL"
        "  SELECT COUNT(*) FROM albums UNION ALL"
        "  SELECT COUNT(*) FROM collection_items UNION ALL"
        "  SELECT COUNT(*) FROM photocards UNION ALL"
        "  SELECT COUNT(*) FROM wishlist)"
    ).fetchone()[0]
    conn.close()
    print(f"\n  TOTAL ROWS: {total}")


if __name__ == "__main__":
    print("Seeding K-Pop Collection database...")
    seed()
    print("Done! ✓")
