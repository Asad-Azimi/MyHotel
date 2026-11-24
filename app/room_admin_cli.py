import pymysql

from app.room_admin import (
    list_room_types,
    list_hotel_rooms,
    add_room,
    update_room,
    set_room_active,
    set_room_rate,
    delete_room,
)


def ask_int(prompt):
    return int(input(prompt).strip())


def show_types():
    for t in list_room_types():
        print(
            f"{t['TypeID']}: {t['BedSize']} | "
            f"Smoking: {'Yes' if t['SmokingAllowed'] else 'No'} | "
            f"Accessible: {'Yes' if t['WheelchairAccessible'] else 'No'}"
        )


def show_rooms():
    hotel_id = ask_int("Hotel ID: ")
    rooms = list_hotel_rooms(hotel_id)

    if not rooms:
        print("No rooms found.")
        return

    for r in rooms:
        print(
            f"ID {r['RoomID']} | Room {r['RoomNumber']} | "
            f"Type {r['TypeID']} ({r['BedSize']}) | "
            f"Floor {r['Floor']} | {r['Direction']} | "
            f"${r['NightlyRate']:.2f} | "
            f"{'Active' if r['IsActive'] else 'Inactive'}"
        )


def create_room_ui():
    hotel_id = ask_int("Hotel ID: ")
    show_types()
    room_id = add_room(
        hotel_id,
        input("Room number: "),
        ask_int("Room type ID: "),
        ask_int("Floor: "),
        input("Direction: ")
    )
    print(f"Room created! RoomID: {room_id}")


def update_room_ui():
    room_id = ask_int("Room ID: ")
    print("Enter the updated values:")
    update_room(
        room_id,
        input("Room number: "),
        ask_int("Room type ID: "),
        ask_int("Floor: "),
        input("Direction: ")
    )
    print("Room updated.")


def change_status_ui():
    room_id = ask_int("Room ID: ")
    choice = input("Activate room? (y/n): ").strip().lower()

    if choice not in ("y", "n"):
        raise ValueError("Enter y or n.")

    set_room_active(room_id, choice == "y")
    print("Room status updated.")


def change_rate_ui():
    show_types()
    hotel_id = ask_int("Hotel ID: ")
    type_id = ask_int("Room type ID: ")
    rate = input("New nightly rate: ")

    set_room_rate(hotel_id, type_id, rate)
    print("Rate saved.")


def delete_room_ui():
    room_id = ask_int("Room ID: ")

    if input("Type YES to delete: ").strip() != "YES":
        print("Deletion cancelled.")
        return

    delete_room(room_id)
    print("Room deleted.")


def room_admin_menu():
    while True:
        print("\n=== ROOM MANAGEMENT ===")
        print("1. List Room Types")
        print("2. List Rooms at a Hotel")
        print("3. Add Room")
        print("4. Update Room")
        print("5. Activate / Deactivate Room")
        print("6. Set Hotel Room Rate")
        print("7. Delete Unreserved Room")
        print("0. Back")

        choice = input("Choose: ").strip()

        try:
            if choice == "1":
                show_types()
            elif choice == "2":
                show_rooms()
            elif choice == "3":
                create_room_ui()
            elif choice == "4":
                update_room_ui()
            elif choice == "5":
                change_status_ui()
            elif choice == "6":
                change_rate_ui()
            elif choice == "7":
                delete_room_ui()
            elif choice == "0":
                return
            else:
                print("Invalid option.")
        except (ValueError, pymysql.MySQLError) as error:
            print(f"Error: {error}")