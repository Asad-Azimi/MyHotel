# MyHotel — Hotel Reservation Management System

**COSC 3510: Introduction to Database · Georgetown University · Fall 2026**  
**Team:** Asadullah Azimi and Amelia [Last Name]

## Overview

MyHotel is a command-line application for managing a hotel chain through a centralized MySQL database. Staff can look up hotels and available rooms, book and manage reservations, maintain customer and payment-card records, record charges, and update hotel facilities without writing SQL.

The project supports multiple hotel locations and room types, including non-smoking and wheelchair-accessible rooms. It uses relational constraints to protect related records and stores the booked room rate so later price changes do not alter an existing reservation.

## Main features

- **Hotels and facilities:** View hotel details, manage hotel records and rooms, update hotel-specific room rates, and maintain amenities, nearby features, and conference rooms.
- **Room availability:** Search by city, dates, bed size, smoking preference, and wheelchair accessibility; avoid double-booking rooms.
- **Reservations:** Book one or more rooms, reuse existing customer records, support a guest whose cardholder is someone else, change reservations, check guests in/out, cancel bookings, and handle no-shows.
- **Charges:** Post room charges and record food, paid amenities, and applicable cancellation/no-show charges. View itemized charges by reservation or by guest/cardholder.
- **Customer records:** Add, find, edit, or remove unused customers and maintain payment-card records.
- **Reports:** Find hotels near oceans/mountains, list late arrivals, identify frequent customers eligible for a bonus, and print detailed reservation confirmations.

## Requirements

- Python **3.9 or newer** (Python 3.10+ recommended)
- MySQL **8.0.16 or newer**, running locally or on an accessible server
- Python dependencies specified in `requirements.txt` (including the MySQL driver)
- A terminal or command prompt

## Setup and run

Run these commands from the **project root** (the directory containing `main.py`). On macOS/Linux:

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install Python dependencies
python -m pip install -r requirements.txt

# 3. Create your local configuration file
cp .env.example .env
```

Open `.env` and fill in the MySQL settings shown in `.env.example`. Make sure the database name matches **`myHotel`** and the username/password are correct. **Never commit `.env` or actual passwords.**

### Database setup — only for a new installation

Ensure MySQL is running. Use the schema and seed SQL files provided in the project's `database/` folder. In the standard project layout, the commands are:

```bash
mysql -u root -p < database/schema.sql
mysql -u root -p myHotel < database/seed.sql
```

> **Important:** Check the filenames and contents of your local `database/` folder before running these commands. Database setup scripts may create or reset data. **Do not rerun schema/seed scripts against an existing database containing reservations or demo test data.** The provided seed data is for demonstration and testing.

To confirm that the database is accessible:

```bash
mysql -u root -p -e "SHOW TABLES FROM myHotel;"
```

### Start the application

```bash
python main.py
```

On some systems the equivalent command is `python3 main.py`. The application runs in the terminal; **no web browser or Flask server is required**.

## How to use the application

Enter a menu number and follow the prompts. Use `0` to go back or exit the current menu.

| Main menu | What to do |
| --- | --- |
| **1. List Hotels** | See all hotel locations. |
| **2. View Hotel Details** | View a hotel's address, rating, amenities, nearby features, and conference rooms. |
| **3. Search Available Rooms** | Search by city, dates, bed size, and smoking preference. |
| **4. Search Wheelchair-Accessible Rooms** | Search accessible rooms for a city and date range. |
| **5. Hotels Near Oceans or Mountains** | Run the geographic hotel report. |
| **6. Print Reservation Report** | Display or save the detailed printable reservation information. |
| **7. Customers** | Manage customers, saved cards, reservation counts, and bonus awards. |
| **8. Reservations** | Book and manage reservations, check-in/out, cancel, or review late arrivals. |
| **9. Charges** | Post room charges, record other charges, and view itemized billing. |
| **10. Manage Hotels** | Add/update/delete eligible hotels, manage rooms/rates, amenities, features, and conference rooms. |

### Where to find the eight required queries

| Query | Application menu |
| --- | --- |
| **1. Available rooms by city, bed size, and smoking preference** | Main menu **3** |
| **2. Wheelchair-accessible room availability** | Main menu **4** |
| **3. Hotels near an ocean or mountain** | Main menu **5** |
| **4. Reservations for a guest (name and phone)** | **8 → 3** |
| **5. Itemized guest/cardholder charges and dates** | **9 → 1** |
| **6. Guests who are late to check in** | **8 → 11** |
| **7. Frequent-customer bonus eligibility** | **7 → 10** (also evaluated when a reservation is booked) |
| **8. Detailed printable reservation information** | Main menu **6** |

### Example workflow: make a reservation

1. Select **8 → 1 (Search available rooms)** or **8 → 2 (Make a reservation)**.
2. Enter the city and check-in/check-out dates in `YYYY-MM-DD` format, then choose room preferences.
3. Select one or more **available room IDs** from a single hotel.
4. Enter the guest's name, 10-digit phone number, and mailing address as requested.
5. Enter a **fictional test card number**, expiration month/year, and indicate whether the guest is also the cardholder. If not, provide the cardholder's information.
6. The system creates a reservation ID; use **6 (Print Reservation Report)** to review the confirmation.

**Billing note:** Creating a reservation does **not** automatically add the full room charge to the `Charge` table. To record that charge, use **9 → 5 (Post room charges)** with the reservation ID. The charge can then be viewed under **9 → 2 (A reservation's charges)** or **9 → 1 (A customer's charges)**. Posting the same standard room charge twice is rejected.

**Cardholder note:** A guest may book using another person's registered card. The customer-charge report includes charges where the searched person is either the **guest** or the **cardholder**. A charge can therefore appear in two different people's reports without being stored or billed twice.

### Demo-friendly examples

- Search **San Diego** for available rooms, then inspect a hotel's rooms and amenities.
- Open the customer reservation report using a seeded guest's name and phone number.
- Print a reservation confirmation and inspect the room types, rate, and number of nights.
- Create a test reservation using an available room, then confirm that a conflicting booking is rejected.
- Record a room/amenity charge and display the itemized total.
- Explore the **Manage Hotels** submenu using a temporary hotel instead of changing seeded reservations.

## Data and business rules

- A reservation requires a payment card, but the cardholder may be different from the guest.
- A room cannot be booked for overlapping dates while an active reservation holds it.
- Booked nightly rates are saved with the reservation and are not changed by later hotel rate updates.
- Cancellation within the 48-hour window may incur a fee of **20% of the first night's booked room rate**; a no-show can incur the corresponding fee.
- The frequent-customer report uses **at least three qualifying reservations in a booking year**, following the wording of required Query 7.
- Hotels and rooms with related reservation history are protected from unsafe deletion; deactivation or preservation of history is preferred.
- Charges and payment-card associations have validation checks to prevent inappropriate reassignment of historical charges.

## Project organization

```text
.
├── main.py                 # Terminal application and main menus
├── app/
│   ├── db.py               # MySQL connection and transaction helpers
│   ├── hotels.py           # Hotel details and hotel data operations
│   ├── rooms.py            # Room searches and availability
│   ├── reports.py          # Reporting queries
│   ├── customers.py        # Customers, cards, bonus awards
│   ├── reservations.py     # Booking and reservation management
│   ├── charges.py          # Billing and itemized charge queries
│   ├── hotel_cli.py        # Hotel management menu
│   ├── room_admin.py       # Room and room-rate operations
│   ├── room_admin_cli.py   # Room management menu
│   ├── facilities.py       # Amenities, features, conference rooms
│   └── facilities_cli.py   # Facility management menu
├── database/               # Database schema and sample-data SQL
├── docs/                   # Design, test and cover documents
├── requirements.txt        # Python dependencies
└── .env.example            # Configuration example (no secrets)
```

## Project documentation

The submitted project includes a **cover page**, **one-page relational schema/design document**, and **requirements test document**. The test document maps each required feature and sample query to its test outcome. These materials, along with source code, are submitted through Canvas according to the course instructions.

## Notes

This is an **academic demonstration application**, not a production payment system. Use invented customer information and **fictional payment-card numbers only**. Do not use real payment-card details or sensitive personal information.
