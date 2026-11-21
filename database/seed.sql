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