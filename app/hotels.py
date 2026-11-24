from app import db
from app.db import get_connection
from datetime import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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


def validate_hotel(name, street, city, state, postal_code,
                   rating, time_zone, check_in_time):
    """Validate hotel information before saving it."""

    fields = [
        ("Hotel name", name, 100),
        ("Street", street, 150),
        ("City", city, 100),
        ("State", state, 100),
        ("Postal code", postal_code, 20),
        ("Time zone", time_zone, 64),
    ]

    cleaned = []

    for label, value, max_length in fields:
        value = str(value).strip()

        if not value:
            raise ValueError(f"{label} is required.")

        if len(value) > max_length:
            raise ValueError(f"{label} is too long.")

        cleaned.append(value)

    try:
        rating = int(rating)
    except (TypeError, ValueError):
        raise ValueError("Rating must be a whole number.")

    if not 1 <= rating <= 6:
        raise ValueError("Rating must be between 1 and 6.")

    try:
        ZoneInfo(cleaned[5])
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError(
            "Invalid time zone. Use America/New_York, "
            "America/Chicago, etc."
        )

    try:
        check_in = time.fromisoformat(str(check_in_time).strip())
        if check_in.tzinfo is not None:
            raise ValueError()
    except ValueError:
        raise ValueError("Check-in time must be HH:MM (24-hour).")

    return (
        cleaned[0], cleaned[1], cleaned[2],
        cleaned[3], cleaned[4], rating,
        cleaned[5], check_in
    )


def add_hotel(name, street, city, state, postal_code,
              rating, time_zone, check_in_time):
    """Create a new hotel."""

    values = validate_hotel(
        name, street, city, state, postal_code,
        rating, time_zone, check_in_time
    )

    with db.transaction() as cur:
        cur.execute("""
            INSERT INTO Hotel
                (Name, Street, City, State, PostalCode,
                 Rating, TimeZone, CheckInTime)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, values)

        return cur.lastrowid


def update_hotel(hotel_id, name, street, city, state,
                 postal_code, rating, time_zone, check_in_time):
    """Update the information of an existing hotel."""

    values = validate_hotel(
        name, street, city, state, postal_code,
        rating, time_zone, check_in_time
    )

    with db.transaction() as cur:
        cur.execute(
            "SELECT HotelID FROM Hotel WHERE HotelID=%s FOR UPDATE",
            (hotel_id,)
        )

        if cur.fetchone() is None:
            raise ValueError("Hotel not found.")

        cur.execute("""
            UPDATE Hotel
            SET Name=%s, Street=%s, City=%s, State=%s,
                PostalCode=%s, Rating=%s, TimeZone=%s,
                CheckInTime=%s
            WHERE HotelID=%s
        """, values + (hotel_id,))


def delete_hotel(hotel_id):
    """Delete a hotel only if no related records depend on it."""

    dependent_tables = (
        "Room",
        "Reservation",
        "HotelRoomRate",
        "HotelAmenity",
        "HotelNearbyFeature",
        "ConferenceRoom"
    )

    with db.transaction() as cur:
        cur.execute(
            "SELECT HotelID FROM Hotel WHERE HotelID=%s FOR UPDATE",
            (hotel_id,)
        )

        if cur.fetchone() is None:
            raise ValueError("Hotel not found.")

        for table in dependent_tables:
            cur.execute(
                f"SELECT 1 FROM {table} WHERE HotelID=%s LIMIT 1",
                (hotel_id,)
            )

            if cur.fetchone():
                raise ValueError(
                    f"Cannot delete this hotel because "
                    f"it has related records in {table}."
                )

        cur.execute(
            "DELETE FROM Hotel WHERE HotelID=%s",
            (hotel_id,)
        )
