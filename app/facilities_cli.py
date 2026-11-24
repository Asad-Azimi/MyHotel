"""Terminal menus for management of hotel amenities, nearby features and conference rooms."""

import pymysql

from app import facilities as f


def ask(label):
    return input(f"{label}: ").strip()


def ask_int(label):
    return int(ask(label))


def confirmed(label):
    return ask(label + " (type YES to confirm)") == "YES"


def display(rows):
    if not rows:
        print("  None found.")
    else:
        for row in rows:
            print("  " + " | ".join(f"{key}: {value}" for key, value in row.items()))


def amenity_menu():
    while True:
        print("\n=== AMENITIES ===")
        print("1. List amenity catalog")
        print("2. Add amenity to catalog")
        print("3. Rename amenity")
        print("4. List amenities at hotel")
        print("5. Assign amenity / change hotel price")
        print("6. Remove amenity from hotel")
        print("7. Delete unused amenity from catalog")
        print("0. Back")
        choice = ask("Choose")
        try:
            if choice == "1":
                display(f.list_amenities())
            elif choice == "2":
                print(f"  Added AmenityID: {f.add_amenity(ask('Amenity name'))}")
            elif choice == "3":
                f.rename_amenity(ask_int("Amenity ID"), ask("New name"))
                print("  Amenity renamed.")
            elif choice == "4":
                display(f.list_hotel_amenities(ask_int("Hotel ID")))
            elif choice == "5":
                print("  Price 0 means free. Amenity IDs are from the catalog.")
                f.set_hotel_amenity(ask_int("Hotel ID"), ask_int("Amenity ID"),
                                    ask("Price"))
                print("  Hotel amenity saved.")
            elif choice == "6":
                hid, aid = ask_int("Hotel ID"), ask_int("Amenity ID")
                if confirmed("Remove this offering"):
                    f.remove_hotel_amenity(hid, aid)
                    print("  Offering removed; historical charges are unchanged.")
            elif choice == "7":
                aid = ask_int("Amenity ID")
                if confirmed("Delete this unused catalog amenity"):
                    f.delete_unused_amenity(aid)
                    print("  Amenity deleted.")
            elif choice == "0":
                return
            else:
                print("  Invalid choice.")
        except (ValueError, pymysql.MySQLError) as error:
            print(f"  Error: {error}")


def nearby_menu():
    while True:
        print("\n=== NEARBY FEATURES ===")
        print("1. List feature catalog")
        print("2. Add feature to catalog")
        print("3. Rename feature")
        print("4. List hotel's nearby features")
        print("5. Assign feature to hotel")
        print("6. Remove feature from hotel")
        print("7. Delete unused feature from catalog")
        print("0. Back")
        choice = ask("Choose")
        try:
            if choice == "1":
                display(f.list_nearby_features())
            elif choice == "2":
                print(f"  Added FeatureID: {f.add_nearby_feature(ask('Feature name'))}")
            elif choice == "3":
                f.rename_nearby_feature(ask_int("Feature ID"), ask("New name"))
                print("  Feature renamed.")
            elif choice == "4":
                display(f.list_hotel_features(ask_int("Hotel ID")))
            elif choice == "5":
                f.assign_nearby_feature(ask_int("Hotel ID"), ask_int("Feature ID"))
                print("  Feature assigned.")
            elif choice == "6":
                hid, fid = ask_int("Hotel ID"), ask_int("Feature ID")
                if confirmed("Remove this hotel-feature association"):
                    f.remove_nearby_feature(hid, fid)
                    print("  Association removed.")
            elif choice == "7":
                fid = ask_int("Feature ID")
                if confirmed("Delete this unused catalog feature"):
                    f.delete_unused_feature(fid)
                    print("  Feature deleted.")
            elif choice == "0":
                return
            else:
                print("  Invalid choice.")
        except (ValueError, pymysql.MySQLError) as error:
            print(f"  Error: {error}")


def conference_menu():
    while True:
        print("\n=== CONFERENCE ROOMS ===")
        print("1. List conference rooms for hotel")
        print("2. Add conference room")
        print("3. Update conference room")
        print("4. Delete conference room")
        print("0. Back")
        choice = ask("Choose")
        try:
            if choice == "1":
                display(f.list_conference_rooms(ask_int("Hotel ID")))
            elif choice == "2":
                room_id = f.add_conference_room(ask_int("Hotel ID"),
                                                ask("Name"), ask_int("Capacity"))
                print(f"  Added ConferenceRoomID: {room_id}")
            elif choice == "3":
                f.update_conference_room(ask_int("Conference room ID"),
                                         ask("New name"), ask_int("New capacity"))
                print("  Conference room updated.")
            elif choice == "4":
                rid = ask_int("Conference room ID")
                if confirmed("Delete conference room"):
                    f.delete_conference_room(rid)
                    print("  Conference room deleted.")
            elif choice == "0":
                return
            else:
                print("  Invalid choice.")
        except (ValueError, pymysql.MySQLError) as error:
            print(f"  Error: {error}")


def facilities_menu():
    while True:
        print("\n=== HOTEL FACILITIES ===")
        print("1. Manage amenities and hotel prices")
        print("2. Manage nearby features")
        print("3. Manage conference rooms")
        print("0. Back")
        choice = ask("Choose")
        if choice == "1":
            amenity_menu()
        elif choice == "2":
            nearby_menu()
        elif choice == "3":
            conference_menu()
        elif choice == "0":
            return
        else:
            print("  Invalid choice.")
