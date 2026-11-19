-- ============================================
-- MyHotel Database Schema
-- ============================================

-- Drop and recreate database
DROP DATABASE IF EXISTS myHotel;
CREATE DATABASE myHotel;
USE myHotel;

-- ============================================
-- Hotels and their features
-- ============================================

CREATE TABLE Hotel (
    HotelID INT PRIMARY KEY AUTO_INCREMENT NOT NULL,
    Name VARCHAR(50) NOT NULL, 
    Street VARCHAR(50) NOT NULL,
    City VARCHAR(50) NOT NULL, 
    State VARCHAR(2) NOT NULL, 
    PostalCode VARCHAR(10) NOT NULL,
    Rating INT NOT NULL,
    TimeZone VARCHAR(40) NOT NULL,
    CheckInTime TIME NOT NULL,

    UNIQUE(Name, City),
    CONSTRAINT check_rating CHECK (Rating BETWEEN 1 AND 6)
);

CREATE TABLE NearbyFeatures (
    FeatureName VARCHAR(50) PRIMARY KEY NOT NULL

);

CREATE TABLE HotelNearbyFeatures (
    HotelID INT NOT NULL,
    FeatureName VARCHAR(50) NOT NULL,
    
    PRIMARY KEY (HotelID, FeatureName),
    FOREIGN KEY (HotelID) REFERENCES Hotel(HotelID),
    FOREIGN KEY (FeatureName) REFERENCES NearbyFeatures(FeatureName)

);

CREATE TABLE Amenities (
    AmenityName VARCHAR(50) PRIMARY KEY NOT NULL
);

CREATE TABLE HotelAmenities (
    HotelID INT NOT NULL,
    AmenityName VARCHAR(50) NOT NULL,
    Price DECIMAL(8, 2) NULL,
    
    PRIMARY KEY (HotelID, AmenityName),
    FOREIGN KEY (HotelID) REFERENCES Hotel(HotelID),
    FOREIGN KEY (AmenityName) REFERENCES Amenities(AmenityName)
);

-- ============================================
-- Rooms: room rates and room types
-- ============================================

CREATE TABLE ConferenceRoom (
    ConferenceRoomID INT PRIMARY KEY AUTO_INCREMENT NOT NULL,
    HotelID INT NOT NULL,
    Capacity INT NOT NULL,
    
    FOREIGN KEY (HotelID) REFERENCES Hotel(HotelID)
);

CREATE TABLE RoomType (
    TypeID INT PRIMARY KEY AUTO_INCREMENT NOT NULL,
    BedSize VARCHAR(20) NOT NULL,
    SmokingAllowed BOOLEAN NOT NULL,
    WheelchairAccessible BOOLEAN NOT NULL,

    UNIQUE (BedSize, SmokingAllowed, WheelchairAccessible)
);

CREATE TABLE HotelRoomRate (
    HotelID INT NOT NULL,
    TypeID INT NOT NULL,
    NightlyRate DECIMAL (8, 2) NOT NULL,
    
    PRIMARY KEY (HotelID, TypeID),
    FOREIGN KEY (HotelID) REFERENCES Hotel(HotelID),
    FOREIGN KEY (TypeID) REFERENCES RoomType(TypeID)
);

CREATE TABLE Room (
    RoomID INT PRIMARY KEY AUTO_INCREMENT NOT NULL, 
    HotelID INT NOT NULL, 
    RoomNumber INT NOT NULL,
    TypeID INT NOT NULL, 
    Floor INT NOT NULL,
    Direction ENUM('South', 'North', 'East', 'West', 'North-East', 'South-East', 'North-West', 'South-West') NOT NULL, 
    isActive BOOLEAN NOT NULL DEFAULT TRUE,

    UNIQUE (HotelID, RoomNumber),
    FOREIGN KEY (HotelID, TypeID) REFERENCES HotelRoomRate(HotelID, TypeID)
);


-- ============================================
-- People / Payments
-- ============================================

CREATE TABLE Person (
    PersonID INT PRIMARY KEY AUTO_INCREMENT NOT NULL,
    FullName VARCHAR(50) NOT NULL,
    Phone VARCHAR(20) NOT NULL,
    MailingAddress VARCHAR(100) NOT NULL,
    
    UNIQUE(FullName, Phone)
);

CREATE TABLE PaymentCard (
    CardID INT PRIMARY KEY AUTO_INCREMENT NOT NULL,
    CardHolderName VARCHAR(50) NOT NULL,
    CardNumber VARCHAR(20) NOT NULL,
    ExpMonth INT NOT NULL,
    ExpYear INT NOT NULL,

    UNIQUE (CardNumber, ExpMonth, ExpYear)
);

-- ============================================
-- Reservations / Charges / Bonuses
-- ============================================

CREATE TABLE Reservation (
    ReservationID INT PRIMARY KEY AUTO_INCREMENT NOT NULL,
    HotelID INT NOT NULL,
    PersonID INT NOT NULL,
    CardID INT NOT NULL,
    CheckInDate DATE NOT NULL,
    CheckOutDate DATE NOT NULL,
    Status ENUM('Active', 'Cancelled', 'CheckedIn') NOT NULL DEFAULT 'Active',
    CancelledAt DATETIME NULL,

    FOREIGN KEY (HotelID) REFERENCES Hotel(HotelID),
    FOREIGN KEY (PersonID) REFERENCES Person(PersonID),
    FOREIGN KEY (CardID) REFERENCES PaymentCard(CardID)
);

CREATE TABLE ReservedRoom (
    ReservationID INT NOT NULL,
    RoomID INT NOT NULL,
    BookedNightlyRate DECIMAL (8, 2) NOT NULL,

    PRIMARY KEY (ReservationID, RoomID),
    FOREIGN KEY (ReservationID) REFERENCES Reservation(ReservationID),
    FOREIGN KEY (RoomID) REFERENCES Room(RoomID)
);

CREATE TABLE Charge (
    ChargeID INT PRIMARY KEY AUTO_INCREMENT NOT NULL,
    ReservationID INT NOT NULL,
    CardID INT NOT NULL,
    ChargeDate DATE NOT NULL,
    ChargeType ENUM('Room', 'Amenity', 'CancellationFee', 'Food') NOT NULL,
    Amount DECIMAL(8, 2) NOT NULL,

    FOREIGN KEY (ReservationID) REFERENCES Reservation(ReservationID),
    FOREIGN KEY (CardID) REFERENCES PaymentCard(CardID)
);

CREATE TABLE FrequentCustomers (
    PersonID INT NOT NULL,
    Year INT NOT NULL,

    PRIMARY KEY (PersonID, Year),
    FOREIGN KEY (PersonID) REFERENCES Person(PersonID)
);

-- ============================================
-- Sample data
-- ============================================

INSERT INTO NearbyFeatures (FeatureName)  VALUES
('Ocean'),
('Mountain'), 
('Lake'),
('River'),
('Airport'),
('Downtown');

INSERT INTO Amenities (AmenityName) VALUES
('Pool'),
('Spa'),
('Gym'),
('Free WiFi'),
('Parking'),
('Airport Shuttle'),
('Breakfast Buffet');

INSERT INTO Hotel (Name, Street, City, State, PostalCode, Rating, TimeZone, CheckInTime) VALUES
('MyHotel at Chicago Downtown', '100 N State St', 'Chicago', 'IL', '60601', 4, 'America/Chicago', '15:00:00'),
('MyHotel at O''Hare',          '10000 W O''Hare Ave', 'Chicago', 'IL', '60666', 3, 'America/Chicago', '15:00:00'),
('MyHotel at Orlando',          '500 International Dr', 'Orlando', 'FL', '32819', 5, 'America/New_York', '16:00:00');

INSERT INTO HotelNearbyFeatures(HotelID, FeatureName) VALUES
(1, 'Lake'),
(1, 'River'),
(1, 'Downtown'),
(2, 'Airport'),
(3, 'Lake');

INSERT INTO HotelAmenities (HotelID, AmenityName, Price) VALUES
(1, 'Free WiFi', NULL), (1, 'Gym', NULL), (1, 'Pool', 15.00), (1, 'Spa', 60.00), (1, 'Parking', 35.00),
(2, 'Free WiFi', NULL), (2, 'Airport Shuttle', NULL), (2, 'Parking', 20.00),
(3, 'Free WiFi', NULL), (3, 'Pool', NULL), (3, 'Spa', 80.00), (3, 'Breakfast Buffet', 25.00);

INSERT INTO ConferenceRoom (HotelID, Capacity) VALUES
(1, 40),
(1, 120),
(3, 300);

INSERT INTO RoomType (TypeID, BedSize, SmokingAllowed, WheelchairAccessible) VALUES
(1,'King',0,0),  (2,'King',0,1),  (3,'King',1,0),  (4,'King',1,1),
(5,'Queen',0,0), (6,'Queen',0,1), (7,'Queen',1,0), (8,'Queen',1,1),
(9,'Double',0,0),(10,'Double',0,1),(11,'Double',1,0),(12,'Double',1,1);

INSERT INTO HotelRoomRate (HotelID, TypeID, NightlyRate)
SELECT h.HotelId, t.TypeID, (80 + CASE t.BedSize WHEN 'King' THEN 30 WHEN 'Queen' THEN 15 ELSE 0 END)
FROM Hotel h JOIN RoomType t;

INSERT INTO Room (HotelID, RoomNumber, TypeID, Floor, Direction) VALUES
(1, 101, 1, 1, 'North'),  (1, 102, 2, 1, 'South'),  (1, 201, 5, 2, 'East'),
(1, 202, 3, 2, 'West'),  (1, 301, 9, 3, 'North-East'), (1, 302, 6, 3, 'South-West'),
(2, 110, 1, 1, 'North'),  (2, 111, 5, 1, 'East'),  (2, 210, 9, 2, 'South'),
(3, 1001, 1, 10, 'South-East'), (3, 1002, 2, 10, 'North-West'), (3, 1101, 5, 11, 'West');

