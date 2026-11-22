USE myHotel;

-- =====================================
-- 1. Nearby Features
-- =====================================

INSERT INTO NearbyFeature (FeatureID, FeatureName)
VALUES
(1, 'Ocean'),
(2, 'Mountain'),
(3, 'Lake'),
(4, 'River');


-- =====================================
-- 2. Amenities
-- =====================================

INSERT INTO Amenity (AmenityID, AmenityName)
VALUES
(1, 'WiFi'),
(2, 'Parking'),
(3, 'Pool'),
(4, 'Breakfast'),
(5, 'Spa');


-- =====================================
-- 3. Hotels (fictional test data)
-- =====================================

INSERT INTO Hotel
(HotelID, Name, Street, City, State,
 PostalCode, Rating, TimeZone, CheckInTime)
VALUES
(1, 'MyHotel San Diego Beach',
 '100 Ocean View Ave', 'San Diego', 'CA',
 '92101', 4, 'America/Los_Angeles', '15:00:00'),

(2, 'MyHotel San Diego Central',
 '200 Central St', 'San Diego', 'CA',
 '92102', 3, 'America/Los_Angeles', '15:00:00'),

(3, 'MyHotel Denver Heights',
 '300 Mountain Rd', 'Denver', 'CO',
 '80201', 5, 'America/Denver', '16:00:00'),

(4, 'MyHotel Chicago River',
 '400 River St', 'Chicago', 'IL',
 '60601', 4, 'America/Chicago', '15:00:00');


-- =====================================
-- 4. Hotel Nearby Features
-- =====================================

INSERT INTO HotelNearbyFeature (HotelID, FeatureID)
VALUES
(1, 1),
(3, 2),
(4, 3),
(4, 4);


-- =====================================
-- 5. Hotel Amenities
-- Price = 0 means free
-- =====================================

INSERT INTO HotelAmenity (HotelID, AmenityID, Price)
VALUES
(1, 1, 0.00),
(1, 2, 25.00),
(1, 3, 15.00),

(2, 1, 0.00),
(2, 2, 18.00),

(3, 1, 0.00),
(3, 5, 80.00),
(3, 4, 20.00),

(4, 1, 0.00),
(4, 4, 25.00);


-- =====================================
-- 6. Conference Rooms
-- =====================================

INSERT INTO ConferenceRoom (HotelID, Name, Capacity)
VALUES
(1, 'Pacific Hall', 80),
(3, 'Summit Hall', 120),
(4, 'Lakeside Room', 40);


-- =====================================
-- 7. Room Types
-- =====================================

INSERT INTO RoomType
(TypeID, BedSize, SmokingAllowed, WheelchairAccessible)
VALUES
(1, 'King',   0, 0),
(2, 'King',   0, 1),
(3, 'Queen',  0, 0),
(4, 'Queen',  0, 1),
(5, 'Double', 0, 0),
(6, 'Double', 0, 1),
(7, 'King',   1, 0),
(8, 'Queen',  1, 0),
(9, 'Double', 1, 0);


-- =====================================
-- 8. Hotel-Specific Room Rates
-- =====================================

INSERT INTO HotelRoomRate
(HotelID, TypeID, NightlyRate)
VALUES
-- San Diego Beach
(1, 1, 220.00),
(1, 2, 240.00),
(1, 3, 180.00),
(1, 5, 160.00),
(1, 7, 225.00),

-- San Diego Central
(2, 1, 165.00),
(2, 3, 145.00),
(2, 4, 155.00),
(2, 5, 125.00),
(2, 8, 155.00),

-- Denver Heights
(3, 1, 260.00),
(3, 2, 280.00),
(3, 3, 220.00),
(3, 6, 195.00),
(3, 7, 275.00),

-- Chicago River
(4, 1, 210.00),
(4, 3, 190.00),
(4, 4, 205.00),
(4, 5, 170.00),
(4, 9, 180.00);


-- =====================================
-- 9. Physical Rooms
-- =====================================

INSERT INTO Room
(HotelID, RoomNumber, TypeID, Floor, Direction, IsActive)
VALUES
-- San Diego Beach
(1, '101', 1, 1, 'North', 1),
(1, '102', 2, 1, 'South', 1),
(1, '103', 3, 1, 'East', 1),
(1, '104', 5, 1, 'West', 1),
(1, '201', 7, 2, 'North-East', 1),
(1, '202', 1, 2, 'South-West', 1),

-- San Diego Central
(2, '101', 1, 1, 'North', 1),
(2, '102', 3, 1, 'South', 1),
(2, '103', 4, 1, 'East', 1),
(2, '104', 5, 1, 'West', 1),
(2, '201', 8, 2, 'North-East', 1),
(2, '202', 3, 2, 'South-West', 0),

-- Denver Heights
(3, '301', 1, 3, 'North', 1),
(3, '302', 2, 3, 'South', 1),
(3, '303', 3, 3, 'East', 1),
(3, '304', 6, 3, 'West', 1),
(3, '401', 7, 4, 'North-East', 1),
(3, '402', 1, 4, 'South-West', 1),

-- Chicago River
(4, '101', 1, 1, 'North', 1),
(4, '102', 3, 1, 'South', 1),
(4, '103', 4, 1, 'East', 1),
(4, '104', 5, 1, 'West', 1),
(4, '201', 9, 2, 'North-East', 1),
(4, '202', 3, 2, 'South-West', 1);

-- 10. People: guests and cardholders
INSERT INTO Person (PersonID, FullName, Phone, MailingAddress) VALUES
(1, 'Alice Anderson', '202-555-0101', '10 Maple St, San Diego, CA 92101'),
(2, 'Bob Baker', '202-555-0102', '20 Cedar St, Denver, CO 80201'),
(3, 'Carla Chen', '202-555-0103', '30 Pine St, San Diego, CA 92102'),
(4, 'David Diaz', '202-555-0104', '40 Oak St, Chicago, IL 60601'),
(5, 'Evelyn Evans', '202-555-0105', NULL);

-- 11. Fictional payment cards: NOT real financial information
INSERT INTO PaymentCard
(CardID, HolderPersonID, CardholderName, CardNumber, ExpMonth, ExpYear) VALUES
(1, 1, 'Alice Anderson', 'TEST-ALICE-0001', 12, 2030),
(2, 2, 'Bob Baker',     'TEST-BOB-0002',   11, 2030),
(3, 3, 'Carla Chen',    'TEST-CARLA-0003', 10, 2030),
(4, 4, 'David Diaz',    'TEST-DAVID-0004',  9, 2030),
(5, 5, 'Evelyn Evans',  'TEST-EVELYN-0005', 8, 2030);

-- 12. Reservations
-- ScheduledCheckInAtUTC is 3 PM Pacific => 23:00 UTC in November/December,
-- 4 PM Mountain => 23:00 UTC, 3 PM Central => 21:00 UTC.
-- Reservation 2 intentionally has Alice as guest, but Bob's card as payment.
INSERT INTO Reservation
(ReservationID, GuestPersonID, HotelID, CardID, BookedAtUTC,
 CheckInDate, CheckOutDate, ScheduledCheckInAtUTC,
 ActualCheckInAtUTC, CancelledAtUTC, Status) VALUES
(1, 1, 1, 1, '2026-11-12 15:00:00', '2026-11-24', '2026-11-27', '2026-11-24 23:00:00', NULL, NULL, 'Booked'),
(2, 1, 2, 2, '2026-11-14 14:00:00', '2026-12-02', '2026-12-04', '2026-12-02 23:00:00', NULL, NULL, 'Booked'),
(3, 1, 3, 1, '2026-11-16 13:00:00', '2026-11-28', '2026-12-01', '2026-11-28 23:00:00', NULL, NULL, 'Booked'),
(4, 1, 4, 1, '2026-11-18 13:00:00', '2026-12-10', '2026-12-12', '2026-12-10 21:00:00', NULL, NULL, 'Booked'),
(5, 2, 1, 2, '2026-11-15 15:00:00', '2026-11-24', '2026-11-27', '2026-11-24 23:00:00', NULL, NULL, 'Booked'),
(6, 2, 3, 2, '2026-11-17 12:00:00', '2026-11-20', '2026-11-23', '2026-11-20 23:00:00', '2026-11-20 23:05:00', NULL, 'CheckedIn'),
(7, 2, 2, 2, '2026-11-19 12:00:00', '2026-12-05', '2026-12-07', '2026-12-05 23:00:00', NULL, NULL, 'Booked'),
(8, 3, 2, 3, '2026-11-08 12:00:00', '2026-11-20', '2026-11-23', '2026-11-20 23:00:00', NULL, NULL, 'Booked'),
(9, 4, 4, 4, '2026-10-20 12:00:00', '2026-11-01', '2026-11-04', '2026-11-01 21:00:00', '2026-11-01 21:03:00', NULL, 'CheckedOut'),
(10,5, 3, 5, '2026-11-01 12:00:00', '2026-11-10', '2026-11-12', '2026-11-10 23:00:00', NULL, '2026-11-08 12:00:00', 'Cancelled'),
(11,3, 1, 3, '2026-11-18 12:00:00', '2026-11-22', '2026-11-24', '2026-11-22 23:00:00', NULL, '2026-11-21 18:00:00', 'Cancelled'),
(12,5, 1, 5, '2026-11-19 10:00:00', '2026-11-25', '2026-11-28', '2026-11-25 23:00:00', NULL, NULL, 'Booked'),
(13,4, 3, 4, '2026-11-10 13:00:00', '2026-11-18', '2026-11-20', '2026-11-18 23:00:00', NULL, NULL, 'NoShow');

-- 13. Rooms assigned to reservations; rates copied at booking time.
-- RoomIDs are based on the 24 rooms inserted in Stage B on a freshly reset DB.
INSERT INTO ReservedRoom (ReservationID, RoomID, BookedNightlyRate) VALUES
(1,  1, 220.00), -- San Diego Beach 101, King, 3 nights
(1,  3, 180.00), -- San Diego Beach 103, Queen, 3 nights
(2,  7, 165.00), -- San Diego Central 101, King, 2 nights
(3, 13, 260.00), -- Denver Heights 301, King, 3 nights
(4, 19, 210.00), -- Chicago River 101, King, 2 nights
(5,  2, 240.00), -- San Diego Beach 102, accessible King, 3 nights
(6, 16, 195.00), -- Denver Heights 304, accessible Double, 3 nights
(7,  9, 155.00), -- San Diego Central 103, accessible Queen, 2 nights
(8,  8, 145.00), -- San Diego Central 102, Queen, 3 nights; missed check-in
(9, 20, 190.00), -- Chicago River 102, Queen, 3 nights; checked out
(10,14, 280.00), -- Denver Heights 302, cancelled early; no fee
(11, 4, 160.00), -- San Diego Beach 104, cancelled late; 20% of 160 = 32
(12, 6, 220.00), -- San Diego Beach 202, King, 3 nights
(13,17, 275.00); -- Denver Heights 401, no-show; 20% of 275 = 55

-- 14. Itemized, simulated charges; same payment card as each reservation.
-- Prepaid room charges on future reservations happen when booked.
INSERT INTO Charge
(ReservationID, AmenityID, ChargeType, Amount, ChargedAtUTC, Description) VALUES
(1, NULL, 'Room', 660.00, '2026-11-12 15:05:00', 'Room 101: 3 nights at $220'),
(1, NULL, 'Room', 540.00, '2026-11-12 15:05:00', 'Room 103: 3 nights at $180'),
(2, NULL, 'Room', 330.00, '2026-11-14 14:05:00', 'Room 101: 2 nights at $165'),
(3, NULL, 'Room', 780.00, '2026-11-16 13:05:00', 'Room 301: 3 nights at $260'),
(4, NULL, 'Room', 420.00, '2026-11-18 13:05:00', 'Room 101: 2 nights at $210'),
(5, NULL, 'Room', 720.00, '2026-11-15 15:05:00', 'Room 102: 3 nights at $240'),
(6, NULL, 'Room', 585.00, '2026-11-20 23:10:00', 'Room 304: 3 nights at $195'),
(6, 5, 'Amenity', 80.00, '2026-11-21 10:00:00', 'Spa usage at Denver Heights'),
(6, NULL, 'Food', 27.00, '2026-11-21 12:00:00', 'Restaurant meal'),
(7, NULL, 'Room', 310.00, '2026-11-19 12:05:00', 'Room 103: 2 nights at $155'),
(9, NULL, 'Room', 570.00, '2026-11-04 17:00:00', 'Room 102: 3 nights at $190'),
(9, 4, 'Amenity', 25.00, '2026-11-02 15:00:00', 'Breakfast at Chicago River'),
(9, NULL, 'Food', 35.00, '2026-11-03 19:00:00', 'Restaurant dinner'),
(11,NULL, 'Cancellation', 32.00, '2026-11-21 18:00:00', 'Late cancellation: 20% of first-night rate $160'),
(12,NULL, 'Room', 660.00, '2026-11-19 10:05:00', 'Room 202: 3 nights at $220'),
(13,NULL, 'Cancellation', 55.00, '2026-11-19 00:00:00', 'No-show penalty: 20% of first-night rate $275');

-- 15. One bonus per person per calendar booking year.
-- Assumption: 3+ non-cancelled reservations, counted across hotels.
-- Alice has 4, Bob has exactly 3; this exercises the 3-versus-4 ambiguity.
INSERT INTO BonusAward
(PersonID, BookingYear, AwardedAtUTC, MailedAtUTC, Status) VALUES
(1, 2026, '2026-11-18 14:00:00', NULL, 'Pending'),
(2, 2026, '2026-11-19 12:05:00', '2026-11-20 16:00:00', 'Mailed');
