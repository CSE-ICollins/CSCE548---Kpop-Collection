-- ============================================================
-- K-POP COLLECTION DATABASE SCHEMA
-- ============================================================

CREATE DATABASE IF NOT EXISTS kpop_collection;
USE kpop_collection;

-- ============================================================
-- TABLE: artists
-- Represents K-pop groups/solo artists
-- ============================================================
CREATE TABLE artists (
    artist_id   INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    debut_year  YEAR,
    agency      VARCHAR(100),
    fandom_name VARCHAR(100),
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_debut_year CHECK (debut_year >= 1990 AND debut_year <= YEAR(CURDATE()))
);

-- ============================================================
-- TABLE: albums
-- Represents physical/digital album releases
-- ============================================================
CREATE TABLE albums (
    album_id      INT AUTO_INCREMENT PRIMARY KEY,
    artist_id     INT NOT NULL,
    title         VARCHAR(200) NOT NULL,
    release_date  DATE NOT NULL,
    album_type    ENUM('Mini Album', 'Full Album', 'Single', 'Repackage', 'Special Album') NOT NULL,
    num_versions  INT NOT NULL DEFAULT 1,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_album_artist FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_num_versions CHECK (num_versions >= 1)
);

-- ============================================================
-- TABLE: collection_items
-- Represents physical copies owned by the collector
-- ============================================================
CREATE TABLE collection_items (
    item_id        INT AUTO_INCREMENT PRIMARY KEY,
    album_id       INT NOT NULL,
    version_name   VARCHAR(100),
    condition_grade ENUM('Mint', 'Near Mint', 'Very Good', 'Good', 'Fair') NOT NULL DEFAULT 'Mint',
    purchase_price DECIMAL(8,2),
    purchase_date  DATE,
    purchase_source VARCHAR(100),
    notes          TEXT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_item_album FOREIGN KEY (album_id) REFERENCES albums(album_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_purchase_price CHECK (purchase_price IS NULL OR purchase_price >= 0)
);

-- ============================================================
-- TABLE: photocards
-- Represents individual photocards pulled from albums
-- ============================================================
CREATE TABLE photocards (
    photocard_id   INT AUTO_INCREMENT PRIMARY KEY,
    item_id        INT NOT NULL,
    member_name    VARCHAR(100) NOT NULL,
    card_type      ENUM('Standard', 'Rare', 'Unit', 'Special', 'POB') NOT NULL DEFAULT 'Standard',
    is_duplicate   BOOLEAN NOT NULL DEFAULT FALSE,
    for_trade      BOOLEAN NOT NULL DEFAULT FALSE,
    estimated_value DECIMAL(8,2),
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pc_item FOREIGN KEY (item_id) REFERENCES collection_items(item_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_pc_value CHECK (estimated_value IS NULL OR estimated_value >= 0)
);

-- ============================================================
-- TABLE: wishlist
-- Albums or items the collector wants to acquire
-- ============================================================
CREATE TABLE wishlist (
    wish_id        INT AUTO_INCREMENT PRIMARY KEY,
    album_id       INT NOT NULL,
    version_name   VARCHAR(100),
    priority       ENUM('Low', 'Medium', 'High', 'Must Have') NOT NULL DEFAULT 'Medium',
    max_budget     DECIMAL(8,2),
    notes          TEXT,
    is_acquired    BOOLEAN NOT NULL DEFAULT FALSE,
    added_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_wish_album FOREIGN KEY (album_id) REFERENCES albums(album_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_budget CHECK (max_budget IS NULL OR max_budget >= 0)
);

-- ============================================================
-- INDEXES for performance
-- ============================================================
CREATE INDEX idx_albums_artist ON albums(artist_id);
CREATE INDEX idx_items_album ON collection_items(album_id);
CREATE INDEX idx_pc_item ON photocards(item_id);
CREATE INDEX idx_pc_member ON photocards(member_name);
CREATE INDEX idx_wishlist_album ON wishlist(album_id);
CREATE INDEX idx_wishlist_acquired ON wishlist(is_acquired);
