from app.db import get_connection
from decimal import Decimal
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


def get_reservation_report(reservation_id):
    """Fetch the information required for the reservation report."""
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            # Reservation, guest, hotel, and cardholder
            cursor.execute("""
                SELECT r.ReservationID, r.Status, r.BookedAtUTC,
                       r.CheckInDate, r.CheckOutDate,
                       r.ScheduledCheckInAtUTC, r.ActualCheckInAtUTC,
                       r.CancelledAtUTC,
                       h.HotelID, h.Name AS HotelName, h.Street,
                       h.City, h.State, h.PostalCode, h.Rating,
                       h.TimeZone, h.CheckInTime,
                       p.FullName AS GuestName, p.Phone AS GuestPhone,
                       p.MailingAddress AS GuestAddress,
                       pc.CardholderName,
                       (SELECT COUNT(*) FROM Room x
                        WHERE x.HotelID = h.HotelID) AS TotalHotelRooms
                FROM Reservation r
                JOIN Hotel h ON h.HotelID = r.HotelID
                JOIN Person p ON p.PersonID = r.GuestPersonID
                JOIN PaymentCard pc ON pc.CardID = r.CardID
                WHERE r.ReservationID = %s
            """, (reservation_id,))

            reservation = cursor.fetchone()

            if reservation is None:
                return None

            # Rooms and historical booked rates
            cursor.execute("""
                SELECT rm.RoomNumber, rm.Floor, rm.Direction,
                       rt.BedSize, rt.SmokingAllowed,
                       rt.WheelchairAccessible, rr.BookedNightlyRate
                FROM ReservedRoom rr
                JOIN Room rm ON rm.RoomID = rr.RoomID
                JOIN RoomType rt ON rt.TypeID = rm.TypeID
                WHERE rr.ReservationID = %s
                ORDER BY rm.RoomNumber
            """, (reservation_id,))

            rooms = cursor.fetchall()

            # Nearby features
            cursor.execute("""
                SELECT nf.FeatureName
                FROM HotelNearbyFeature hnf
                JOIN NearbyFeature nf ON nf.FeatureID = hnf.FeatureID
                WHERE hnf.HotelID = %s
                ORDER BY nf.FeatureName
            """, (reservation["HotelID"],))

            features = cursor.fetchall()

            # Hotel amenities
            cursor.execute("""
                SELECT a.AmenityName, ha.Price
                FROM HotelAmenity ha
                JOIN Amenity a ON a.AmenityID = ha.AmenityID
                WHERE ha.HotelID = %s
                ORDER BY a.AmenityName
            """, (reservation["HotelID"],))

            amenities = cursor.fetchall()

            # Conference rooms
            cursor.execute("""
                SELECT Name, Capacity
                FROM ConferenceRoom
                WHERE HotelID = %s
                ORDER BY Name
            """, (reservation["HotelID"],))

            conference_rooms = cursor.fetchall()

            # Recorded charges
            cursor.execute("""
                SELECT c.ChargeType, c.Description, c.Amount,
                       c.ChargedAtUTC, a.AmenityName
                FROM Charge c
                LEFT JOIN Amenity a ON a.AmenityID = c.AmenityID
                WHERE c.ReservationID = %s
                ORDER BY c.ChargedAtUTC, c.ChargeID
            """, (reservation_id,))

            charges = cursor.fetchall()

        return {
            "reservation": reservation,
            "rooms": rooms,
            "features": features,
            "amenities": amenities,
            "conference_rooms": conference_rooms,
            "charges": charges
        }

    finally:
        conn.close()


def format_reservation_report(data):
    """Convert the reservation information to printable text."""

    r = data["reservation"]
    nights = (r["CheckOutDate"] - r["CheckInDate"]).days

    lines = [
        "=" * 55,
        "MYHOTEL - RESERVATION REPORT",
        "=" * 55,
        f"Reservation #: {r['ReservationID']}",
        f"Status: {r['Status']}",
        f"Booked (UTC): {r['BookedAtUTC']}",
        f"Check-in: {r['CheckInDate']}",
        f"Check-out: {r['CheckOutDate']}",
        f"Number of nights: {nights}",
        f"Scheduled check-in (UTC): {r['ScheduledCheckInAtUTC']}",
        f"Actual check-in (UTC): {r['ActualCheckInAtUTC'] or 'Not checked in'}",
        f"Cancelled (UTC): {r['CancelledAtUTC'] or 'Not cancelled'}",
        "",
        "GUEST INFORMATION",
        f"Name: {r['GuestName']}",
        f"Phone: {r['GuestPhone']}",
        f"Address: {r['GuestAddress'] or 'Not provided'}",
        f"Payment cardholder: {r['CardholderName']}",
        "",
        "HOTEL INFORMATION",
        f"Name: {r['HotelName']}",
        f"Address: {r['Street']}, {r['City']}, "
        f"{r['State']} {r['PostalCode']}",
        f"Rating: {r['Rating']} stars",
        f"Total hotel rooms: {r['TotalHotelRooms']}",
        f"Check-in time: {r['CheckInTime']}",
        f"Time zone: {r['TimeZone']}",
        "",
        "NEARBY FEATURES",
    ]

    if data["features"]:
        for feature in data["features"]:
            lines.append(f"- {feature['FeatureName']}")
    else:
        lines.append("None listed")

    lines.extend(["", "HOTEL AMENITIES"])

    if data["amenities"]:
        for amenity in data["amenities"]:
            price = (
                "Free" if amenity["Price"] == 0
                else f"${amenity['Price']:.2f}"
            )
            lines.append(f"- {amenity['AmenityName']}: {price}")
    else:
        lines.append("None listed")

    lines.extend(["", "CONFERENCE ROOMS"])

    if data["conference_rooms"]:
        for room in data["conference_rooms"]:
            lines.append(
                f"- {room['Name']} (Capacity: {room['Capacity']})"
            )
    else:
        lines.append("None")

    lines.extend(["", "RESERVED ROOMS"])

    room_subtotal = Decimal("0.00")

    for room in data["rooms"]:
        total = room["BookedNightlyRate"] * nights
        room_subtotal += total

        lines.extend([
            f"Room {room['RoomNumber']}",
            f"  Floor: {room['Floor']}",
            f"  Direction: {room['Direction']}",
            f"  Bed size: {room['BedSize']}",
            f"  Smoking: {'Yes' if room['SmokingAllowed'] else 'No'}",
            f"  Accessible: "
            f"{'Yes' if room['WheelchairAccessible'] else 'No'}",
            f"  Rate: ${room['BookedNightlyRate']:.2f}/night",
            f"  Total: ${total:.2f}",
            ""
        ])

    if not data["rooms"]:
        lines.append("No rooms assigned - reservation needs review")

    lines.append(f"Booked room subtotal: ${room_subtotal:.2f}")

    lines.extend(["", "RECORDED CHARGES"])

    charge_total = Decimal("0.00")

    if data["charges"]:
        for charge in data["charges"]:
            charge_total += charge["Amount"]
            lines.append(
                f"- {charge['ChargedAtUTC']} UTC | "
                f"{charge['ChargeType']}: "
                f"{charge['Description']} | "
                f"${charge['Amount']:.2f}"
            )
    else:
        lines.append("No charges recorded")

    lines.extend([
        f"Recorded charge total: ${charge_total:.2f}",
        "Note: Booked room subtotal and recorded charges "
        "are different measures.",
        "=" * 55
    ])

    return "\n".join(lines)