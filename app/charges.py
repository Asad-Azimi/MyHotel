#charges.py: money charged to a reservation's credit card (room, food, amenity, cancellation)

from decimal import Decimal, InvalidOperation

from app import customers
from app import db

LATE_FEE_RATE = Decimal('0.20')                 # 20% of the first night
MANUAL_TYPES = ('Room', 'Food')                 # additional non-amenitycharge types, amenities use add_amenity_charge


def parse_amount(value):
    try:
        amount = Decimal(str(value).strip().lstrip('$').replace(',', ''))
        if not amount.is_finite():
            raise InvalidOperation
    except InvalidOperation:
        raise ValueError('Amount must be a number.')
    if amount <= 0:
        raise ValueError('Amount must be greater than zero.')
    return amount.quantize(Decimal('0.01'))


def _description(value, label='Description', required=True):
    value = ' '.join((value or '').split())
    if required and not value:
        raise ValueError('%s is required.' % label)
    if len(value) > 255:
        raise ValueError('%s must be 255 characters or fewer.' % label)
    return value


# helpers for reservations.py
#they they join the caller's transaction by taking the caller's cursor

def first_night_fee(cur, res_id):
    #20% of the first night's rate, summed over every room on the reservation
    cur.execute('SELECT SUM(BookedNightlyRate) AS s FROM ReservedRoom WHERE ReservationID=%s', (res_id,))
    total = cur.fetchone()['s'] or Decimal('0')
    return (total * LATE_FEE_RATE).quantize(Decimal('0.01'))


def add_cancellation_charge(cur, res_id, amount, description):
    cur.execute('''INSERT INTO Charge (ReservationID, ChargeType, Amount, ChargedAtUTC, Description)
                   VALUES (%s,'Cancellation',%s,UTC_TIMESTAMP(),%s)''', (res_id, amount, description))


# insert charges

def _open_reservation(cur, res_id):
    cur.execute('SELECT Status, DATEDIFF(CheckOutDate, CheckInDate) AS Nights '
                'FROM Reservation WHERE ReservationID=%s', (res_id,))
    res = cur.fetchone()
    if not res:
        raise ValueError('No reservation with ID %s.' % res_id)
    if res['Status'] in ('Cancelled', 'NoShow'):
        raise ValueError('Cannot add charges to a %s reservation.' % res['Status'].lower())
    return res


def add_charge(res_id, charge_type, amount, description=None):
    #add a Room or Food charge, returns the charge ID
    charge_type = (charge_type or '').strip().capitalize()
    if charge_type not in MANUAL_TYPES:
        raise ValueError('Charge type must be Room or Food (use the amenity option for amenities).')
    amount = parse_amount(amount)
    description = _description(description, required=(charge_type == 'Food')) or 'Room charge'
    with db.transaction() as cur:
        _open_reservation(cur, res_id)
        cur.execute('''INSERT INTO Charge (ReservationID, ChargeType, Amount, ChargedAtUTC, Description)
                       VALUES (%s,%s,%s,UTC_TIMESTAMP(),%s)''', (res_id, charge_type, amount, description))
        return cur.lastrowid


def paid_amenities(res_id):
    #amenities at the reservation's hotel that are not free
    return db.query('''SELECT a.AmenityID, a.AmenityName, ha.Price
                       FROM Reservation res
                       JOIN HotelAmenity ha ON ha.HotelID = res.HotelID
                       JOIN Amenity a ON a.AmenityID = ha.AmenityID
                       WHERE res.ReservationID=%s AND ha.Price > 0
                       ORDER BY a.AmenityName''', (res_id,))


def add_amenity_charge(res_id, amenity_id, quantity=1):
    #charge a paid amenity at the price this hotel lists for it, returns (charge_id, amount)
    try:
        amenity_id, quantity = int(amenity_id), int(quantity)
    except (TypeError, ValueError):
        raise ValueError('Amenity ID and quantity must be whole numbers.')
    if quantity < 1:
        raise ValueError('Quantity must be at least 1.')
    with db.transaction() as cur:
        _open_reservation(cur, res_id)
        cur.execute('''SELECT a.AmenityName, ha.Price FROM Reservation res
                       JOIN HotelAmenity ha ON ha.HotelID = res.HotelID
                       JOIN Amenity a ON a.AmenityID = ha.AmenityID
                       WHERE res.ReservationID=%s AND a.AmenityID=%s''', (res_id, amenity_id))
        row = cur.fetchone()
        if not row:
            raise ValueError("That amenity is not offered at this reservation's hotel.")
        if row['Price'] <= 0:
            raise ValueError('That amenity is free; there is nothing to charge.')
        amount = (row['Price'] * quantity).quantize(Decimal('0.01'))
        description = row['AmenityName'] + (' x%d' % quantity if quantity > 1 else '')
        cur.execute('''INSERT INTO Charge (ReservationID, AmenityID, ChargeType, Amount, ChargedAtUTC, Description)
                       VALUES (%s,%s,'Amenity',%s,UTC_TIMESTAMP(),%s)''',
                    (res_id, amenity_id, amount, description))
        return cur.lastrowid, amount


def post_room_charges(res_id):
    #adds the cost of a stay to a reservation's charges
    with db.transaction() as cur:
        res = _open_reservation(cur, res_id)
        cur.execute("SELECT COUNT(*) AS n FROM Charge WHERE ReservationID=%s AND ChargeType='Room'", (res_id,))
        if cur.fetchone()['n']:
            raise ValueError('Room charges were already posted for this reservation.')
        cur.execute('SELECT SUM(BookedNightlyRate) AS s FROM ReservedRoom WHERE ReservationID=%s', (res_id,))
        nightly = cur.fetchone()['s']
        if not nightly:
            raise ValueError('This reservation has no rooms to charge.')
        total = (Decimal(nightly) * res['Nights']).quantize(Decimal('0.01'))
        cur.execute('''INSERT INTO Charge (ReservationID, ChargeType, Amount, ChargedAtUTC, Description)
                       VALUES (%s,'Room',%s,UTC_TIMESTAMP(),%s)''',
                    (res_id, total, 'Room charges: %d night%s' % (res['Nights'], '' if res['Nights'] == 1 else 's')))
        return total


# update / delete charges

def update_charge(charge_id, amount, description):
    amount, description = parse_amount(amount), _description(description)
    if not db.query('SELECT 1 FROM Charge WHERE ChargeID=%s', (charge_id,)):
        raise ValueError('No charge with ID %s.' % charge_id)
    db.execute('UPDATE Charge SET Amount=%s, Description=%s WHERE ChargeID=%s', (amount, description, charge_id))


def get_charge(charge_id):
    rows = db.query('SELECT * FROM Charge WHERE ChargeID=%s', (charge_id,))
    if not rows:
        raise ValueError('No charge with ID %s.' % charge_id)
    return rows[0]


def delete_charge(charge_id):
    get_charge(charge_id)
    db.execute('DELETE FROM Charge WHERE ChargeID=%s', (charge_id,))


# query 5

_CHARGE_COLUMNS = '''c.ChargeID, c.ChargedAtUTC, c.ChargeType, c.Description, c.Amount, c.ReservationID,
                     h.Name AS Hotel, pc.CardholderName, RIGHT(pc.CardNumber, 4) AS Last4'''
_CHARGE_JOINS = '''FROM Charge c
                   JOIN Reservation res ON res.ReservationID = c.ReservationID
                   JOIN Hotel h ON h.HotelID = res.HotelID
                   JOIN PaymentCard pc ON pc.CardID = res.CardID'''


def get_charges_for_reservation(res_id):
    return db.query('SELECT %s %s WHERE c.ReservationID=%%s ORDER BY c.ChargedAtUTC, c.ChargeID'
                    % (_CHARGE_COLUMNS, _CHARGE_JOINS), (res_id,))


def get_charges_for_person(name, phone):
    # query 5
    person = customers.require_person(name, phone)
    return db.query('''SELECT %s %s
                       WHERE res.CardID IN (SELECT CardID FROM Reservation WHERE GuestPersonID=%%s
                                            UNION SELECT CardID FROM PaymentCard WHERE HolderPersonID=%%s)
                       ORDER BY c.ChargedAtUTC, c.ChargeID''' % (_CHARGE_COLUMNS, _CHARGE_JOINS),
                    (person['PersonID'], person['PersonID']))


def total(charges):
    return sum((c['Amount'] for c in charges), Decimal('0.00'))
