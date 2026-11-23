from datetime import date
from app.db import get_connection


def find_available_rooms(
    city,
    check_in,
    check_out,
    bed_size=None,
    smoking=None,
    accessible=None
):
    """Return available rooms matching the requested criteria."""

    check_in = date.fromisoformat(check_in)
    check_out = date.fromisoformat(check_out)

    if check_out <= check_in:
        raise ValueError("Check-out must be after check-in.")

    sql = """
        SELECT
            h.HotelID,
            h.Name AS HotelName,
            h.City,
            r.RoomID,
            r.RoomNumber,
            r.Floor,
            r.Direction,
            t.BedSize,
            t.SmokingAllowed,
            t.WheelchairAccessible,
            hr.NightlyRate
        FROM Room r

        JOIN Hotel h
            ON r.HotelID = h.HotelID

        JOIN RoomType t
            ON r.TypeID = t.TypeID

        JOIN HotelRoomRate hr
            ON r.HotelID = hr.HotelID
           AND r.TypeID = hr.TypeID

        WHERE h.City = %s
          AND r.IsActive = 1

          AND NOT EXISTS (
              SELECT 1
              FROM ReservedRoom rr
              JOIN Reservation res
                  ON rr.ReservationID = res.ReservationID

              WHERE rr.RoomID = r.RoomID
                AND res.Status <> 'Cancelled'
                AND res.CheckInDate < %s
                AND res.CheckOutDate > %s
          )
    """

    params = [city, check_out, check_in]

    if bed_size is not None:
        sql += " AND t.BedSize = %s"
        params.append(bed_size)

    if smoking is not None:
        sql += " AND t.SmokingAllowed = %s"
        params.append(int(smoking))

    if accessible is not None:
        sql += " AND t.WheelchairAccessible = %s"
        params.append(int(accessible))

    sql += " ORDER BY h.Name, r.RoomNumber"

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conn.close()