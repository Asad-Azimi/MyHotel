from app.hotels import list_hotels
from app.hotels import list_hotels, get_hotel_details

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

def main():
    while True:
        print("\n=== MyHotel Management System ===")
        print("1. List Hotels")
        print("2. View Hotel Details")
        print("0. Exit")

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            show_hotels()

        elif choice == "0":
            print("Goodbye!")
            break

        elif choice == "2":
            show_hotel_details()

        else:
            print("Invalid option. Try again.")


if __name__ == "__main__":
    main()