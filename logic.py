
"""Database layer: every SQL query in the project lives in this file.

Front-ends uses view.py  (web app, Flask)

"""

import pymysql

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo


class BookingError(ValueError):
    """A business-rule problem; the message is safe to show to the user."""



def to_date(value):
        return value if isinstance(value, date) else date.fromisoformat(value)


def _fix_hotel(h):
    """pymysql returns TIME columns as timedelta; turn it into 'HH:MM'."""
    if h and isinstance(h.get('CheckInTime'), timedelta):
        h['CheckInTime'] = (datetime.min + h['CheckInTime']).strftime('%H:%M')
    return h


class Database(object):
    """Database object to handle all DB operations"""

    def __init__(self, opts):
        """Initialize and connect to the database"""
        self.opts = opts
        self.__connect()

    def __connect(self):
        """Establish the MySQL connection"""
        self.conn = pymysql.connect(
            host=self.opts.DB_HOST,
            user=self.opts.DB_USER,
            password=self.opts.DB_PASSWORD,
            database=self.opts.DB_NAME
        )

    def close(self):
        """Close the connection when the program ends"""
        self.conn.close()

    
    # --- Helpers ----

    # Helper for read operations
    def _q(self, sql, args=()):
        """Run a SELECT, return all rows (list of dicts)."""
        self.conn.ping(reconnect=True)
        with self.conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchall()
        
    # Helper for inserts / updates / deletes (changing database)
    def _x(self, sql, args=()):
        """Run a single INSERT/UPDATE/DELETE (autocommit), return lastrowid."""
        self.conn.ping(reconnect=True)
        with self.conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.lastrowid
    
    # Helper for multi-line sql statements to ensure that if one fails, none will be executed
    def _tx(self):
        """Transaction: everything inside commits together or rolls back."""
        self.conn.ping(reconnect=True)
        self.conn.begin()
        cur = self.conn.cursor()
        try:
            yield cur
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    # ---------- Read operations ----------

    def get_hotels(self):
        return [_fix_hotel(h) for h in self._q('SELECT * FROM Hotel ORDER BY City, Name')]

    def get_hotel(self, hotel_id):
        rows = self._q('SELECT * FROM Hotel WHERE HotelID=%s', (hotel_id,))
        return _fix_hotel(rows[0]) if rows else None

    def get_cities(self):
        return [r['City'] for r in self._q('SELECT DISTINCT City FROM Hotel ORDER BY City')]

    def get_room_types(self):
        return self._q('SELECT * FROM RoomType ORDER BY TypeID')

    def get_features(self):
        return [r['FeatureName'] for r in self._q('SELECT FeatureName FROM NearbyFeatures ORDER BY FeatureName')]

    def get_amenities(self):
        return [r['AmenityName'] for r in self._q('SELECT AmenityName FROM Amenities ORDER BY AmenityName')]

    def get_hotel_features(self, hotel_id):
        return [r['FeatureName'] for r in self._q(
            'SELECT FeatureName FROM HotelNearbyFeatures WHERE HotelID=%s ORDER BY FeatureName', (hotel_id,))]

    def get_hotel_amenities(self, hotel_id):
        return self._q('SELECT AmenityName, Price FROM HotelAmenities WHERE HotelID=%s ORDER BY AmenityName',
                       (hotel_id,))

    def get_conference_rooms(self, hotel_id):
        return self._q('SELECT * FROM ConferenceRoom WHERE HotelID=%s ORDER BY ConferenceRoomID', (hotel_id,))

    def get_hotel_rates(self, hotel_id):
        return self._q('''SELECT hr.TypeID, hr.NightlyRate, t.BedSize, t.SmokingAllowed, t.WheelchairAccessible
                          FROM HotelRoomRate hr JOIN RoomType t ON t.TypeID = hr.TypeID
                          WHERE hr.HotelID=%s ORDER BY hr.TypeID''', (hotel_id,))

    def get_hotel_rooms(self, hotel_id):
        return self._q('''SELECT r.RoomID, r.RoomNumber, r.TypeID, r.Floor, r.Direction, r.isActive,
                                 t.BedSize, t.SmokingAllowed, t.WheelchairAccessible, hr.NightlyRate
                          FROM Room r
                          JOIN RoomType t ON t.TypeID = r.TypeID
                          JOIN HotelRoomRate hr ON hr.HotelID = r.HotelID AND hr.TypeID = r.TypeID
                          WHERE r.HotelID=%s ORDER BY r.RoomNumber''', (hotel_id,))

    def get_rooms_by_ids(self, hotel_id, room_ids):
        room_ids = sorted(set(room_ids))
        marks = ','.join(['%s'] * len(room_ids))
        return self._q(f'''SELECT r.RoomID, r.RoomNumber, r.Floor, r.Direction, h.Name AS HotelName,
                                  t.BedSize, t.SmokingAllowed, t.WheelchairAccessible, hr.NightlyRate
                           FROM Room r
                           JOIN Hotel h ON h.HotelID = r.HotelID
                           JOIN RoomType t ON t.TypeID = r.TypeID
                           JOIN HotelRoomRate hr ON hr.HotelID = r.HotelID AND hr.TypeID = r.TypeID
                           WHERE r.HotelID=%s AND r.RoomID IN ({marks}) ORDER BY r.RoomNumber''',
                       [hotel_id, *room_ids])

    # ---------- Write operations ----------

    # ================= hotel =================

    def add_hotel(self, name, street, city, state, postal, rating, tz, checkin):
        return self._x('''INSERT INTO Hotel (Name, Street, City, State, PostalCode, Rating, TimeZone, CheckInTime)
                          VALUES (%s,%s,%s,%s,%s,%s,%s,%s)''',
                       (name, street, city, state, postal, rating, tz, checkin))

    def update_hotel(self, hotel_id, name, street, city, state, postal, rating, tz, checkin):
        self._x('''UPDATE Hotel SET Name=%s, Street=%s, City=%s, State=%s, PostalCode=%s,
                          Rating=%s, TimeZone=%s, CheckInTime=%s WHERE HotelID=%s''',
                (name, street, city, state, postal, rating, tz, checkin, hotel_id))

    def delete_hotel(self, hotel_id):
        """Deletes the hotel and its child rows. Fails (and rolls back) if reservations exist."""
        with self._tx() as cur:
            for table in ('HotelNearbyFeatures', 'HotelAmenities', 'ConferenceRoom', 'Room', 'HotelRoomRate'):
                cur.execute(f'DELETE FROM {table} WHERE HotelID=%s', (hotel_id,))
            cur.execute('DELETE FROM Hotel WHERE HotelID=%s', (hotel_id,))

    # ---------- features / amenities ----------

    def add_feature(self, name):
        self._x('INSERT INTO NearbyFeatures (FeatureName) VALUES (%s)', (name,))

    def delete_feature(self, name):
        with self._tx() as cur:
            cur.execute('DELETE FROM HotelNearbyFeatures WHERE FeatureName=%s', (name,))
            cur.execute('DELETE FROM NearbyFeatures WHERE FeatureName=%s', (name,))

    def add_amenity(self, name):
        self._x('INSERT INTO Amenities (AmenityName) VALUES (%s)', (name,))

    def delete_amenity(self, name):
        with self._tx() as cur:
            cur.execute('DELETE FROM HotelAmenities WHERE AmenityName=%s', (name,))
            cur.execute('DELETE FROM Amenities WHERE AmenityName=%s', (name,))

    def assign_feature(self, hotel_id, feature):
        self._x('INSERT IGNORE INTO HotelNearbyFeatures (HotelID, FeatureName) VALUES (%s,%s)',
                (hotel_id, feature))

    def unassign_feature(self, hotel_id, feature):
        self._x('DELETE FROM HotelNearbyFeatures WHERE HotelID=%s AND FeatureName=%s', (hotel_id, feature))

    def set_amenity(self, hotel_id, amenity, price):
        """price None = free."""
        self._x('''INSERT INTO HotelAmenities (HotelID, AmenityName, Price) VALUES (%s,%s,%s)
                   ON DUPLICATE KEY UPDATE Price=%s''', (hotel_id, amenity, price, price))

    def remove_amenity(self, hotel_id, amenity):
        self._x('DELETE FROM HotelAmenities WHERE HotelID=%s AND AmenityName=%s', (hotel_id, amenity))

    # ---------- conference rooms ----------

    def add_conference(self, hotel_id, capacity):
        self._x('INSERT INTO ConferenceRoom (HotelID, Capacity) VALUES (%s,%s)', (hotel_id, capacity))

    def update_conference(self, conf_id, capacity):
        self._x('UPDATE ConferenceRoom SET Capacity=%s WHERE ConferenceRoomID=%s', (capacity, conf_id))

    def delete_conference(self, conf_id):
        self._x('DELETE FROM ConferenceRoom WHERE ConferenceRoomID=%s', (conf_id,))

    # ---------- rates and rooms ----------

    def set_rate(self, hotel_id, type_id, rate):
        self._x('''INSERT INTO HotelRoomRate (HotelID, TypeID, NightlyRate) VALUES (%s,%s,%s)
                   ON DUPLICATE KEY UPDATE NightlyRate=%s''', (hotel_id, type_id, rate, rate))

    def delete_rate(self, hotel_id, type_id):
        self._x('DELETE FROM HotelRoomRate WHERE HotelID=%s AND TypeID=%s', (hotel_id, type_id))

    def add_room(self, hotel_id, number, type_id, floor, direction):
        self._x('''INSERT INTO Room (HotelID, RoomNumber, TypeID, Floor, Direction, isActive)
                   VALUES (%s,%s,%s,%s,%s,1)''', (hotel_id, number, type_id, floor, direction))

    def update_room(self, room_id, type_id, floor, direction, active):
        self._x('UPDATE Room SET TypeID=%s, Floor=%s, Direction=%s, isActive=%s WHERE RoomID=%s',
                (type_id, floor, direction, int(active), room_id))

    def delete_room(self, room_id):
        self._x('DELETE FROM Room WHERE RoomID=%s', (room_id,))

    # ---------- persons ----------

    def get_persons(self):
        return self._q('SELECT * FROM Person ORDER BY FullName')

    def add_person(self, name, phone, address):
        return self._x('INSERT INTO Person (FullName, Phone, MailingAddress) VALUES (%s,%s,%s)',
                       (name, phone, address))

    def update_person(self, person_id, name, phone, address):
        self._x('UPDATE Person SET FullName=%s, Phone=%s, MailingAddress=%s WHERE PersonID=%s',
                (name, phone, address, person_id))

    def delete_person(self, person_id):
        with self._tx() as cur:
            cur.execute('DELETE FROM FrequentCustomers WHERE PersonID=%s', (person_id,))
            cur.execute('DELETE FROM Person WHERE PersonID=%s', (person_id,))

    def get_frequent_customers(self):
        return self._q('''SELECT p.FullName, p.Phone, p.MailingAddress, f.`Year`
                          FROM FrequentCustomers f JOIN Person p ON p.PersonID = f.PersonID
                          ORDER BY f.`Year` DESC, p.FullName''')


    # ---------- reservations ----------

    # TODO

    # ---------- 8 required queries in project outline ----------
     
    # TODO

