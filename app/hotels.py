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

def get_hotel_details(hotel_id):
    """Get hotel information, features, amenities, and conference rooms."""

    conn = get_connection()

    try:
        with conn.cursor() as cursor:

            # 1. Get the hotel
            cursor.execute("""
                SELECT *
                FROM Hotel
                WHERE HotelID = %s
            """, (hotel_id,))

            hotel = cursor.fetchone()

            if hotel is None:
                return None

            # 2. Get nearby features
            cursor.execute("""
                SELECT nf.FeatureName
                FROM HotelNearbyFeature hnf
                JOIN NearbyFeature nf
                    ON hnf.FeatureID = nf.FeatureID
                WHERE hnf.HotelID = %s
                ORDER BY nf.FeatureName
            """, (hotel_id,))

            features = cursor.fetchall()

            # 3. Get amenities and their prices
            cursor.execute("""
                SELECT a.AmenityName, ha.Price
                FROM HotelAmenity ha
                JOIN Amenity a
                    ON ha.AmenityID = a.AmenityID
                WHERE ha.HotelID = %s
                ORDER BY a.AmenityName
            """, (hotel_id,))

            amenities = cursor.fetchall()

            # 4. Get conference rooms
            cursor.execute("""
                SELECT Name, Capacity
                FROM ConferenceRoom
                WHERE HotelID = %s
                ORDER BY Name
            """, (hotel_id,))

            conference_rooms = cursor.fetchall()

            return {
                "hotel": hotel,
                "features": features,
                "amenities": amenities,
                "conference_rooms": conference_rooms
            }

    finally:
        conn.close()