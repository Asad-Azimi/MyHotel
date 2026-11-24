"""Hotel facilities: amenities, nearby features and conference rooms.

Uses the canonical MyHotel schema and the app.db query/transaction helpers.
"""

from decimal import Decimal, InvalidOperation

from app import db


def _name(value, label, maximum):
    result = " ".join(str(value or "").split())
    if not result:
        raise ValueError(f"{label} is required.")
    if len(result) > maximum:
        raise ValueError(f"{label} must be {maximum} characters or fewer.")
    return result


def _id(value, label):
    try:
        result = int(value)
    except (ValueError, TypeError):
        raise ValueError(f"{label} must be a whole number.")
    if result < 1:
        raise ValueError(f"{label} must be positive.")
    return result


def _money(value):
    try:
        result = Decimal(str(value).strip())
        if not result.is_finite() or result < 0:
            raise InvalidOperation
        rounded = result.quantize(Decimal("0.01"))
        if rounded != result:
            raise InvalidOperation
        result = rounded
        if result > Decimal("99999999.99"):
            raise InvalidOperation
        return result
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Price must be a nonnegative amount (up to 2 decimal places).")


def _require_row(cur, table, key, value, label):
    # Only called with the fixed table/column names defined in this module.
    cur.execute(f"SELECT 1 FROM {table} WHERE {key}=%s FOR UPDATE", (value,))
    if cur.fetchone() is None:
        raise ValueError(f"{label} not found.")


# ------- Master amenity catalog + per-hotel offerings -------

def list_amenities():
    return db.query("SELECT AmenityID, AmenityName FROM Amenity ORDER BY AmenityName")


def add_amenity(name):
    name = _name(name, "Amenity name", 100)
    with db.transaction() as cur:
        cur.execute("INSERT INTO Amenity (AmenityName) VALUES (%s)", (name,))
        return cur.lastrowid


def rename_amenity(amenity_id, new_name):
    amenity_id = _id(amenity_id, "Amenity ID")
    new_name = _name(new_name, "Amenity name", 100)
    with db.transaction() as cur:
        _require_row(cur, "Amenity", "AmenityID", amenity_id, "Amenity")
        cur.execute("UPDATE Amenity SET AmenityName=%s WHERE AmenityID=%s",
                    (new_name, amenity_id))


def delete_unused_amenity(amenity_id):
    """FKs prevent removal if hotels offer it or historical charges reference it."""
    amenity_id = _id(amenity_id, "Amenity ID")
    with db.transaction() as cur:
        _require_row(cur, "Amenity", "AmenityID", amenity_id, "Amenity")
        for table in ("HotelAmenity", "Charge"):
            cur.execute(f"SELECT 1 FROM {table} WHERE AmenityID=%s LIMIT 1", (amenity_id,))
            if cur.fetchone():
                raise ValueError(f"Cannot delete: records in {table} reference this amenity.")
        cur.execute("DELETE FROM Amenity WHERE AmenityID=%s", (amenity_id,))


def list_hotel_amenities(hotel_id):
    hotel_id = _id(hotel_id, "Hotel ID")
    return db.query("""
        SELECT a.AmenityID, a.AmenityName, ha.Price
        FROM HotelAmenity ha
        JOIN Amenity a ON a.AmenityID = ha.AmenityID
        WHERE ha.HotelID=%s
        ORDER BY a.AmenityName
    """, (hotel_id,))


def set_hotel_amenity(hotel_id, amenity_id, price):
    """Add an amenity to a hotel or change its hotel-specific price; 0 means free."""
    hotel_id = _id(hotel_id, "Hotel ID")
    amenity_id = _id(amenity_id, "Amenity ID")
    price = _money(price)
    with db.transaction() as cur:
        _require_row(cur, "Hotel", "HotelID", hotel_id, "Hotel")
        _require_row(cur, "Amenity", "AmenityID", amenity_id, "Amenity")
        cur.execute("""
            INSERT INTO HotelAmenity (HotelID, AmenityID, Price)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE Price=%s
        """, (hotel_id, amenity_id, price, price))


def remove_hotel_amenity(hotel_id, amenity_id):
    """Only remove the hotel's offering, not the amenity or past charges."""
    hotel_id = _id(hotel_id, "Hotel ID")
    amenity_id = _id(amenity_id, "Amenity ID")
    with db.transaction() as cur:
        cur.execute("DELETE FROM HotelAmenity WHERE HotelID=%s AND AmenityID=%s",
                    (hotel_id, amenity_id))
        if cur.rowcount == 0:
            raise ValueError("This hotel does not offer that amenity.")


# ------- Named nearby features + hotel/feature links -------

def list_nearby_features():
    return db.query("SELECT FeatureID, FeatureName FROM NearbyFeature ORDER BY FeatureName")


def add_nearby_feature(name):
    name = _name(name, "Feature name", 50)
    with db.transaction() as cur:
        cur.execute("INSERT INTO NearbyFeature (FeatureName) VALUES (%s)", (name,))
        return cur.lastrowid


def rename_nearby_feature(feature_id, new_name):
    feature_id = _id(feature_id, "Feature ID")
    new_name = _name(new_name, "Feature name", 50)
    with db.transaction() as cur:
        _require_row(cur, "NearbyFeature", "FeatureID", feature_id, "Feature")
        cur.execute("UPDATE NearbyFeature SET FeatureName=%s WHERE FeatureID=%s",
                    (new_name, feature_id))


def delete_unused_feature(feature_id):
    feature_id = _id(feature_id, "Feature ID")
    with db.transaction() as cur:
        _require_row(cur, "NearbyFeature", "FeatureID", feature_id, "Feature")
        cur.execute("SELECT 1 FROM HotelNearbyFeature WHERE FeatureID=%s LIMIT 1", (feature_id,))
        if cur.fetchone():
            raise ValueError("Remove this feature from all hotels before deleting it.")
        cur.execute("DELETE FROM NearbyFeature WHERE FeatureID=%s", (feature_id,))


def list_hotel_features(hotel_id):
    hotel_id = _id(hotel_id, "Hotel ID")
    return db.query("""
        SELECT f.FeatureID, f.FeatureName
        FROM HotelNearbyFeature hf
        JOIN NearbyFeature f ON f.FeatureID=hf.FeatureID
        WHERE hf.HotelID=%s ORDER BY f.FeatureName
    """, (hotel_id,))


def assign_nearby_feature(hotel_id, feature_id):
    hotel_id = _id(hotel_id, "Hotel ID")
    feature_id = _id(feature_id, "Feature ID")
    with db.transaction() as cur:
        _require_row(cur, "Hotel", "HotelID", hotel_id, "Hotel")
        _require_row(cur, "NearbyFeature", "FeatureID", feature_id, "Feature")
        cur.execute("SELECT 1 FROM HotelNearbyFeature WHERE HotelID=%s AND FeatureID=%s",
                    (hotel_id, feature_id))
        if cur.fetchone():
            raise ValueError("This feature is already assigned to the hotel.")
        cur.execute("INSERT INTO HotelNearbyFeature (HotelID, FeatureID) VALUES (%s,%s)",
                    (hotel_id, feature_id))


def remove_nearby_feature(hotel_id, feature_id):
    hotel_id = _id(hotel_id, "Hotel ID")
    feature_id = _id(feature_id, "Feature ID")
    with db.transaction() as cur:
        cur.execute("DELETE FROM HotelNearbyFeature WHERE HotelID=%s AND FeatureID=%s",
                    (hotel_id, feature_id))
        if cur.rowcount == 0:
            raise ValueError("That feature is not assigned to this hotel.")


# ------- Conference rooms -------

def list_conference_rooms(hotel_id):
    hotel_id = _id(hotel_id, "Hotel ID")
    return db.query("""
        SELECT ConferenceRoomID, Name, Capacity
        FROM ConferenceRoom
        WHERE HotelID=%s ORDER BY Name
    """, (hotel_id,))


def add_conference_room(hotel_id, name, capacity):
    hotel_id = _id(hotel_id, "Hotel ID")
    name = _name(name, "Conference room name", 100)
    capacity = _id(capacity, "Capacity")
    with db.transaction() as cur:
        _require_row(cur, "Hotel", "HotelID", hotel_id, "Hotel")
        cur.execute("""
            INSERT INTO ConferenceRoom (HotelID, Name, Capacity)
            VALUES (%s,%s,%s)
        """, (hotel_id, name, capacity))
        return cur.lastrowid


def update_conference_room(conference_room_id, name, capacity):
    conference_room_id = _id(conference_room_id, "Conference room ID")
    name = _name(name, "Conference room name", 100)
    capacity = _id(capacity, "Capacity")
    with db.transaction() as cur:
        _require_row(cur, "ConferenceRoom", "ConferenceRoomID", conference_room_id,
                     "Conference room")
        cur.execute("""
            UPDATE ConferenceRoom SET Name=%s, Capacity=%s
            WHERE ConferenceRoomID=%s
        """, (name, capacity, conference_room_id))


def delete_conference_room(conference_room_id):
    conference_room_id = _id(conference_room_id, "Conference room ID")
    with db.transaction() as cur:
        _require_row(cur, "ConferenceRoom", "ConferenceRoomID", conference_room_id,
                     "Conference room")
        cur.execute("DELETE FROM ConferenceRoom WHERE ConferenceRoomID=%s",
                    (conference_room_id,))
