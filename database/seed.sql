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