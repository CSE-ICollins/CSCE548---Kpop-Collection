import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date

DSN = "dbname=kpop_collection user=postgres"

def get_conn():
    return psycopg2.connect(DSN)

def list_albums():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT a.album_id, a.title, ar.name AS artist
                FROM albums a
                JOIN artists ar ON a.artist_id = ar.artist_id
                ORDER BY a.album_id
            """)
            for r in cur.fetchall():
                print(f"{r['album_id']}: {r['artist']} - {r['title']}")

def show_album(album_id):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT a.title, ar.name AS artist
                FROM albums a
                JOIN artists ar ON a.artist_id = ar.artist_id
                WHERE a.album_id = %s
            """, (album_id,))
            album = cur.fetchone()
            if not album:
                print("Album not found")
                return
            print(album['artist'], "-", album['title'])

            cur.execute("SELECT * FROM editions WHERE album_id = %s", (album_id,))
            editions = cur.fetchall()
            for e in editions:
                print(" Edition:", e['edition_name'])
                cur.execute("SELECT item_type, qty FROM inclusions WHERE edition_id = %s", (e['edition_id'],))
                for i in cur.fetchall():
                    print("   -", i['item_type'], "x", i['qty'])

def main():
    print("K-pop Collection")
    print("1. List albums")
    print("2. Show album details")
    choice = input("Choose: ")

    if choice == "1":
        list_albums()
    elif choice == "2":
        aid = int(input("Album ID: "))
        show_album(aid)
    else:
        print("Goodbye")

if __name__ == "__main__":
    main()
