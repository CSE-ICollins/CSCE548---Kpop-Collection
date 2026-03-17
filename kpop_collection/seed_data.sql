-- ============================================================
-- K-POP COLLECTION - SEED DATA
-- 50+ rows across all tables
-- ============================================================

PRAGMA foreign_keys = ON;

-- ============================================================
-- GROUPS (12 rows)
-- ============================================================
INSERT INTO groups (group_name, agency, debut_date, fandom_name, active, gender_type) VALUES
('BTS',              'HYBE',              '2013-06-13', 'ARMY',      1, 'Boy Group'),
('BLACKPINK',        'YG Entertainment', '2016-08-08', 'Blink',     1, 'Girl Group'),
('TWICE',            'JYP Entertainment','2015-10-20', 'Once',      1, 'Girl Group'),
('EXO',              'SM Entertainment', '2012-04-08', 'EXO-L',     1, 'Boy Group'),
('aespa',            'SM Entertainment', '2020-11-17', 'MY',        1, 'Girl Group'),
('Stray Kids',       'JYP Entertainment','2018-03-25', 'STAY',      1, 'Boy Group'),
('IVE',              'Starship',         '2021-12-01', 'Dive',      1, 'Girl Group'),
('NewJeans',         'ADOR/HYBE',         '2022-08-01', 'Bunnies',  1, 'Girl Group'),
('TXT',              'HYBE',              '2019-03-04', 'MOA',       1, 'Boy Group'),
('ITZY',             'JYP Entertainment','2019-02-12', 'MIDZY',     1, 'Girl Group'),
('Red Velvet',       'SM Entertainment', '2014-08-01', 'ReVeluv',   1, 'Girl Group'),
('SHINee',           'SM Entertainment', '2008-05-22', 'Shawol',    1, 'Boy Group');

-- ============================================================
-- ARTISTS (20 rows)
-- ============================================================
INSERT INTO artists (stage_name, real_name, birthdate, nationality, gender, debut_year) VALUES
-- BTS
('RM',       'Kim Namjoon',  '1994-09-12', 'South Korean', 'Male', 2013),
('Jin',      'Kim Seokjin',  '1992-12-04', 'South Korean', 'Male', 2013),
('Suga',     'Min Yoongi',   '1993-03-09', 'South Korean', 'Male', 2013),
('J-Hope',   'Jung Hoseok',  '1994-02-18', 'South Korean', 'Male', 2013),
('Jimin',    'Park Jimin',   '1995-10-13', 'South Korean', 'Male', 2013),
('V',        'Kim Taehyung', '1995-12-30', 'South Korean', 'Male', 2013),
('Jungkook', 'Jeon Jungkook','1997-09-01', 'South Korean', 'Male', 2013),
-- BLACKPINK
('Jisoo',    'Kim Jisoo',    '1995-01-03', 'South Korean', 'Female', 2016),
('Jennie',   'Jennie Kim',   '1996-01-16', 'South Korean', 'Female', 2016),
('Rosé',     'Park Chaeyoung','1997-02-11','South Korean', 'Female', 2016),
('Lisa',     'Lalisa Manoban','1997-03-27','Thai',          'Female', 2016),
-- TWICE
('Nayeon',   'Im Na-yeon',   '1995-09-22', 'South Korean', 'Female', 2015),
('Jihyo',    'Park Ji-hyo',  '1997-02-01', 'South Korean', 'Female', 2015),
('Sana',     'Minatozaki Sana','1996-12-29','Japanese',    'Female', 2015),
-- aespa
('Karina',   'Yoo Ji-min',   '2000-04-11', 'South Korean', 'Female', 2020),
('Winter',   'Kim Min-jeong', '2001-01-01', 'South Korean', 'Female', 2020),
('NingNing', 'Ning Yi-zhuo', '2002-10-23', 'Chinese',      'Female', 2020),
-- IVE
('Wonyoung', 'Jang Won-young','2004-08-31', 'South Korean', 'Female', 2021),
('Yujin',    'An Yu-jin',    '2003-09-01', 'South Korean', 'Female', 2021),
-- NewJeans
('Hanni',    'Pham Ngoc Han', '2004-10-06', 'Vietnamese-Australian','Female', 2022);

-- ============================================================
-- GROUP_MEMBERS (20 rows)
-- ============================================================
INSERT INTO group_members (artist_id, group_id, position) VALUES
-- BTS (group_id=1)
(1,  1, 'Leader, Main Rapper'),
(2,  1, 'Vocalist'),
(3,  1, 'Lead Rapper'),
(4,  1, 'Main Dancer, Sub Rapper'),
(5,  1, 'Main Dancer, Lead Vocalist'),
(6,  1, 'Vocalist, Visual'),
(7,  1, 'Main Vocalist, Maknae'),
-- BLACKPINK (group_id=2)
(8,  2, 'Visual, Sub Vocalist'),
(9,  2, 'Main Rapper, Sub Vocalist'),
(10, 2, 'Main Vocalist'),
(11, 2, 'Main Dancer, Lead Rapper'),
-- TWICE (group_id=3)
(12, 3, 'Center, Lead Vocalist'),
(13, 3, 'Leader, Main Vocalist'),
(14, 3, 'Sub Vocalist'),
-- aespa (group_id=5)
(15, 5, 'Leader, Main Dancer'),
(16, 5, 'Main Vocalist'),
(17, 5, 'Main Vocalist, Maknae'),
-- IVE (group_id=7)
(18, 7, 'Center, Visual'),
(19, 7, 'Leader, Main Vocalist'),
-- NewJeans (group_id=8)
(20, 8, 'Vocalist');

-- ============================================================
-- ALBUMS (14 rows)
-- ============================================================
INSERT INTO albums (group_id, title, album_type, release_date, version_name, track_count, duration_mins, label, is_limited) VALUES
(1,  'LOVE YOURSELF 轉 Tear',     'Full Album',   '2018-05-18', 'L Version',      11, 45.2, 'Big Hit',        0),
(1,  'MAP OF THE SOUL: 7',        'Full Album',   '2020-02-21', 'Concept Version', 20, 74.8, 'Big Hit',       0),
(1,  'Proof',                     'Special Album','2022-06-10', 'Compact Edition',  48, 148.0,'HYBE',          0),
(2,  'THE ALBUM',                 'Full Album',   '2020-10-02', 'Standard',         8, 24.5, 'YG',            0),
(2,  'BORN PINK',                 'Full Album',   '2022-09-16', 'Digipack',         8, 22.3, 'YG',            0),
(3,  'MORE & MORE',               'Mini Album',   '2020-06-01', 'Standard',         6, 18.1, 'JYP',           0),
(3,  'BETWEEN 1&2',               'Mini Album',   '2022-08-26', 'Standard',         6, 17.9, 'JYP',           0),
(5,  'SAVAGE',                    'Mini Album',   '2021-10-05', 'Drama Version',    6, 20.3, 'SM',            0),
(5,  'MY WORLD',                  'Mini Album',   '2023-05-08', 'Standard',         5, 17.1, 'SM',            0),
(6,  'ODDINARY',                  'Mini Album',   '2022-03-18', 'Standard',         7, 21.4, 'JYP',           0),
(7,  'IVE MINE',                  'Mini Album',   '2023-10-13', 'Standard',         5, 15.3, 'Starship',      0),
(8,  'Get Up',                    'Mini Album',   '2023-07-21', 'Bunny Beach Box',  6, 19.8, 'ADOR',          1),
(9,  'The Name Chapter: TEMPTATION','Mini Album', '2023-01-27', 'Farewell Version', 5, 18.6, 'HYBE',          0),
(11, 'The ReVe Festival 2022',    'Mini Album',   '2022-09-19', 'Birthday Version', 5, 16.4, 'SM',            0);

-- ============================================================
-- COLLECTION_ITEMS (18 rows — user's owned copies)
-- ============================================================
INSERT INTO collection_items (album_id, condition, purchase_date, purchase_price, purchase_from, is_sealed, has_poster, inclusions) VALUES
(1,  'Mint',      '2023-01-15', 35.00, 'Weverse Shop',   0, 1, 'Photocard, Mini Book, Sticker'),
(2,  'Mint',      '2023-02-20', 42.00, 'KTOWN4U',        0, 1, 'Photocard, Bookmark, Mini Poster'),
(3,  'Mint',      '2022-06-15', 55.00, 'Weverse Shop',   0, 1, 'Photocard, ID Card, Lyric Book'),
(4,  'Near Mint', '2022-11-01', 30.00, 'Ebay',           0, 0, 'Photocard'),
(5,  'Mint',      '2022-09-20', 28.00, 'Weverse Shop',   0, 1, 'Photocard, PostCard'),
(6,  'Very Good', '2021-05-10', 18.00, 'Amazon',         0, 0, 'Photocard'),
(7,  'Mint',      '2022-09-01', 22.00, 'KTOWN4U',        0, 1, 'Photocard, PostCard'),
(8,  'Mint',      '2022-01-10', 25.00, 'Weverse Shop',   0, 1, 'Photocard, Mini Poster, Sticker'),
(9,  'Mint',      '2023-05-15', 24.00, 'SM Store',       1, 0, 'Photocard, Unit Card'),
(10, 'Mint',      '2022-04-01', 20.00, 'JYP Shop',       0, 1, 'Photocard, Film'),
(11, 'Near Mint', '2023-10-20', 22.00, 'Weverse Shop',   0, 0, 'Photocard'),
(12, 'Mint',      '2023-07-25', 48.00, 'ADOR Shop',      1, 1, 'Photocard Set, Postcard, Sticker Sheet'),
(13, 'Mint',      '2023-02-01', 26.00, 'HYBE Shop',      0, 1, 'Photocard, Lyric Card'),
(14, 'Mint',      '2022-09-25', 21.00, 'Weverse Shop',   0, 0, 'Photocard'),
(1,  'Near Mint', '2021-06-01', 28.00, 'Carousell',      0, 0, 'Photocard (Jimin)'),
(2,  'Mint',      '2023-03-10', 45.00, 'KTOWN4U',        0, 1, 'Photocard, Mini Book'),
(4,  'Good',      '2023-04-05', 22.00, 'Mercari',        0, 0, 'Photocard (Lisa)'),
(5,  'Mint',      '2023-01-01', 30.00, 'Weverse Shop',   1, 1, 'Photocard, PostCard');

-- ============================================================
-- PHOTOCARDS (20 rows)
-- ============================================================
INSERT INTO photocards (item_id, artist_id, album_id, card_type, condition, acquired_date, acquired_from, estimated_value, is_duplicate, for_trade) VALUES
(1,  5,  1,  'Standard',    'Mint',      '2023-01-15', 'Pulled from album', 15.00, 0, 0),
(1,  7,  1,  'Standard',    'Mint',      '2023-01-15', 'Pulled from album', 25.00, 0, 0),
(2,  1,  2,  'Standard',    'Mint',      '2023-02-20', 'Pulled from album', 20.00, 0, 0),
(2,  6,  2,  'Standard',    'Near Mint', '2023-02-20', 'Pulled from album', 30.00, 0, 0),
(3,  4,  3,  'Special',     'Mint',      '2022-06-15', 'Pulled from album', 18.00, 0, 0),
(4,  10, 4,  'Standard',    'Near Mint', '2022-11-01', 'Pulled from album', 22.00, 0, 0),
(5,  9,  5,  'Standard',    'Mint',      '2022-09-20', 'Pulled from album', 19.00, 0, 0),
(5,  11, 5,  'Standard',    'Mint',      '2022-09-20', 'Pulled from album', 35.00, 0, 0),
(6,  13, 6,  'Standard',    'Very Good', '2021-05-10', 'Pulled from album',  8.00, 0, 0),
(7,  12, 7,  'Standard',    'Mint',      '2022-09-01', 'Pulled from album', 12.00, 0, 0),
(8,  15, 8,  'Standard',    'Mint',      '2022-01-10', 'Pulled from album', 20.00, 0, 0),
(8,  16, 8,  'Special',     'Mint',      '2022-01-10', 'Pulled from album', 18.00, 0, 0),
(9,  15, 9,  'Standard',    'Mint',      '2023-05-15', 'Pulled from album', 15.00, 0, 0),
(10, 6,  10, 'Standard',    'Mint',      '2022-04-01', 'Pulled from album', 22.00, 0, 0),
(11, 18, 11, 'Standard',    'Near Mint', '2023-10-20', 'Pulled from album', 17.00, 0, 0),
(12, 20, 12, 'Pre-order',   'Mint',      '2023-07-25', 'Pulled from album', 45.00, 0, 0),
(13, 9,  13, 'Standard',    'Mint',      '2023-02-01', 'Pulled from album', 12.00, 0, 0),
(15, 5,  1,  'Standard',    'Near Mint', '2021-06-01', 'Carousell trade',   18.00, 1, 1),
(17, 11, 4,  'Standard',    'Good',      '2023-04-05', 'Mercari',           28.00, 0, 0),
(18, 8,  5,  'Standard',    'Mint',      '2023-01-01', 'Pulled from album', 16.00, 0, 0);

-- ============================================================
-- WISHLIST (10 rows)
-- ============================================================
INSERT INTO wishlist (item_type, album_id, artist_id, description, max_budget, priority, acquired) VALUES
('Album',     3,    NULL, 'BTS Proof - Anthology Box version',         200.00, 1, 0),
('Photocard', NULL, 1,    'RM MAP OF THE SOUL: PERSONA photocard',      40.00, 2, 0),
('Album',     NULL, NULL, 'BLACKPINK 2NE1 collab (if released)',        60.00, 5, 0),
('Photocard', NULL, 20,   'Hanni Get Up POB photocard',                 55.00, 1, 0),
('Album',     12,   NULL, 'NewJeans Get Up - Bluebook version',         50.00, 2, 0),
('Merch',     NULL, 6,    'V Layover vinyl LP signed',                 150.00, 1, 0),
('Photocard', NULL, 11,   'Lisa Solo debut photocard set',              35.00, 3, 0),
('Album',     NULL, NULL, 'aespa Drama mini album (upcoming)',           30.00, 2, 0),
('Photocard', NULL, 18,   'Wonyoung IVE MINE lucky draw card',          80.00, 1, 0),
('Album',     10,   NULL, 'Stray Kids ODDINARY - limited signed',      120.00, 3, 0);