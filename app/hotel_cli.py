
import pymysql

from app import db
from app.hotels import add_hotel, update_hotel, delete_hotel


def ask_hotel_fields(current=None):
    """Ask for hotel fields; Enter keeps existing values."""

    fields = [
        ("Hotel name", "Name"),
        ("Street", "Street"),
        ("City", "City"),
        ("State", "State"),
        ("Postal code", "PostalCode"),
        ("Rating (1-6)", "Rating"),
        ("Time zone (e.g. America/Chicago)", "TimeZone"),
        ("Check-in time (HH:MM)", "CheckInTime")
    ]

    values = []

    for label, key in fields:
        old = str(current[key]) if current else ""

        prompt = f"{label} [{old}]: " if current else f"{label}: "
        value = input(prompt).strip()

        values.append(value if value else old)

    return values


def get_hotel(hotel_id):
    rows = db.query(
        "SELECT * FROM Hotel WHERE HotelID=%s",
        (hotel_id,)
    )

    if not rows:
        raise ValueError("Hotel not found.")

    return rows[0]


def add_hotel_ui():
    print("\n=== Add Hotel ===")

    values = ask_hotel_fields()

    hotel_id = add_hotel(*values)

    print(f"Hotel created successfully! HotelID: {hotel_id}")


def update_hotel_ui():
    hotel_id = int(input("Hotel ID to update: ").strip())
    hotel = get_hotel(hotel_id)

    print(f"\nUpdating: {hotel['Name']}")
    print("Press Enter to keep an existing value.")

    values = ask_hotel_fields(hotel)

    update_hotel(hotel_id, *values)

    print("Hotel updated successfully.")


def delete_hotel_ui():
    hotel_id = int(input("Hotel ID to delete: ").strip())
    hotel = get_hotel(hotel_id)

    print(f"Hotel: {hotel['Name']}")
    confirmation = input("Type YES to delete: ").strip()

    if confirmation != "YES":
        print("Deletion cancelled.")
        return

    delete_hotel(hotel_id)

    print("Hotel deleted successfully.")


def hotel_admin_menu():
    while True:
        print("\n=== HOTEL MANAGEMENT ===")
        print("1. Add Hotel")
        print("2. Update Hotel")
        print("3. Delete Hotel")
        print("0. Back")

        choice = input("\nChoose an option: ").strip()

        try:
            if choice == "1":
                add_hotel_ui()
            elif choice == "2":
                update_hotel_ui()
            elif choice == "3":
                delete_hotel_ui()
            elif choice == "0":
                return
            else:
                print("Invalid option.")

        except (ValueError, pymysql.MySQLError) as error:
            print(f"Error: {error}")
