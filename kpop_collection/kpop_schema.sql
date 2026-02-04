-- kpop_schema.sql
-- Database schema for K-pop album collection tracking

CREATE TABLE artists (
  artist_id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE albums (
  album_id SERIAL PRIMARY KEY,
  artist_id INT NOT NULL REFERENCES artists(artist_id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  release_date DATE,
  main_genre TEXT,
  notes TEXT
);

CREATE TABLE editions (
  edition_id SERIAL PRIMARY KEY,
  album_id INT NOT NULL REFERENCES albums(album_id) ON DELETE CASCADE,
  edition_name TEXT NOT NULL,
  format TEXT,
  release_year INT
);

CREATE TABLE inclusions (
  inclusion_id SERIAL PRIMARY KEY,
  edition_id INT NOT NULL REFERENCES editions(edition_id) ON DELETE CASCADE,
  item_type TEXT NOT NULL,
  qty INT DEFAULT 1 CHECK (qty >= 0),
  notes TEXT
);

CREATE TABLE collection (
  collection_id SERIAL PRIMARY KEY,
  edition_id INT NOT NULL REFERENCES editions(edition_id) ON DELETE CASCADE,
  acquired_date DATE DEFAULT CURRENT_DATE,
  owned BOOLEAN DEFAULT TRUE,
  condition_text TEXT,
  count INT DEFAULT 1 CHECK (count >= 0),
  personal_notes TEXT
);
