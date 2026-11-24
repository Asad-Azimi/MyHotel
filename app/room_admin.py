from decimal import Decimal, InvalidOperation

from app import db


DIRECTIONS = (
    "North", "South", "East", "West",
    "North-East", "South-East",
    "North-West", "South-West"
)


def list_room_types():
    return db.query("""
        SELECT TypeID, BedSize, SmokingAllowed,
               WheelchairAccessible
        FROM RoomType
        ORDER BY TypeID
    """)


def list_hotel_rooms(hotel_id):
    return db.query("""
        SELECT r.RoomID, r.RoomNumber, r.Floor,
               r.Direction, r.IsActive,
               t.TypeID, t.BedSize,
               t.SmokingAllowed, t.WheelchairAccessible,
               hr.NightlyRate
        FROM Room r
        JOIN RoomType t ON t.TypeID = r.TypeID
        JOIN HotelRoomRate hr
            ON hr.HotelID = r.HotelID
           AND hr.TypeID = r.TypeID
        WHERE r.HotelID = %s
        ORDER BY r.RoomNumber
    """, (hotel_id,))


def validate_room(number, type_id, floor, direction):
    number = str(number).strip()

    if not number or len(number) > 10:
        raise ValueError("Room number must be 1-10 characters.")

    try:
        type_id = int(type_id)
        floor = int(floor)
    except (ValueError, TypeError):
        raise ValueError("Type ID and floor must be whole numbers.")

    direction = str(direction).strip().title()

    if direction not in DIRECTIONS:
        raise ValueError("Invalid room direction.")

    return number, type_id, floor, direction


def add_room(hotel_id, number, type_id, floor, direction):
    number, type_id, floor, direction = validate_room(
        number, type_id, floor, direction
    )

    with db.transaction() as cur:
        cur.execute("""
            SELECT 1
            FROM HotelRoomRate
            WHERE HotelID = %s AND TypeID = %s
        """, (hotel_id, type_id))

        if not cur.fetchone():
            raise ValueError(
                "This hotel has no rate for the selected room type. "
                "Set the rate first."
            )

        cur.execute("""
            INSERT INTO Room
                (HotelID, RoomNumber, TypeID, Floor, Direction)
            VALUES (%s, %s, %s, %s, %s)
        """, (hotel_id, number, type_id, floor, direction))

        return cur.lastrowid


def update_room(room_id, number, type_id, floor, direction):
    number, type_id, floor, direction = validate_room(
        number, type_id, floor, direction
    )

    with db.transaction() as cur:
        cur.execute(
            "SELECT HotelID, TypeID FROM Room WHERE RoomID=%s FOR UPDATE",
            (room_id,)
        )
        room = cur.fetchone()

        if not room:
            raise ValueError("Room not found.")

        if type_id != room["TypeID"]:
            cur.execute("""
                SELECT 1 FROM ReservedRoom
                WHERE RoomID = %s LIMIT 1
            """, (room_id,))

            if cur.fetchone():
                raise ValueError(
                    "Cannot change room type because this room "
                    "has reservation history."
                )

        cur.execute("""
            SELECT 1 FROM HotelRoomRate
            WHERE HotelID=%s AND TypeID=%s
        """, (room["HotelID"], type_id))

        if not cur.fetchone():
            raise ValueError(
                "This hotel has no rate for the selected room type."
            )

        cur.execute("""
            UPDATE Room
            SET RoomNumber=%s, TypeID=%s,
                Floor=%s, Direction=%s
            WHERE RoomID=%s
        """, (number, type_id, floor, direction, room_id))


def set_room_active(room_id, active):
    with db.transaction() as cur:
        cur.execute(
            "SELECT RoomID FROM Room WHERE RoomID=%s FOR UPDATE",
            (room_id,)
        )

        if not cur.fetchone():
            raise ValueError("Room not found.")

        if not active:
            cur.execute("""
                SELECT 1
                FROM ReservedRoom rr
                JOIN Reservation res
                  ON res.ReservationID = rr.ReservationID
                WHERE rr.RoomID=%s
                  AND res.Status IN ('Booked', 'CheckedIn')
                  AND res.CheckOutDate > UTC_DATE()
                LIMIT 1
            """, (room_id,))

            if cur.fetchone():
                raise ValueError(
                    "Cannot deactivate a room with an active "
                    "or upcoming reservation."
                )

        cur.execute(
            "UPDATE Room SET IsActive=%s WHERE RoomID=%s",
            (int(active), room_id)
        )


def set_room_rate(hotel_id, type_id, rate):
    try:
        rate = Decimal(str(rate))
        if not rate.is_finite() or rate < 0:
            raise ValueError()
        rate = rate.quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        raise ValueError("Rate must be a nonnegative amount.")

    with db.transaction() as cur:
        cur.execute("""
            SELECT 1 FROM HotelRoomRate
            WHERE HotelID=%s AND TypeID=%s
            FOR UPDATE
        """, (hotel_id, type_id))

        if cur.fetchone():
            cur.execute("""
                UPDATE HotelRoomRate
                SET NightlyRate=%s
                WHERE HotelID=%s AND TypeID=%s
            """, (rate, hotel_id, type_id))
        else:
            cur.execute("""
                INSERT INTO HotelRoomRate
                    (HotelID, TypeID, NightlyRate)
                VALUES (%s, %s, %s)
            """, (hotel_id, type_id, rate))


def delete_room(room_id):
    """Delete a room only when it has never been reserved."""

    with db.transaction() as cur:
        cur.execute(
            "SELECT RoomID FROM Room WHERE RoomID=%s FOR UPDATE",
            (room_id,)
        )

        if not cur.fetchone():
            raise ValueError("Room not found.")

        cur.execute(
            "SELECT 1 FROM ReservedRoom WHERE RoomID=%s LIMIT 1",
            (room_id,)
        )

        if cur.fetchone():
            raise ValueError(
                "This room has reservation history. "
                "Deactivate it instead."
            )

        cur.execute(
            "DELETE FROM Room WHERE RoomID=%s",
            (room_id,)
        )