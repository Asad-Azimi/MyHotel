-- ============================================
-- MyHotel Database Schema
-- ============================================

-- Create database if not exist
CREATE DATABASE IF NOT EXISTS myHotel
    CHARACTER SET utf8mb4;
USE myHotel;

-- ============================================
-- Hotels and their features
-- ============================================

CREATE TABLE Hotel (
    HotelID INT NOT NULL AUTO_INCREMENT,
    Name VARCHAR(100) NOT NULL,
    Street VARCHAR(150) NOT NULL,
    City VARCHAR(100) NOT NULL,
    State VARCHAR(100) NOT NULL,
    PostalCode VARCHAR(20) NOT NULL,
    Rating INT NOT NULL,
    TimeZone VARCHAR(64) NOT NULL,
    CheckInTime TIME NOT NULL,
    PRIMARY KEY (HotelID),
    CONSTRAINT chk_hotel_rating CHECK (Rating BETWEEN 1 AND 6)
);

-- 2. Named categories of nearby natural/geographic features
CREATE TABLE NearbyFeature (
    FeatureID INT NOT NULL AUTO_INCREMENT,
    FeatureName VARCHAR(50) NOT NULL,
    PRIMARY KEY (FeatureID),
    UNIQUE KEY uq_nearby_feature_name (FeatureName)
);

-- 3. Many-to-many: hotels and nearby features
CREATE TABLE HotelNearbyFeature (
    HotelID INT NOT NULL,
    FeatureID INT NOT NULL,
    PRIMARY KEY (HotelID, FeatureID),
    CONSTRAINT fk_hnf_hotel FOREIGN KEY (HotelID)
        REFERENCES Hotel(HotelID),
    CONSTRAINT fk_hnf_feature FOREIGN KEY (FeatureID)
        REFERENCES NearbyFeature(FeatureID)
);

-- 4. Master amenity list
CREATE TABLE Amenity (
    AmenityID INT NOT NULL AUTO_INCREMENT,
    AmenityName VARCHAR(100) NOT NULL,
    PRIMARY KEY (AmenityID),
    UNIQUE KEY uq_amenity_name (AmenityName)
);

-- 5. Hotel-specific amenity availability and price
-- Price=0.00 means free; never use NULL to mean free.
CREATE TABLE HotelAmenity (
    HotelID INT NOT NULL,
    AmenityID INT NOT NULL,
    Price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    PRIMARY KEY (HotelID, AmenityID),
    CONSTRAINT fk_ha_hotel FOREIGN KEY (HotelID)
        REFERENCES Hotel(HotelID),
    CONSTRAINT fk_ha_amenity FOREIGN KEY (AmenityID)
        REFERENCES Amenity(AmenityID),
    CONSTRAINT chk_ha_price CHECK (Price >= 0)
);

-- ============================================
-- Rooms: room rates and room types
-- ============================================

-- 6. Conference rooms (zero or more per hotel)
CREATE TABLE ConferenceRoom (
    ConferenceRoomID INT NOT NULL AUTO_INCREMENT,
    HotelID INT NOT NULL,
    Name VARCHAR(100) NOT NULL,
    Capacity INT NOT NULL,
    PRIMARY KEY (ConferenceRoomID),
    UNIQUE KEY uq_conference_hotel_name (HotelID, Name),
    CONSTRAINT fk_conference_hotel FOREIGN KEY (HotelID)
        REFERENCES Hotel(HotelID),
    CONSTRAINT chk_conference_capacity CHECK (Capacity > 0)
);

-- 7. Chain-wide room categories
CREATE TABLE RoomType (
    TypeID INT NOT NULL AUTO_INCREMENT,
    BedSize VARCHAR(20) NOT NULL,
    SmokingAllowed BOOLEAN NOT NULL,
    WheelchairAccessible BOOLEAN NOT NULL,
    PRIMARY KEY (TypeID),
    UNIQUE KEY uq_roomtype_characteristics
        (BedSize, SmokingAllowed, WheelchairAccessible),
    CONSTRAINT chk_roomtype_bedsize CHECK (BedSize IN ('King','Queen','Double')),
    CONSTRAINT chk_roomtype_smoking CHECK (SmokingAllowed IN (0,1)),
    CONSTRAINT chk_roomtype_accessible CHECK (WheelchairAccessible IN (0,1))
);

-- 8. Current prices by hotel and type
CREATE TABLE HotelRoomRate (
    HotelID INT NOT NULL,
    TypeID INT NOT NULL,
    NightlyRate DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (HotelID, TypeID),
    CONSTRAINT fk_rate_hotel FOREIGN KEY (HotelID)
        REFERENCES Hotel(HotelID),
    CONSTRAINT fk_rate_type FOREIGN KEY (TypeID)
        REFERENCES RoomType(TypeID),
    CONSTRAINT chk_rate_nonnegative CHECK (NightlyRate >= 0)
);

-- 9. Physical guest rooms. Each hotel/type combination must have a rate.
CREATE TABLE Room (
    RoomID INT NOT NULL AUTO_INCREMENT,
    HotelID INT NOT NULL,
    RoomNumber VARCHAR(10) NOT NULL,
    TypeID INT NOT NULL,
    Floor INT NOT NULL,
    Direction ENUM('North','South','East','West',
                   'North-East','South-East','North-West','South-West') NOT NULL,
    IsActive BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (RoomID),
    UNIQUE KEY uq_room_number_in_hotel (HotelID, RoomNumber),
    CONSTRAINT fk_room_hotel FOREIGN KEY (HotelID)
        REFERENCES Hotel(HotelID),
    CONSTRAINT fk_room_hotel_type FOREIGN KEY (HotelID, TypeID)
        REFERENCES HotelRoomRate(HotelID, TypeID),
    CONSTRAINT chk_room_active CHECK (IsActive IN (0,1))
);


-- ============================================
-- People / Payments
-- ============================================

-- 10. Guests and people who own payment cards
CREATE TABLE Person (
    PersonID INT NOT NULL AUTO_INCREMENT,
    FullName VARCHAR(150) NOT NULL,
    Phone VARCHAR(25) NOT NULL,
    MailingAddress VARCHAR(255) NULL,
    PRIMARY KEY (PersonID),
    INDEX idx_person_name_phone (FullName, Phone)
);

-- 11. Fictional payment cards ONLY; never put real card data in this demo.
CREATE TABLE PaymentCard (
    CardID INT NOT NULL AUTO_INCREMENT,
    HolderPersonID INT NOT NULL,
    CardholderName VARCHAR(150) NOT NULL,
    CardNumber VARCHAR(25) NOT NULL,
    ExpMonth INT NOT NULL,
    ExpYear INT NOT NULL,
    PRIMARY KEY (CardID),
    CONSTRAINT fk_card_holder FOREIGN KEY (HolderPersonID)
        REFERENCES Person(PersonID),
    CONSTRAINT chk_card_month CHECK (ExpMonth BETWEEN 1 AND 12)
);

-- ============================================
-- Reservations / Charges / Bonuses
-- ============================================

-- 12. One reservation is for one hotel and shared date range.
-- UTC fields are a convention; app must supply/convert UTC values.
CREATE TABLE Reservation (
    ReservationID INT NOT NULL AUTO_INCREMENT,
    GuestPersonID INT NOT NULL,
    HotelID INT NOT NULL,
    CardID INT NOT NULL,
    BookedAtUTC DATETIME NOT NULL,
    CheckInDate DATE NOT NULL,
    CheckOutDate DATE NOT NULL,
    ScheduledCheckInAtUTC DATETIME NOT NULL,
    ActualCheckInAtUTC DATETIME NULL,
    CancelledAtUTC DATETIME NULL,
    Status ENUM('Booked','CheckedIn','CheckedOut','Cancelled','NoShow')
        NOT NULL DEFAULT 'Booked',
    PRIMARY KEY (ReservationID),
    CONSTRAINT fk_reservation_guest FOREIGN KEY (GuestPersonID)
        REFERENCES Person(PersonID),
    CONSTRAINT fk_reservation_hotel FOREIGN KEY (HotelID)
        REFERENCES Hotel(HotelID),
    CONSTRAINT fk_reservation_card FOREIGN KEY (CardID)
        REFERENCES PaymentCard(CardID),
    CONSTRAINT chk_stay_dates CHECK (CheckOutDate > CheckInDate),
    INDEX idx_reservation_guest (GuestPersonID),
    INDEX idx_reservation_due (Status, ScheduledCheckInAtUTC)
);

-- 13. Room assignments within each reservation; booked rate is historical.
-- Additional cross-table rules (same hotel, no overlapping active stays)
-- MUST be enforced in the transactional booking service.
CREATE TABLE ReservedRoom (
    ReservationID INT NOT NULL,
    RoomID INT NOT NULL,
    BookedNightlyRate DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (ReservationID, RoomID),
    CONSTRAINT fk_rr_reservation FOREIGN KEY (ReservationID)
        REFERENCES Reservation(ReservationID),
    CONSTRAINT fk_rr_room FOREIGN KEY (RoomID)
        REFERENCES Room(RoomID),
    CONSTRAINT chk_booked_nightly_rate CHECK (BookedNightlyRate >= 0)
);

-- 14. Itemized charges for a reservation. Uses Reservation.CardID.
CREATE TABLE Charge (
    ChargeID INT NOT NULL AUTO_INCREMENT,
    ReservationID INT NOT NULL,
    AmenityID INT NULL,
    ChargeType ENUM('Room','Food','Amenity','Cancellation') NOT NULL,
    Amount DECIMAL(10,2) NOT NULL,
    ChargedAtUTC DATETIME NOT NULL,
    Description VARCHAR(255) NOT NULL,
    PRIMARY KEY (ChargeID),
    CONSTRAINT fk_charge_reservation FOREIGN KEY (ReservationID)
        REFERENCES Reservation(ReservationID),
    CONSTRAINT fk_charge_amenity FOREIGN KEY (AmenityID)
        REFERENCES Amenity(AmenityID),
    CONSTRAINT chk_charge_amount CHECK (Amount >= 0),
    CONSTRAINT chk_charge_amenity_type CHECK (
        (ChargeType = 'Amenity' AND AmenityID IS NOT NULL)
        OR (ChargeType <> 'Amenity' AND AmenityID IS NULL)
    )
);

-- 15. One bonus record per person and booking year.
CREATE TABLE BonusAward (
    PersonID INT NOT NULL,
    BookingYear SMALLINT NOT NULL,
    AwardedAtUTC DATETIME NOT NULL,
    MailedAtUTC DATETIME NULL,
    Status ENUM('Pending','Mailed') NOT NULL DEFAULT 'Pending',
    PRIMARY KEY (PersonID, BookingYear),
    CONSTRAINT fk_bonus_person FOREIGN KEY (PersonID)
        REFERENCES Person(PersonID)
);