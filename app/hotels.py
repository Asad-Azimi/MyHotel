from app.db import get_connection


def list_hotels():
    """Return all hotels from the database."""
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT HotelID, Name, City, State, Rating
                FROM Hotel
                ORDER BY City, Name
            """)

            return cursor.fetchall()

    finally:
        conn.close()