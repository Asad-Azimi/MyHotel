#customers.py: customers, payment cards, and the frequent-customer bonus (BonusAward)

import re
from datetime import date, datetime, timezone

import db

BONUS_MIN_RESERVATIONS = 3

# cleaning up inputs

def _text(value, label, max_len):
    value = ' '.join((value or '').split())
    if not value:
        raise ValueError('%s is required.' % label)
    if len(value) > max_len:
        raise ValueError('%s must be %d characters or fewer.' % (label, max_len))
    return value


def clean_name(name):
    return _text(name, 'Name', 150)


def clean_address(address, required=True):
    # the address is needed to mail the bonus, so it is required for guests
    address = ' '.join((address or '').split())
    if not address:
        if required:
            raise ValueError('Mailing address is required.')
        return None
    if len(address) > 255:
        raise ValueError('Mailing address must be 255 characters or fewer.')
    return address


def clean_phone(phone):
    phone = re.sub(r'[\s().-]', '', phone or '')
    if not (phone.isdigit() and len(phone) == 10):
        raise ValueError('Phone must be 10 digits.')
    return phone


def clean_person(name, phone, address, require_address=True):
    return clean_name(name), clean_phone(phone), clean_address(address, require_address)


def clean_card(number, exp_month, exp_year):
    # reservation cannot be made without card number
    number = re.sub(r'[\s-]', '', number or '')
    if not number:
        raise ValueError('A credit card number is required to make a reservation.')
    if not number.isdigit() or not 13 <= len(number) <= 19:
        raise ValueError('Card number must be 13 to 19 digits.')
    try:
        month, year = int(exp_month), int(exp_year)
    except (TypeError, ValueError):
        raise ValueError('Expiration month and year must be numbers.')
    if year < 100:
        year += 2000
    if not 1 <= month <= 12:
        raise ValueError('Expiration month must be 1 to 12.')
    return number, month, year


# insert/list/update/delete customers

def get_or_create_person(cur, name, phone, address, require_address=True):
    #reuse the person if name + phone already exist (updating a changed address), else insert
    #returns (person_id, created)
    name, phone, address = clean_person(name, phone, address, require_address)
    cur.execute('''SELECT PersonID, MailingAddress FROM Person
                   WHERE FullName=%s AND Phone=%s ORDER BY PersonID LIMIT 1 FOR UPDATE''', (name, phone))
    row = cur.fetchone()
    if row:
        if address and row['MailingAddress'] != address:
            cur.execute('UPDATE Person SET MailingAddress=%s WHERE PersonID=%s', (address, row['PersonID']))
        return row['PersonID'], False
    cur.execute('INSERT INTO Person (FullName, Phone, MailingAddress) VALUES (%s,%s,%s)',
                (name, phone, address))
    return cur.lastrowid, True


def add_person(name, phone, address):
    with db.transaction() as cur:
        return get_or_create_person(cur, name, phone, address)

# check if customer already exists
def find_person(name, phone):
    rows = db.query('SELECT * FROM Person WHERE FullName=%s AND Phone=%s ORDER BY PersonID LIMIT 1',
                    (clean_name(name), clean_phone(phone)))
    return rows[0] if rows else None

# used for query 4, 5, card list to ensure customer exists
def require_person(name, phone):
    person = find_person(name, phone)
    if not person:
        raise ValueError('No customer found with that name and phone number.')
    return person


# find person from ID 
def get_person(person_id):
    rows = db.query('SELECT * FROM Person WHERE PersonID=%s', (person_id,))
    if not rows:
        raise ValueError('No customer with ID %s.' % person_id)
    return rows[0]

# list all customers
def list_persons():
    return db.query('SELECT * FROM Person ORDER BY FullName')


def update_person(person_id, name, phone, address):
    name, phone, address = clean_person(name, phone, address)
    get_person(person_id)
    if db.query('SELECT 1 FROM Person WHERE FullName=%s AND Phone=%s AND PersonID<>%s',
                (name, phone, person_id)):
        raise ValueError('Another customer already has that name and phone number.')
    db.execute('UPDATE Person SET FullName=%s, Phone=%s, MailingAddress=%s WHERE PersonID=%s',
               (name, phone, address, person_id))


def delete_person(person_id):
    #nothing deleted if the customer is a guest on a reservation or holds a card used by one
    #unused cards they hold and their bonus records are removed with them
    get_person(person_id)
    with db.transaction() as cur:
        cur.execute('DELETE FROM BonusAward WHERE PersonID=%s', (person_id,))
        cur.execute('''DELETE FROM PaymentCard WHERE HolderPersonID=%s
                       AND CardID NOT IN (SELECT CardID FROM Reservation)''', (person_id,))
        cur.execute('DELETE FROM Person WHERE PersonID=%s', (person_id,))


# insert/list/update/delete payment cards

def get_or_create_card(cur, holder_person_id, holder_name, number, exp_month, exp_year):
    #reuse the card if number + expiration already exist, else insert it
    #the holder is a Person row and may differ from the guest.
    #returns card_id
    number, month, year = clean_card(number, exp_month, exp_year)
    cur.execute('SELECT CardID FROM PaymentCard WHERE CardNumber=%s AND ExpMonth=%s AND ExpYear=%s LIMIT 1',
                (number, month, year))
    row = cur.fetchone()
    if row:
        return row['CardID']
    cur.execute('''INSERT INTO PaymentCard (HolderPersonID, CardholderName, CardNumber, ExpMonth, ExpYear)
                   VALUES (%s,%s,%s,%s,%s)''',
                (holder_person_id, _text(holder_name, 'Card holder name', 150), number, month, year))
    return cur.lastrowid


def get_card(card_id):
    rows = db.query('''SELECT CardID, HolderPersonID, CardholderName, RIGHT(CardNumber, 4) AS Last4,
                              ExpMonth, ExpYear FROM PaymentCard WHERE CardID=%s''', (card_id,))
    if not rows:
        raise ValueError('No card with ID %s.' % card_id)
    return rows[0]


def list_cards_for_person(person_id):
    return db.query('''SELECT CardID, CardholderName, RIGHT(CardNumber, 4) AS Last4, ExpMonth, ExpYear
                       FROM PaymentCard
                       WHERE HolderPersonID=%s
                          OR CardID IN (SELECT CardID FROM Reservation WHERE GuestPersonID=%s)
                       ORDER BY CardID''', (person_id, person_id))


def update_card(card_id, holder_name, exp_month, exp_year):
    #change the holder's name and/or the expiration date.
    get_card(card_id)
    holder_name = _text(holder_name, 'Card holder name', 150)
    try:
        month, year = int(exp_month), int(exp_year)
    except (TypeError, ValueError):
        raise ValueError('Expiration month and year must be numbers.')
    if year < 100:
        year += 2000
    if not 1 <= month <= 12:
        raise ValueError('Expiration month must be 1 to 12.')
    today = date.today()
    if (year, month) < (today.year, today.month):
        raise ValueError('That expiration date is in the past.')
    db.execute('UPDATE PaymentCard SET CardholderName=%s, ExpMonth=%s, ExpYear=%s WHERE CardID=%s',
               (holder_name, month, year, card_id))


def delete_card(card_id):
    """Blocked if a reservation uses the card."""
    get_card(card_id)
    db.execute('DELETE FROM PaymentCard WHERE CardID=%s', (card_id,))


# query 7

def _utc_year():
    return datetime.now(timezone.utc).year


def count_reservations(person_id, year=None):
    #reservations this customer booked in year (default: this year), not counting cancelled ones
    return db.query('''SELECT COUNT(*) AS n FROM Reservation
                       WHERE GuestPersonID=%s AND YEAR(BookedAtUTC)=%s AND Status <> 'Cancelled' ''',
                    (person_id, year or _utc_year()))[0]['n']


def reservation_counts(year=None):
    #how many reservations each customer made in a year
    return db.query('''SELECT p.PersonID, p.FullName, p.Phone, COUNT(*) AS Reservations
                       FROM Reservation res JOIN Person p ON p.PersonID = res.GuestPersonID
                       WHERE YEAR(res.BookedAtUTC)=%s AND res.Status <> 'Cancelled'
                       GROUP BY p.PersonID, p.FullName, p.Phone
                       ORDER BY Reservations DESC, p.FullName''', (year or _utc_year(),))


def check_bonus(person_id, year=None):
    #call after every booking
    year = year or _utc_year()
    if count_reservations(person_id, year) >= BONUS_MIN_RESERVATIONS:
        db.execute('''INSERT IGNORE INTO BonusAward (PersonID, BookingYear, AwardedAtUTC)
                      VALUES (%s,%s,UTC_TIMESTAMP())''', (person_id, year))
        return True
    return False


def list_bonus_awards(year=None, pending_only=False):
    #name and the address the bonus is mailed to
    sql = '''SELECT b.PersonID, b.BookingYear, b.Status, p.FullName, p.Phone, p.MailingAddress
             FROM BonusAward b JOIN Person p ON p.PersonID = b.PersonID WHERE 1=1'''
    args = []
    if year:
        sql += ' AND b.BookingYear=%s'
        args.append(int(year))
    if pending_only:
        sql += " AND b.Status='Pending'"
    return db.query(sql + ' ORDER BY b.BookingYear DESC, p.FullName', args)


def mark_bonus_mailed(person_id, year):
    with db.transaction() as cur:
        cur.execute('''UPDATE BonusAward SET Status='Mailed', MailedAtUTC=UTC_TIMESTAMP()
                       WHERE PersonID=%s AND BookingYear=%s AND Status='Pending' ''', (person_id, year))
        if cur.rowcount == 0:
            raise ValueError('No pending bonus for that customer and year.')
