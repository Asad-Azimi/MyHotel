from app.hotels import list_hotels


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


def main():
    while True:
        print("\n=== MyHotel Management System ===")
        print("1. List Hotels")
        print("0. Exit")

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            show_hotels()

        elif choice == "0":
            print("Goodbye!")
            break

        else:
            print("Invalid option. Try again.")


if __name__ == "__main__":
    main()