from pathlib import Path
from app.hotels import list_hotels
from app.hotels import list_hotels, get_hotel_details
from app.rooms import find_available_rooms
from app.reports import get_hotels_near_ocean_or_mountain
from app.reports import (
    get_hotels_near_ocean_or_mountain,
    get_reservation_report,
    format_reservation_report
)

def show_hotels():
    """Display all hotels."""

    hotels = list_hotels()

    if not hotels:
        print("\nNo hotels found.")
        return

    print("\nHotels:")
    print("-" * 65)

    for hotel in hotels:
        print(
            f"{hotel['HotelID']}: "
            f"{hotel['Name']} | "
            f"{hotel['City']}, {hotel['State']} | "
            f"{hotel['Rating']} stars"
        )

    print("-" * 65)

def show_hotel_details():
    """Ask for a hotel ID and display its information."""

    answer = input("\nEnter Hotel ID: ").strip()

    if not answer.isdigit():
        print("Invalid Hotel ID. Please enter a number.")
        return

    details = get_hotel_details(int(answer))

    if details is None:
        print("Hotel not found.")
        return

    hotel = details["hotel"]

    print(f"\n=== {hotel['Name']} ===")

    print(f"\nAddress: {hotel['Street']}")
    print(f"         {hotel['City']}, {hotel['State']} "
          f"{hotel['PostalCode']}")

    print(f"Rating: {hotel['Rating']} stars")
    print(f"Check-in: {hotel['CheckInTime']}")
    print(f"Time Zone: {hotel['TimeZone']}")

    print("\nNearby Features:")

    if details["features"]:
        for feature in details["features"]:
            print(f"- {feature['FeatureName']}")
    else:
        print("None listed.")

    print("\nAmenities:")

    if details["amenities"]:
        for amenity in details["amenities"]:

            if amenity["Price"] == 0:
                price = "Free"
            else:
                price = f"${amenity['Price']:.2f}"

            print(f"- {amenity['AmenityName']}: {price}")
    else:
        print("None listed.")

    print("\nConference Rooms:")

    if details["conference_rooms"]:
        for room in details["conference_rooms"]:
            print(f"- {room['Name']} "
                  f"(Capacity: {room['Capacity']})")
    else:
        print("None listed.")


def search_available_rooms(accessible_only=False):
    """Search rooms using customer criteria."""

    city = input("\nEnter city: ").strip()

    check_in = input("Check-in date (YYYY-MM-DD): ").strip()
    check_out = input("Check-out date (YYYY-MM-DD): ").strip()

    if not city:
        print("City is required.")
        return

    bed_size = None
    smoking = None
    accessible = None

    if accessible_only:
        accessible = True
    else:
        bed_size = input(
            "Bed size (King/Queen/Double): "
        ).strip().title()

        if bed_size not in ("King", "Queen", "Double"):
            print("Invalid bed size.")
            return

        answer = input(
            "Smoking allowed? (y/n): "
        ).strip().lower()

        if answer not in ("y", "n"):
            print("Please enter y or n.")
            return

        smoking = answer == "y"

    try:
        rooms = find_available_rooms(
            city=city,
            check_in=check_in,
            check_out=check_out,
            bed_size=bed_size,
            smoking=smoking,
            accessible=accessible
        )

    except ValueError as error:
        print(f"Invalid dates: {error}")
        return

    if not rooms:
        print("\nNo available rooms found.")
        return

    print(f"\nFound {len(rooms)} available room(s):")

    for room in rooms:
        print(
            f"\n{room['HotelName']}"
            f"\n  Room: {room['RoomNumber']}"
            f" (ID: {room['RoomID']})"
            f"\n  Bed: {room['BedSize']}"
            f"\n  Smoking: "
            f"{'Yes' if room['SmokingAllowed'] else 'No'}"
            f"\n  Accessible: "
            f"{'Yes' if room['WheelchairAccessible'] else 'No'}"
            f"\n  Rate: ${room['NightlyRate']:.2f}/night"
        )


def show_hotels_near_nature():
    hotels = get_hotels_near_ocean_or_mountain()

    print("\n=== Hotels Near Oceans or Mountains ===")

    if not hotels:
        print("No matching hotels found.")
        return

    for hotel in hotels:
        print(f"\nCity: {hotel['City']}")
        print(f"Hotel: {hotel['HotelName']}")
        print(
            f"Address: {hotel['Street']}, "
            f"{hotel['City']}, {hotel['State']} "
            f"{hotel['PostalCode']}"
        )
        print(f"Nearby: {hotel['FeatureName']}")


def show_reservation_report():
    answer = input("\nEnter Reservation ID: ").strip()

    if not answer.isdigit():
        print("Invalid Reservation ID.")
        return

    details = get_reservation_report(int(answer))

    if details is None:
        print("Reservation not found.")
        return

    report = format_reservation_report(details)

    print("\n" + report)

    save = input("\nSave report to a text file? (y/n): ").strip().lower()

    if save == "y":
        folder = Path("generated_reports")
        folder.mkdir(exist_ok=True)

        filename = folder / f"reservation_{answer}.txt"
        filename.write_text(report + "\n", encoding="utf-8")

        print(f"Report saved to: {filename}")


def main():
    while True:
        print("\n=== MyHotel Management System ===")
        print("1. List Hotels")
        print("2. View Hotel Details")
        print("3. Search Available Rooms")
        print("4. Search Wheelchair-Accessible Rooms")
        print("5. Hotels Near Oceans or Mountains")
        print("6. Print Reservation Report")
        print("0. Exit")

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            show_hotels()

        elif choice == "0":
            print("Goodbye!")
            break

        elif choice == "2":
            show_hotel_details()

        elif choice == "3":
            search_available_rooms()

        elif choice == "4":
            search_available_rooms(accessible_only=True)

        elif choice == "5":
            show_hotels_near_nature()

        elif choice == "6":
            show_reservation_report()

        else:
            print("Invalid option. Try again.")


if __name__ == "__main__":
    main()