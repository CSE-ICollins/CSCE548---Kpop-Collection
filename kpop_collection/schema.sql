-- ============================================================
-- K-POP COLLECTION DATABASE SCHEMA
-- Author: Generated for CSCE Project
-- Description: Tracks K-pop albums, artists, groups, photocards,
--              and wishlists for a personal collector.
-- ============================================================

PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------
-- TABLE: artists
-- Individual K-pop idols/solo artists
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS artists (
    artist_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    stage_name   TEXT    NOT NULL,
    real_name    TEXT,
    birthdate    TEXT,                        -- ISO 8601 YYYY-MM-DD
    nationality  TEXT    NOT NULL DEFAULT 'South Korean',
    gender       TEXT    CHECK (gender IN ('Male', 'Female', 'Non-binary')),
    active       INTEGER NOT NULL DEFAULT 1   CHECK (active IN (0, 1)),
    debut_year   INTEGER CHECK (debut_year >= 1990 AND debut_year <= 2100),
    notes        TEXT,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- TABLE: groups
-- K-pop groups / solo acts as a unit
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS groups (
    group_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name   TEXT    NOT NULL UNIQUE,
    agency       TEXT,
    debut_date   TEXT,                        -- ISO 8601
    fandom_name  TEXT,
    active       INTEGER NOT NULL DEFAULT 1   CHECK (active IN (0, 1)),
    gender_type  TEXT    CHECK (gender_type IN ('Boy Group', 'Girl Group', 'Co-ed', 'Solo')),
    notes        TEXT,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- TABLE: group_members  (junction: artists <-> groups)
-- Supports sub-units & solo acts; an artist may belong to many groups
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS group_members (
    member_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    artist_id    INTEGER NOT NULL REFERENCES artists(artist_id) ON DELETE CASCADE,
    group_id     INTEGER NOT NULL REFERENCES groups(group_id)   ON DELETE CASCADE,
    position     TEXT,                        -- e.g. 'Leader', 'Main Vocalist'
    join_date    TEXT,
    leave_date   TEXT,                        -- NULL means still active
    UNIQUE (artist_id, group_id)
);

-- ------------------------------------------------------------
-- TABLE: albums
-- Physical or digital album releases
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS albums (
    album_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id       INTEGER NOT NULL REFERENCES groups(group_id) ON DELETE RESTRICT,
    title          TEXT    NOT NULL,
    album_type     TEXT    NOT NULL CHECK (album_type IN (
                       'Mini Album', 'Full Album', 'Single Album',
                       'Repackage', 'Special Album', 'OST', 'Collaboration')),
    release_date   TEXT,
    version_name   TEXT,                      -- e.g. 'Digipack', 'Jewel Case', 'Poca'
    track_count    INTEGER CHECK (track_count > 0),
    duration_mins  REAL    CHECK (duration_mins > 0),
    label          TEXT,
    is_limited     INTEGER NOT NULL DEFAULT 0 CHECK (is_limited IN (0, 1)),
    notes          TEXT,
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- TABLE: collection_items
-- User's owned physical albums / copies
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS collection_items (
    item_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    album_id       INTEGER NOT NULL REFERENCES albums(album_id) ON DELETE RESTRICT,
    condition      TEXT    NOT NULL DEFAULT 'Mint'
                           CHECK (condition IN ('Mint', 'Near Mint', 'Very Good', 'Good', 'Fair', 'Poor')),
    purchase_date  TEXT,
    purchase_price REAL    CHECK (purchase_price >= 0),
    purchase_from  TEXT,                      -- e.g. 'Weverse Shop', 'Ebay', 'KTOWN4U'
    is_sealed      INTEGER NOT NULL DEFAULT 0 CHECK (is_sealed IN (0, 1)),
    has_poster     INTEGER NOT NULL DEFAULT 0 CHECK (has_poster IN (0, 1)),
    has_cd         INTEGER NOT NULL DEFAULT 1 CHECK (has_cd IN (0, 1)),
    inclusions     TEXT,                      -- comma-separated extras
    notes          TEXT,
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- TABLE: photocards
-- Individual photocards that come with albums
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS photocards (
    photocard_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id        INTEGER NOT NULL REFERENCES collection_items(item_id) ON DELETE CASCADE,
    artist_id      INTEGER NOT NULL REFERENCES artists(artist_id) ON DELETE RESTRICT,
    album_id       INTEGER NOT NULL REFERENCES albums(album_id) ON DELETE RESTRICT,
    card_type      TEXT    NOT NULL DEFAULT 'Standard'
                           CHECK (card_type IN ('Standard', 'Unit', 'Solo', 'Special', 'Lucky Draw', 'POB', 'Pre-order')),
    condition      TEXT    NOT NULL DEFAULT 'Mint'
                           CHECK (condition IN ('Mint', 'Near Mint', 'Very Good', 'Good', 'Fair', 'Poor')),
    acquired_date  TEXT,
    acquired_from  TEXT,
    estimated_value REAL   CHECK (estimated_value >= 0),
    is_duplicate   INTEGER NOT NULL DEFAULT 0 CHECK (is_duplicate IN (0, 1)),
    for_trade      INTEGER NOT NULL DEFAULT 0 CHECK (for_trade IN (0, 1)),
    notes          TEXT,
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- TABLE: wishlist
-- Albums / photocards the user wants to acquire
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS wishlist (
    wish_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    item_type      TEXT    NOT NULL CHECK (item_type IN ('Album', 'Photocard', 'Merch')),
    album_id       INTEGER REFERENCES albums(album_id) ON DELETE SET NULL,
    artist_id      INTEGER REFERENCES artists(artist_id) ON DELETE SET NULL,
    description    TEXT    NOT NULL,
    max_budget     REAL    CHECK (max_budget >= 0),
    priority       INTEGER NOT NULL DEFAULT 3
                           CHECK (priority BETWEEN 1 AND 5),  -- 1=highest, 5=lowest
    acquired       INTEGER NOT NULL DEFAULT 0 CHECK (acquired IN (0, 1)),
    notes          TEXT,
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================
-- INDEXES for performance
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_albums_group      ON albums(group_id);
CREATE INDEX IF NOT EXISTS idx_members_artist    ON group_members(artist_id);
CREATE INDEX IF NOT EXISTS idx_members_group     ON group_members(group_id);
CREATE INDEX IF NOT EXISTS idx_items_album       ON collection_items(album_id);
CREATE INDEX IF NOT EXISTS idx_photocards_artist ON photocards(artist_id);
CREATE INDEX IF NOT EXISTS idx_photocards_item   ON photocards(item_id);
CREATE INDEX IF NOT EXISTS idx_wishlist_album    ON wishlist(album_id);