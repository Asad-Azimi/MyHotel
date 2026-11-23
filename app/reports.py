from app.db import get_connection


def get_hotels_near_ocean_or_mountain():
    """Required query 3: Hotels near an ocean or mountain."""

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    h.City,
                    h.Name AS HotelName,
                    h.Street,
                    h.State,
                    h.PostalCode,
                    nf.FeatureName
                FROM Hotel h
                JOIN HotelNearbyFeature hnf
                    ON h.HotelID = hnf.HotelID
                JOIN NearbyFeature nf
                    ON hnf.FeatureID = nf.FeatureID
                WHERE nf.FeatureName IN ('Ocean', 'Mountain')
                ORDER BY h.City, h.Name
            """)

            return cursor.fetchall()

    finally:
        conn.close()