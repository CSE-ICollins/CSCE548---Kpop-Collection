-- kpop_seed.sql
-- Sample data for K-pop album collection

INSERT INTO artists (name) VALUES
('BTS'),
('BLACKPINK'),
('TWICE'),
('SEVENTEEN'),
('ATEEZ'),
('Stray Kids'),
('NCT 127'),
('Red Velvet'),
('IU'),
('(G)I-DLE');

INSERT INTO albums (artist_id, title, release_date, main_genre, notes)
SELECT
  1 + ((g - 1) % 10),
  'Album ' || g,
  date '2019-01-01' + (g * 20),
  'K-pop',
  'Sample album'
FROM generate_series(1,25) AS g;

INSERT INTO editions (album_id, edition_name, format, release_year)
SELECT
  album_id,
  CASE
    WHEN album_id % 3 = 0 THEN 'Limited'
    WHEN album_id % 3 = 1 THEN 'Version A'
    ELSE 'Version B'
  END,
  'CD',
  2019 + (album_id % 5)
FROM albums;

INSERT INTO inclusions (edition_id, item_type, qty)
SELECT edition_id, 'Photocard', 1 FROM editions WHERE edition_id % 2 = 0;

INSERT INTO inclusions (edition_id, item_type, qty)
SELECT edition_id, 'Poster', 1 FROM editions WHERE edition_id % 3 = 0;

INSERT INTO inclusions (edition_id, item_type, qty)
SELECT edition_id, 'Lyric Book', 1 FROM editions;

INSERT INTO collection (edition_id, condition_text, count, personal_notes)
SELECT
  edition_id,
  'Opened - like new',
  1,
  'Sample owned copy'
FROM editions
LIMIT 25;
