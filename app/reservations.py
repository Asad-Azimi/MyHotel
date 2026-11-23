#reservations.py: booking, changing, cancelling, availability, and the reservation queries

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from app import charges
from app import customers
from app import db

LATE_HOURS = 48 # cancel at least 48 hours before check-in
BEDS = ('King', 'Queen', 'Double')


# helpers

def parse_date(value, label):
    try:
        return date.fromisoformat((value or '').strip())
    except ValueError:
        raise ValueError('%s must be a date like 2026-12-31.' % label)


def parse_stay(check_in, check_out):
    ci, co = parse_date(check_in, 'Check-in'), parse_date(check_out, 'Check-out')
    if co <= ci:
        raise ValueError('Check-out must be after check-in.')
    return ci, co


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def money(amount):
    return f'${amount:,.2f}'


def to_local_str(utc_dt, tz):
    # show a UTC datetime in the hotel's own time zone
    local = utc_dt.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(tz))
    return local.strftime('%Y-%m-%d %H:%M %Z')


# hotel and room ids must be whole numbers, and at least one room is needed
def _clean_ids(hotel_id, room_ids):
    try:
        hotel_id = int(hotel_id)
        room_ids = sorted(set(int(r) for r in room_ids))
    except (TypeError, ValueError):
        raise ValueError('Hotel and room IDs must be whole numbers.')
    if len(room_ids) == 0:
        raise ValueError('Select at least one room.')
    return hotel_id, room_ids


def _scheduled_utc(cur, hotel_id, check_in):
    # hotel's local check-in date + check-in time -> UTC (stored in the reservation)
    #converts UTC values
    cur.execute('SELECT TimeZone, CheckInTime FROM Hotel WHERE HotelID=%s', (hotel_id,))
    hotel = cur.fetchone()
    if hotel is None:
        raise ValueError('No hotel with ID %s.' % hotel_id)
    local = datetime.combine(check_in, time()) + hotel['CheckInTime']    # midnight + check-in time
    local = local.replace(tzinfo=ZoneInfo(hotel['TimeZone']))
    return local.astimezone(timezone.utc).replace(tzinfo=None)


# queries 1 and 2

def search_available_rooms(city, check_in, check_out, bed=None, smoking=None, wheelchair=False):
    # available rooms in every hotel of a city for the dates
    city = (city or '').strip()
    if not city:
        raise ValueError('City is required.')
    ci, co = parse_stay(check_in, check_out)
    if bed:
        bed = bed.strip().capitalize()
        if bed not in BEDS:
            raise ValueError('Bed size must be King, Queen or Double.')

    sql = '''SELECT h.HotelID, h.Name AS Hotel, r.RoomID, r.RoomNumber, r.Floor, r.Direction,
                    t.BedSize, t.SmokingAllowed, t.WheelchairAccessible, hr.NightlyRate
             FROM Room r
             JOIN Hotel h ON h.HotelID = r.HotelID
             JOIN RoomType t ON t.TypeID = r.TypeID
             JOIN HotelRoomRate hr ON hr.HotelID = r.HotelID AND hr.TypeID = r.TypeID
             WHERE h.City=%s AND r.IsActive=1'''
    args = [city]
    if bed:
        sql += ' AND t.BedSize=%s'
        args.append(bed)
    if smoking is not None:
        sql += ' AND t.SmokingAllowed=%s'
        args.append(1 if smoking else 0)
    if wheelchair:
        sql += ' AND t.WheelchairAccessible=1'
    # leave out rooms that overlap a Booked or CheckedIn reservation
    sql += '''
             AND NOT EXISTS (
                 SELECT 1 FROM ReservedRoom rr
                 JOIN Reservation res ON res.ReservationID = rr.ReservationID
                 WHERE rr.RoomID = r.RoomID AND res.Status IN ('Booked','CheckedIn')
                   AND res.CheckInDate < %s AND res.CheckOutDate > %s)
             ORDER BY h.Name, r.RoomNumber'''
    args += [co, ci]
    return db.query(sql, args)


def _check_rooms(cur, hotel_id, room_ids, check_in, check_out, ignore_res=0):
    # check that every room is active at this hotel and not already booked for these dates
    # ignore_res lets a reservation be changed without conflicting with itself
    for room_id in room_ids:
        # FOR UPDATE locks the room so two bookings can't take it at the same time
        cur.execute('SELECT RoomNumber FROM Room WHERE RoomID=%s AND HotelID=%s AND IsActive=1 FOR UPDATE',
                    (room_id, hotel_id))
        room = cur.fetchone()
        if room is None:
            raise ValueError('Room ID %s is not available at that hotel.' % room_id)
        cur.execute('''SELECT 1 FROM ReservedRoom rr
                       JOIN Reservation res ON res.ReservationID = rr.ReservationID
                       WHERE rr.RoomID=%s AND res.Status IN ('Booked','CheckedIn')
                         AND res.ReservationID <> %s
                         AND res.CheckInDate < %s AND res.CheckOutDate > %s''',
                    (room_id, ignore_res, check_out, check_in))
        if cur.fetchone():
            raise ValueError('Room %s is already booked for those dates.' % room['RoomNumber'])


def _insert_rooms(cur, res_id, room_ids):
    # one ReservedRoom per room, the room's current rate is saved with it
    for room_id in room_ids:
        cur.execute('''INSERT INTO ReservedRoom (ReservationID, RoomID, BookedNightlyRate)
                       SELECT %s, r.RoomID, hr.NightlyRate
                       FROM Room r JOIN HotelRoomRate hr ON hr.HotelID = r.HotelID AND hr.TypeID = r.TypeID
                       WHERE r.RoomID=%s''', (res_id, room_id))


def _resolve_card(cur, guest_id, guest_name, number, month, year, holder_name, holder_phone, holder_address):
    # find or create the card
    # the card holder is a Person: the guest by default, or someone else (name and phone required)
    # returns card_id
    if holder_name and holder_name.strip():
        if not (holder_phone or '').strip():
            raise ValueError("The card holder's phone number is required.")
        holder_id, _ = customers.get_or_create_person(cur, holder_name, holder_phone, holder_address,
                                                      require_address=False)
        name_on_card = holder_name
    else:
        holder_id = guest_id
        name_on_card = guest_name
    return customers.get_or_create_card(cur, holder_id, name_on_card, number, month, year)


# booking reservations

def create_reservation(guest_name, guest_phone, guest_address, hotel_id, check_in, check_out, room_ids,
                       card_number, exp_month, exp_year,
                       holder_name=None, holder_phone=None, holder_address=None):
    # book one or more rooms in one transaction
    # the guest is stored once (same name + phone is reused)
    # the card holder defaults to the guest, pass holder_name + holder_phone if the card is someone else's
    # no card number means no reservation
    # returns {'reservation_id', 'person_id', 'bonus'}
    name, phone, address = customers.clean_person(guest_name, guest_phone, guest_address)
    number, month, year = customers.clean_card(card_number, exp_month, exp_year)
    ci, co = parse_stay(check_in, check_out)
    hotel_id, room_ids = _clean_ids(hotel_id, room_ids)

    with db.transaction() as cur:
        guest_id, _ = customers.get_or_create_person(cur, name, phone, address)
        card_id = _resolve_card(cur, guest_id, name, number, month, year,
                                holder_name, holder_phone, holder_address)
        _check_rooms(cur, hotel_id, room_ids, ci, co)
        cur.execute('''INSERT INTO Reservation (GuestPersonID, HotelID, CardID, BookedAtUTC, CheckInDate,
                                                CheckOutDate, ScheduledCheckInAtUTC, Status)
                       VALUES (%s,%s,%s,UTC_TIMESTAMP(),%s,%s,%s,'Booked')''',
                    (guest_id, hotel_id, card_id, ci, co, _scheduled_utc(cur, hotel_id, ci)))
        res_id = cur.lastrowid
        _insert_rooms(cur, res_id, room_ids)

    # query 7: check if the guest now gets a bonus
    return {'reservation_id': res_id, 'person_id': guest_id, 'bonus': customers.check_bonus(guest_id)}


# gets a reservation by id and locks it so nothing else can change it until done
def _lock_reservation(cur, res_id):
    cur.execute('SELECT * FROM Reservation WHERE ReservationID=%s FOR UPDATE', (res_id,))
    res = cur.fetchone()
    if res is None:
        raise ValueError('No reservation with ID %s.' % res_id)
    return res


def _require_status(res, allowed, action):
    if res['Status'] not in allowed:
        raise ValueError('Cannot %s a reservation that is %s.' % (action, res['Status']))


# update

def update_reservation_dates(res_id, check_in, check_out):
    # change the dates (the rooms must still be free) and recompute the check-in deadline
    # costs are always rate x nights from the saved rates so they follow the new dates
    ci, co = parse_stay(check_in, check_out)
    with db.transaction() as cur:
        res = _lock_reservation(cur, res_id)
        _require_status(res, ('Booked',), 'change the dates of')
        cur.execute('SELECT RoomID FROM ReservedRoom WHERE ReservationID=%s ORDER BY RoomID', (res_id,))
        room_ids = [row['RoomID'] for row in cur.fetchall()]
        _check_rooms(cur, res['HotelID'], room_ids, ci, co, ignore_res=res_id)
        new_checkin_utc = _scheduled_utc(cur, res['HotelID'], ci)
        cur.execute('''UPDATE Reservation SET CheckInDate=%s, CheckOutDate=%s, ScheduledCheckInAtUTC=%s
                       WHERE ReservationID=%s''', (ci, co, new_checkin_utc, res_id))


def change_rooms(res_id, room_ids):
    # replace the reserved rooms (same hotel, must be free for the dates), rates are saved again
    with db.transaction() as cur:
        res = _lock_reservation(cur, res_id)
        _require_status(res, ('Booked',), 'change the rooms of')
        _, room_ids = _clean_ids(res['HotelID'], room_ids)
        _check_rooms(cur, res['HotelID'], room_ids, res['CheckInDate'], res['CheckOutDate'],
                     ignore_res=res_id)
        cur.execute('DELETE FROM ReservedRoom WHERE ReservationID=%s', (res_id,))
        _insert_rooms(cur, res_id, room_ids)


def change_guest(res_id, name, phone, address):
    # change who is staying (found or created like any customer)
    with db.transaction() as cur:
        res = _lock_reservation(cur, res_id)
        _require_status(res, ('Booked', 'CheckedIn'), 'change the guest of')
        guest_id, _ = customers.get_or_create_person(cur, name, phone, address)
        cur.execute('UPDATE Reservation SET GuestPersonID=%s WHERE ReservationID=%s', (guest_id, res_id))


def change_card(res_id, card_number, exp_month, exp_year,
                holder_name=None, holder_phone=None, holder_address=None):
    # use a different credit card for the reservation (its charges go to the reservation's card)
    number, month, year = customers.clean_card(card_number, exp_month, exp_year)
    with db.transaction() as cur:
        res = _lock_reservation(cur, res_id)
        _require_status(res, ('Booked', 'CheckedIn', 'CheckedOut'), 'change the card of')
        cur.execute('SELECT PersonID, FullName FROM Person WHERE PersonID=%s', (res['GuestPersonID'],))
        guest = cur.fetchone()
        card_id = _resolve_card(cur, guest['PersonID'], guest['FullName'], number, month, year,
                                holder_name, holder_phone, holder_address)
        cur.execute('UPDATE Reservation SET CardID=%s WHERE ReservationID=%s', (card_id, res_id))

#change status of guest to checked in
def check_in_guest(res_id):
    with db.transaction() as cur:
        res = _lock_reservation(cur, res_id)
        _require_status(res, ('Booked',), 'check in')
        cur.execute("UPDATE Reservation SET Status='CheckedIn', ActualCheckInAtUTC=UTC_TIMESTAMP() "
                    "WHERE ReservationID=%s", (res_id,))

#change status of guest to checked out
def check_out_guest(res_id):
    
    with db.transaction() as cur:
        res = _lock_reservation(cur, res_id)
        _require_status(res, ('CheckedIn',), 'check out')
        cur.execute("UPDATE Reservation SET Status='CheckedOut' WHERE ReservationID=%s", (res_id,))


# cancellation and no-shows

def cancel_reservation(res_id):
    # less than 48 hours before check-in: 20% of the first night is charged
    # cancelled reservations no longer hold their rooms
    # returns {'fee': Decimal, 'late': bool}
    with db.transaction() as cur:
        res = _lock_reservation(cur, res_id)
        _require_status(res, ('Booked',), 'cancel')
        now = utc_now()
        late = now > res['ScheduledCheckInAtUTC'] - timedelta(hours=LATE_HOURS)
        fee = Decimal('0.00')
        if late:
            fee = charges.first_night_fee(cur, res_id)
            charges.add_cancellation_charge(cur, res_id, fee, 'Late cancellation (under 48 hours)')
        cur.execute("UPDATE Reservation SET Status='Cancelled', CancelledAtUTC=%s WHERE ReservationID=%s",
                    (now, res_id))
    return {'fee': fee, 'late': late}


def charge_no_show(res_id):
    # the guest never arrived: charge 20% of the first night and mark the reservation NoShow
    with db.transaction() as cur:
        res = _lock_reservation(cur, res_id)
        _require_status(res, ('Booked',), 'mark as a no-show')
        if res['ScheduledCheckInAtUTC'] >= utc_now():
            raise ValueError('The check-in time has not passed yet.')
        fee = charges.first_night_fee(cur, res_id)
        charges.add_cancellation_charge(cur, res_id, fee, 'No-show')
        cur.execute("UPDATE Reservation SET Status='NoShow' WHERE ReservationID=%s", (res_id,))
    return fee


# query 4

def get_reservations_for_person(name, phone):
    person = customers.require_person(name, phone)
    return db.query('''SELECT res.ReservationID, h.Name AS Hotel, h.City, res.BookedAtUTC,
                              res.CheckInDate, res.CheckOutDate,
                              DATEDIFF(res.CheckOutDate, res.CheckInDate) AS Nights, res.Status,
                              GROUP_CONCAT(r.RoomNumber ORDER BY r.RoomNumber SEPARATOR ', ') AS Rooms
                       FROM Reservation res
                       JOIN Hotel h ON h.HotelID = res.HotelID
                       LEFT JOIN ReservedRoom rr ON rr.ReservationID = res.ReservationID
                       LEFT JOIN Room r ON r.RoomID = rr.RoomID
                       WHERE res.GuestPersonID=%s
                       GROUP BY res.ReservationID, h.Name, h.City, res.BookedAtUTC,
                                res.CheckInDate, res.CheckOutDate, res.Status
                       ORDER BY res.CheckInDate''', (person['PersonID'],))


# query 6

def get_late_arrivals():
    # still Booked (not cancelled, not checked in) and the scheduled check-in time has passed
    rows = db.query('''SELECT res.ReservationID, p.FullName, p.Phone, h.Name AS Hotel, h.City, h.TimeZone,
                              res.CheckInDate, res.ScheduledCheckInAtUTC,
                              GROUP_CONCAT(r.RoomNumber ORDER BY r.RoomNumber SEPARATOR ', ') AS Rooms
                       FROM Reservation res
                       JOIN Person p ON p.PersonID = res.GuestPersonID
                       JOIN Hotel h ON h.HotelID = res.HotelID
                       LEFT JOIN ReservedRoom rr ON rr.ReservationID = res.ReservationID
                       LEFT JOIN Room r ON r.RoomID = rr.RoomID
                       WHERE res.Status='Booked' AND res.ScheduledCheckInAtUTC < UTC_TIMESTAMP()
                       GROUP BY res.ReservationID, p.FullName, p.Phone, h.Name, h.City, h.TimeZone,
                                res.CheckInDate, res.ScheduledCheckInAtUTC
                       ORDER BY res.ScheduledCheckInAtUTC''')
    for r in rows:
        r['ScheduledLocal'] = to_local_str(r['ScheduledCheckInAtUTC'], r['TimeZone'])
    return rows


# query 8

def get_reservation_detail(res_id):
    # everything about one reservation: hotel, rooms, nights, rates, guest, card holder, charges
    rows = db.query('''SELECT res.*, DATEDIFF(res.CheckOutDate, res.CheckInDate) AS Nights,
                              h.Name AS HotelName, h.Street, h.City, h.State, h.PostalCode, h.Rating,
                              h.TimeZone,
                              g.FullName AS GuestName, g.Phone AS GuestPhone, g.MailingAddress AS GuestAddress,
                              pc.CardholderName, RIGHT(pc.CardNumber, 4) AS Last4, pc.ExpMonth, pc.ExpYear,
                              hp.FullName AS HolderName
                       FROM Reservation res
                       JOIN Hotel h ON h.HotelID = res.HotelID
                       JOIN Person g ON g.PersonID = res.GuestPersonID
                       JOIN PaymentCard pc ON pc.CardID = res.CardID
                       JOIN Person hp ON hp.PersonID = pc.HolderPersonID
                       WHERE res.ReservationID=%s''', (res_id,))
    if len(rows) == 0:
        raise ValueError('No reservation with ID %s.' % res_id)
    res = rows[0]

    rooms = db.query('''SELECT r.RoomNumber, r.Floor, r.Direction, t.BedSize, t.SmokingAllowed,
                               t.WheelchairAccessible, rr.BookedNightlyRate
                        FROM ReservedRoom rr
                        JOIN Room r ON r.RoomID = rr.RoomID
                        JOIN RoomType t ON t.TypeID = r.TypeID
                        WHERE rr.ReservationID=%s ORDER BY r.RoomNumber''', (res_id,))
    room_total = Decimal('0')
    for room in rooms:
        room['Subtotal'] = room['BookedNightlyRate'] * res['Nights']
        room_total += room['Subtotal']

    feature_rows = db.query('''SELECT f.FeatureName
                               FROM HotelNearbyFeature hf JOIN NearbyFeature f ON f.FeatureID = hf.FeatureID
                               WHERE hf.HotelID=%s ORDER BY f.FeatureName''', (res['HotelID'],))
    amenities = db.query('''SELECT a.AmenityName, ha.Price
                            FROM HotelAmenity ha JOIN Amenity a ON a.AmenityID = ha.AmenityID
                            WHERE ha.HotelID=%s ORDER BY a.AmenityName''', (res['HotelID'],))
    conference = db.query('SELECT Name, Capacity FROM ConferenceRoom WHERE HotelID=%s ORDER BY Name',
                          (res['HotelID'],))
    return {'res': res, 'rooms': rooms, 'room_total': room_total,
            'features': [f['FeatureName'] for f in feature_rows],
            'amenities': amenities, 'conference': conference,
            'charges': charges.get_charges_for_reservation(res_id)}
