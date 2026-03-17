-- ============================================================
-- K-POP COLLECTION SEED DATA  (50+ rows total)
-- ============================================================

USE kpop_collection;

-- ============================================================
-- ARTISTS (8 rows)
-- ============================================================
INSERT INTO artists (name, debut_year, agency, fandom_name, is_active) VALUES
('BTS',           2013, 'HYBE',            'ARMY',         TRUE),
('BLACKPINK',     2016, 'YG Entertainment','BLINK',        TRUE),
('EXO',           2012, 'SM Entertainment','EXO-L',        TRUE),
('TWICE',         2015, 'JYP Entertainment','ONCE',        TRUE),
('Stray Kids',    2018, 'JYP Entertainment','STAY',        TRUE),
('aespa',         2020, 'SM Entertainment','MY',           TRUE),
('NewJeans',      2022, 'ADOR/HYBE',       'Bunnies',      TRUE),
('SEVENTEEN',     2015, 'PLEDIS/HYBE',     'Carat',        TRUE);

-- ============================================================
-- ALBUMS (12 rows)
-- ============================================================
INSERT INTO albums (artist_id, title, release_date, album_type, num_versions) VALUES
-- BTS
(1, 'Map of the Soul: Persona',   '2019-04-12', 'Mini Album',   4),
(1, 'BE',                          '2020-11-20', 'Full Album',   2),
(1, 'Proof',                       '2022-06-10', 'Full Album',   3),
-- BLACKPINK
(2, 'THE ALBUM',                   '2020-10-02', 'Full Album',   4),
(2, 'Born Pink',                   '2022-09-16', 'Full Album',   2),
-- EXO
(3, 'EXIST',                       '2023-07-10', 'Full Album',   5),
-- TWICE
(4, 'Formula of Love',             '2021-11-12', 'Full Album',   3),
(4, 'READY TO BE',                 '2023-03-10', 'Mini Album',   4),
-- Stray Kids
(5, 'ODDINARY',                    '2022-03-18', 'Mini Album',   3),
(5, 'MAXIDENT',                    '2022-10-07', 'Mini Album',   2),
-- aespa
(6, 'MY WORLD',                    '2023-05-08', 'Mini Album',   3),
-- NewJeans
(7, 'Get Up',                      '2023-07-21', 'Mini Album',   2);

-- ============================================================
-- COLLECTION ITEMS (16 rows)
-- ============================================================
INSERT INTO collection_items (album_id, version_name, condition_grade, purchase_price, purchase_date, purchase_source, notes) VALUES
-- Map of the Soul: Persona (album_id=1)
(1, 'Ver. 1', 'Mint',      22.99, '2023-01-15', 'Weverse Shop',    'Sealed, came with photo book'),
(1, 'Ver. 3', 'Near Mint', 18.50, '2023-03-02', 'eBay',            'Minor corner dent'),
(1, 'Ver. 4', 'Mint',      24.00, '2023-05-10', 'Weverse Shop',    NULL),
-- BE (album_id=2)
(2, 'Essential Edition', 'Mint', 27.99, '2022-11-20', 'Ktown4u',   'Holiday gift from friend'),
-- Proof (album_id=3)
(3, 'Standard Edition', 'Mint', 35.00, '2022-06-12', 'Weverse Shop', 'Pre-ordered'),
(3, 'Collector Edition', 'Mint', 65.00, '2022-06-12', 'Weverse Shop', 'Includes extra disc'),
-- THE ALBUM (album_id=4)
(4, 'Ver. 1 (Jennie)', 'Mint', 19.99, '2021-08-14', 'Amazon', NULL),
(4, 'Ver. 2 (Jisoo)',  'Near Mint', 17.50, '2021-09-01', 'eBay', 'Small scuff on case'),
-- Born Pink (album_id=5)
(5, 'Standard', 'Mint', 21.99, '2022-09-20', 'YG Select', NULL),
-- Formula of Love (album_id=7)
(7, 'Set', 'Mint', 30.00, '2021-12-01', 'JYP Shop', 'Full set of 3'),
-- READY TO BE (album_id=8)
(8, 'READY', 'Mint', 18.99, '2023-03-15', 'Ktown4u', NULL),
-- ODDINARY (album_id=9)
(9, 'Morass', 'Near Mint', 16.50, '2022-04-10', 'eBay', NULL),
(9, 'Standard', 'Mint', 19.99, '2022-04-01', 'Weverse Shop', NULL),
-- MAXIDENT (album_id=10)
(10, 'Standard', 'Mint', 21.00, '2022-10-10', 'Weverse Shop', NULL),
-- MY WORLD (album_id=11)
(11, 'Real World Ver.', 'Mint', 22.99, '2023-05-15', 'SM Store', NULL),
-- Get Up (album_id=12)
(12, 'Bluebook', 'Mint', 17.99, '2023-08-01', 'Ktown4u', 'NewJeans first purchase!');

-- ============================================================
-- PHOTOCARDS (18 rows)
-- ============================================================
INSERT INTO photocards (item_id, member_name, card_type, is_duplicate, for_trade, estimated_value) VALUES
-- From item_id=1 (Map of the Soul Ver.1)
(1, 'Jimin',    'Standard', FALSE, FALSE, 12.00),
(1, 'V',        'Standard', FALSE, FALSE, 15.00),
-- From item_id=2 (Map of the Soul Ver.3)
(2, 'Jungkook', 'Standard', FALSE, FALSE, 18.00),
(2, 'RM',       'Standard', TRUE,  TRUE,  8.00),
-- From item_id=3 (Map of the Soul Ver.4)
(3, 'Jin',      'Standard', FALSE, FALSE, 10.00),
(3, 'SUGA',     'Standard', FALSE, FALSE, 14.00),
-- From item_id=4 (BE Essential)
(4, 'j-hope',   'Rare',     FALSE, FALSE, 25.00),
(4, 'Jimin',    'Standard', TRUE,  TRUE,  9.00),
-- From item_id=5 (Proof Standard)
(5, 'V',        'Special',  FALSE, FALSE, 30.00),
(5, 'Jungkook', 'Rare',     FALSE, FALSE, 28.00),
-- From item_id=7 (THE ALBUM Jennie)
(7, 'Jennie',   'POB',      FALSE, FALSE, 45.00),
(7, 'Lisa',     'Standard', FALSE, FALSE, 16.00),
-- From item_id=9 (Born Pink)
(9, 'Rosé',     'Unit',     FALSE, FALSE, 20.00),
(9, 'Jisoo',    'Standard', FALSE, FALSE, 13.00),
-- From item_id=11 (READY)
(11,'Nayeon',   'Standard', FALSE, FALSE, 8.00),
(11,'Tzuyu',    'Rare',     FALSE, FALSE, 22.00),
-- From item_id=14 (MAXIDENT)
(14,'Felix',    'POB',      FALSE, FALSE, 40.00),
(14,'Han',      'Standard', TRUE,  TRUE,  7.00);

-- ============================================================
-- WISHLIST (10 rows)
-- ============================================================
INSERT INTO wishlist (album_id, version_name, priority, max_budget, notes, is_acquired) VALUES
(1, 'Ver. 2', 'High',      25.00, 'Need to complete full set',              FALSE),
(3, 'Weverse Edition', 'Must Have', 80.00, 'Exclusive photocards',          FALSE),
(4, 'Ver. 3 (Rosé)',   'Medium',    20.00, NULL,                             FALSE),
(4, 'Ver. 4 (Lisa)',   'Medium',    20.00, NULL,                             FALSE),
(6, 'Digipack Ver.',   'High',      40.00, 'EXO fan goal 2024',              FALSE),
(8, 'TO BE',           'Medium',    20.00, NULL,                             FALSE),
(9, 'Halazia',         'Low',       18.00, NULL,                             FALSE),
(11,'MY Ver.',         'High',      25.00, 'Want all 3 versions',            FALSE),
(12,'Woodbook',        'Must Have', 20.00, 'Complete the Get Up set',        FALSE),
(5, 'Limited Box',     'Low',       60.00, 'If price drops on Mercari',      FALSE);
