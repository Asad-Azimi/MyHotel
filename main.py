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

import pymysql
from app import charges
from app import customers
from app import db
from app import reservations

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
        print("7. Customers")
        print("8. Reservations")
        print("9. Charges")
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

        elif choice == "7":
            customers_menu()

        elif choice == "8":
            reservations_menu()

        elif choice == "9":
            charges_menu()

        else:
            print("Invalid option. Try again.")

# helpers

def ask(prompt):
    return input('  %s: ' % prompt).strip()


def ask_int(prompt):
    value = ask(prompt)
    try:
        return int(value)
    except ValueError:
        raise ValueError('%s must be a whole number.' % prompt)


def yes(prompt):
    return ask(prompt + ' (y/N)').lower().startswith('y')


def money(v):
    return '${:,.2f}'.format(v)


def when(dt):
    return dt.strftime('%Y-%m-%d %H:%M UTC') if dt else '-'


# customers


def add_customer():
    name, phone = ask('Full name'), ask('Phone (10 digits)')
    existing = customers.find_person(name, phone)
    if existing:
        print('  That customer already exists (#%d). Address on file: %s' % (
            existing['PersonID'], existing['MailingAddress'] or '(none)'))
        if not yes('Update the address?'):
            return
    pid, created = customers.add_person(name, phone, ask('Mailing address'))
    print('  Added customer #%d.' % pid if created else '  Customer #%d updated.' % pid)


def find_customer():
    person = customers.require_person(ask('Full name'), ask('Phone'))

    print("\nID    Name    Phone    Address")
    print("-" * 65)
    print("%-5s %-15s %-12s %s" % (
        person['PersonID'],
        person['FullName'],
        person['Phone'],
        person['MailingAddress'] or ''
    ))

    n = customers.count_reservations(person['PersonID'])
    print('  Reservations booked this year: %d%s' % (
        n, '   (Will Receive Bonus)' if n >= customers.BONUS_MIN_RESERVATIONS else ''))


def search_customers():
    rows = customers.search_persons(ask('Name or phone contains'))

    if not rows:
        print('No customers found.')
        return

    print("\nID    Name    Phone    Address")
    print("-" * 65)

    for row in rows:
        print("%-5s %-15s %-12s %s" % (
            row['PersonID'],
            row['FullName'],
            row['Phone'],
            row['MailingAddress'] or ''
        ))


def list_customers():
    rows = customers.list_persons()

    if not rows:
        print('  No customers found.')
        return

    print("\nID    Name    Phone    Address")
    print("-" * 65)

    for row in rows:
        print("%-5s %-15s %-12s %s" % (
            row['PersonID'],
            row['FullName'],
            row['Phone'],
            row['MailingAddress'] or ''
        ))


def update_customer():
    person = customers.get_person(ask_int('Customer ID'))
    print('  (press Enter to keep the current value)')
    name = ask('Name [%s]' % person['FullName']) or person['FullName']
    phone = ask('Phone [%s]' % person['Phone']) or person['Phone']
    address = ask('Address [%s]' % (person['MailingAddress'] or '')) or person['MailingAddress']
    customers.update_person(person['PersonID'], name, phone, address)
    print('  Customer updated.')


def delete_customer():
    person = customers.get_person(ask_int('Customer ID'))
    if yes('Delete %s?' % person['FullName']):
        customers.delete_person(person['PersonID'])
        print('  Customer deleted.')





def customer_cards():
    person = customers.require_person(ask('Full name'), ask('Phone'))
    rows = customers.list_cards_for_person(person['PersonID'])

    if not rows:
        print('  No cards found.')
        return

    print("\nCard ID    Name on card    Last 4    Expires")
    print("-" * 60)

    for row in rows:
        print("%-10s %-15s %-9s %02d/%d" % (
            row['CardID'],
            row['CardholderName'],
            row['Last4'],
            row['ExpMonth'],
            row['ExpYear']
        ))


def update_card():
    card = customers.get_card(ask_int('Card ID'))
    print('  (press Enter to keep the current value)')
    holder = ask('Name on card [%s]' % card['CardholderName']) or card['CardholderName']
    month = ask('Expiration month [%d]' % card['ExpMonth']) or card['ExpMonth']
    year = ask('Expiration year [%d]' % card['ExpYear']) or card['ExpYear']
    customers.update_card(card['CardID'], holder, month, year)
    print('  Card updated.')


def delete_card():
    card = customers.get_card(ask_int('Card ID'))
    if yes('Delete the card ending %s?' % card['Last4']):
        customers.delete_card(card['CardID'])
        print('  Card deleted.')


def yearly_counts():
    year = ask('Year (Enter for this year)')
    rows = customers.reservation_counts(year or None)

    if not rows:
        print('  No reservation records found.')
        return

    print("\nID    Name    Phone    Reservations    Bonus?")
    print("-" * 75)

    for row in rows:
        bonus = 'Will Receive Bonus' if row['Reservations'] >= customers.BONUS_MIN_RESERVATIONS else ''

        print("%-5s %-15s %-12s %-15s %s" % (
            row['PersonID'],
            row['FullName'],
            row['Phone'],
            row['Reservations'],
            bonus
        ))


def bonus_list():
    rows = customers.list_bonus_awards(
        pending_only=yes('Only bonuses not yet mailed?')
    )

    if not rows:
        print('No bonus records found.')
        return

    print("\nID    Year    Name    Mail bonus to    Status")
    print("-" * 80)

    for row in rows:
        print("%-5s %-7s %-15s %-30s %s" % (
            row['PersonID'],
            row['BookingYear'],
            row['FullName'],
            row['MailingAddress'] or '',
            row['Status']
        ))


def mark_mailed():
    customers.mark_bonus_mailed(ask_int('Customer ID'), ask_int('Year'))
    print('  Marked as mailed.')


def customers_menu():
    while True:
        print("\n=== Customers ===")
        print("1) Add a customer")
        print("2) Find a customer (name + phone)")
        print("3) List all customers")
        print("4) Update a customer")
        print("5) Delete a customer")
        print("6) A customer's cards")
        print("7) Update a card (name / expiration)")
        print("8) Delete a card")
        print("9) Reservations per customer in a year")
        print("10) Frequent customers: bonus mailing list")
        print("11) Mark a bonus as mailed")
        print("0) Back")

        choice = ask("Choose")

        try:
            if choice == "1":
                add_customer()
            elif choice == "2":
                find_customer()
            elif choice == "3":
                list_customers()
            elif choice == "4":
                update_customer()
            elif choice == "5":
                delete_customer()
            elif choice == "6":
                customer_cards()
            elif choice == "7":
                update_card()
            elif choice == "8":
                delete_card()
            elif choice == "9":
                yearly_counts()
            elif choice == "10":
                bonus_list()
            elif choice == "11":
                mark_mailed()
            elif choice == "0":
                return
            else:
                print("Please choose a number from the menu.")

        except (ValueError, pymysql.MySQLError) as e:
            print("\nError:", e)


# reservations


def ask_search():
    city = ask('City')
    check_in = ask('Check-in date (YYYY-MM-DD)')
    check_out = ask('Check-out date (YYYY-MM-DD)')
    bed = ask('Bed size King/Queen/Double (Enter = any)')
    smoking = {'y': True, 'n': False}.get(ask('Smoking? y = smoking, n = non-smoking (Enter = any)')[:1].lower())
    wheelchair = yes('Wheelchair accessible only?')
    return city, check_in, check_out, bed or None, smoking, wheelchair


def ask_room_ids(prompt='Room IDs (comma separated)'):
    return [int(x) for x in ask(prompt).replace(' ', '').split(',') if x]


def ask_card():
    """Card number + expiration (validated right away), then who holds the card."""
    number = ask('Card number')
    month, year = ask('Expiration month (1-12)'), ask('Expiration year')
    customers.clean_card(number, month, year)
    holder = (None, None, None)
    if not yes('Is the guest the card holder?'):
        holder = (ask('Card holder name'), ask('Card holder phone (10 digits)'),
                  ask('Card holder address (optional)') or None)
    return number, month, year, holder


def search_rooms():
    rows = reservations.search_available_rooms(*ask_search())

    if not rows:
        print('  No available rooms found.')
        return

    print("\nHotel ID    Hotel    Room ID    Room    Floor    Location    Bed    Smoking    Wheelchair    Rate")
    print("-" * 110)

    for row in rows:
        print("%-11s %-15s %-10s %-8s %-8s %-12s %-7s %-11s %-13s %s" % (
            row['HotelID'],
            row['Hotel'],
            row['RoomID'],
            row['RoomNumber'],
            row['Floor'],
            row['Direction'],
            row['BedSize'],
            'Yes' if row['SmokingAllowed'] else 'No',
            'Yes' if row['WheelchairAccessible'] else 'No',
            money(row['NightlyRate'])
        ))




def make_reservation():
    city, check_in, check_out, bed, smoking, wheelchair = ask_search()

    rooms = reservations.search_available_rooms(
        city, check_in, check_out, bed, smoking, wheelchair
    )

    if not rooms:
        print('  No available rooms found.')
        return

    print("\nHotel ID    Hotel    Room ID    Room    Floor    Location    Bed    Smoking    Wheelchair    Rate")
    print("-" * 110)

    for row in rooms:
        print("%-11s %-15s %-10s %-8s %-8s %-12s %-7s %-11s %-13s %s" % (
            row['HotelID'],
            row['Hotel'],
            row['RoomID'],
            row['RoomNumber'],
            row['Floor'],
            row['Direction'],
            row['BedSize'],
            'Yes' if row['SmokingAllowed'] else 'No',
            'Yes' if row['WheelchairAccessible'] else 'No',
            money(row['NightlyRate'])
        ))

    hotel_id = ask_int('Hotel ID to book at')
    room_ids = ask_room_ids('Room IDs to book (comma separated)')

    print('\n  Guest (the person staying)')
    name, phone = ask('Full name'), ask('Phone (10 digits)')
    person = customers.find_person(name, phone)

    if person:
        print('  Existing customer #%d found.' % person['PersonID'])
        address = ask('Mailing address [%s] (Enter to keep)' % (person['MailingAddress'] or '')) \
            or person['MailingAddress']
    else:
        print('  New customer.')
        address = ask('Mailing address')

    print('\n  Credit card (required)')
    number, month, year, (h_name, h_phone, h_addr) = ask_card()

    result = reservations.create_reservation(
        name, phone, address, hotel_id, check_in, check_out, room_ids,
        number, month, year, h_name, h_phone, h_addr
    )

    print('\n  Reservation #%d created.' % result['reservation_id'])

    if result['bonus']:
        print('\n  *** %s: Will Receive Bonus ***' % name)



def reservations_for_customer():
    rows = reservations.get_reservations_for_person(
        ask('Customer name'), ask('Phone')
    )

    if not rows:
        print('  No reservations found.')
        return

    print("\nRes #    Hotel    City    Booked    Check-in    Check-out    Nights    Rooms    Status")
    print("-" * 110)

    for row in rows:
        print("%-8s %-15s %-12s %-22s %-12s %-12s %-8s %-7s %s" % (
            row['ReservationID'],
            row['Hotel'],
            row['City'],
            when(row['BookedAtUTC']),
            row['CheckInDate'],
            row['CheckOutDate'],
            row['Nights'],
            row['Rooms'],
            row['Status']
        ))




def change_dates():
    res_id = ask_int('Reservation ID')
    reservations.update_reservation_dates(res_id, ask('New check-in (YYYY-MM-DD)'), ask('New check-out'))
    print('  Dates updated. The cost is recalculated from the stored rates and the new number of nights.')


def change_rooms():
    res_id = ask_int('Reservation ID')
    detail = reservations.get_reservation_detail(res_id)['res']

    rows = reservations.search_available_rooms(
        detail['City'],
        str(detail['CheckInDate']),
        str(detail['CheckOutDate'])
    )

    if not rows:
        print('  No available rooms found.')
        return

    print("\nHotel ID    Hotel    Room ID    Room    Floor    Location    Bed    Smoking    Wheelchair    Rate")
    print("-" * 110)

    for row in rows:
        print("%-11s %-15s %-10s %-8s %-8s %-12s %-7s %-11s %-13s %s" % (
            row['HotelID'],
            row['Hotel'],
            row['RoomID'],
            row['RoomNumber'],
            row['Floor'],
            row['Direction'],
            row['BedSize'],
            'Yes' if row['SmokingAllowed'] else 'No',
            'Yes' if row['WheelchairAccessible'] else 'No',
            money(row['NightlyRate'])
        ))

    reservations.change_rooms(
        res_id,
        ask_room_ids('NEW Room IDs for this reservation (comma separated)')
    )

    print('  Rooms changed.')


def change_guest():
    res_id = ask_int('Reservation ID')
    reservations.change_guest(res_id, ask('Guest full name'), ask('Guest phone'), ask('Guest mailing address'))
    print('  Guest changed.')


def change_card():
    res_id = ask_int('Reservation ID')
    number, month, year, (h_name, h_phone, h_addr) = ask_card()
    reservations.change_card(res_id, number, month, year, h_name, h_phone, h_addr)
    print('  Card changed.')


def cancel():
    res_id = ask_int('Reservation ID')
    if not yes('Cancel reservation %d?' % res_id):
        return
    result = reservations.cancel_reservation(res_id)
    if result['late']:
        print('  Cancelled. Less than 48 hours before check-in: %s charged to the card.' % money(result['fee']))
    else:
        print('  Cancelled. No fee (more than 48 hours before check-in).')


def check_in_guest():
    reservations.check_in_guest(ask_int('Reservation ID'))
    print('  Guest checked in.')


def check_out_guest():
    reservations.check_out_guest(ask_int('Reservation ID'))
    print('  Guest checked out.')


def late_arrivals():
    rows = reservations.get_late_arrivals()

    if not rows:
        print('  No late arrivals found.')
        return

    print("\nRes #    Guest    Phone    Hotel    Scheduled check-in    Rooms")
    print("-" * 90)

    for row in rows:
        print("%-8s %-18s %-12s %-15s %-22s %s" % (
            row['ReservationID'],
            row['FullName'],
            row['Phone'],
            row['Hotel'],
            row['ScheduledLocal'],
            row['Rooms']
        ))


def charge_no_show():
    fee = reservations.charge_no_show(ask_int('Reservation ID'))
    print('  No-show fee charged: %s. The reservation is now marked NoShow.' % money(fee))


def reservations_menu():
    while True:
        print("\n=== Reservations ===")
        print("1) Search available rooms")
        print("2) Make a reservation")
        print("3) A customer's reservations")
        print("4) Change dates")
        print("5) Change rooms")
        print("6) Change guest")
        print("7) Change credit card")
        print("8) Cancel a reservation")
        print("9) Check a guest in")
        print("10) Check a guest out")
        print("11) Late arrivals")
        print("12) Charge a no-show fee")
        print("0) Back")

        choice = ask("Choose")

        try:
            if choice == "1":
                search_rooms()
            elif choice == "2":
                make_reservation()
            elif choice == "3":
                reservations_for_customer()
            elif choice == "4":
                change_dates()
            elif choice == "5":
                change_rooms()
            elif choice == "6":
                change_guest()
            elif choice == "7":
                change_card()
            elif choice == "8":
                cancel()
            elif choice == "9":
                check_in_guest()
            elif choice == "10":
                check_out_guest()
            elif choice == "11":
                late_arrivals()
            elif choice == "12":
                charge_no_show()
            elif choice == "0":
                return
            else:
                print("Please choose a number from the menu.")

        except (ValueError, pymysql.MySQLError) as e:
            print("\nError:", e)

# charges


def show_charges(rows):
    if not rows:
        print('  No charges found.')
        return

    print("\nCharge #    Date    Type    Description    Amount    Res #    Hotel    Card")
    print("-" * 110)

    for row in rows:
        print("%-11s %-22s %-8s %-20s %-10s %-8s %-15s %s" % (
            row['ChargeID'],
            when(row['ChargedAtUTC']),
            row['ChargeType'],
            row['Description'],
            money(row['Amount']),
            row['ReservationID'],
            row['Hotel'],
            '%s ****%s' % (row['CardholderName'], row['Last4'])
        ))

    print('\n  Total: %s' % money(charges.total(rows)))


def charges_for_customer():
    show_charges(charges.get_charges_for_person(ask('Customer name'), ask('Phone')))


def charges_for_reservation():
    show_charges(charges.get_charges_for_reservation(ask_int('Reservation ID')))


def add_charge():
    res_id = ask_int('Reservation ID')
    charge_type = ask('Type (Room / Food)')
    amount = ask('Amount')
    description = ask('Description (required for Food)')
    print('  Charge #%d added.' % charges.add_charge(res_id, charge_type, amount, description))


def add_amenity_charge():
    res_id = ask_int('Reservation ID')
    rows = charges.paid_amenities(res_id)

    if not rows:
        print('  No paid amenities found.')
        return

    print("\nAmenity ID    Amenity    Price")
    print("-" * 45)

    for row in rows:
        print("%-13s %-20s %s" % (
            row['AmenityID'],
            row['AmenityName'],
            money(row['Price'])
        ))

    charge_id, amount = charges.add_amenity_charge(
        res_id,
        ask_int('Amenity ID'),
        ask('Quantity (1)') or 1
    )

    print('  Charge #%d added: %s' % (charge_id, money(amount)))


def post_room_charges():
    print('  Room charges posted: %s' % money(charges.post_room_charges(ask_int('Reservation ID'))))


def update_charge():
    charge = charges.get_charge(ask_int('Charge ID'))
    print('  (press Enter to keep the current value)')
    amount = ask('Amount [%s]' % charge['Amount']) or charge['Amount']
    description = ask('Description [%s]' % charge['Description']) or charge['Description']
    charges.update_charge(charge['ChargeID'], amount, description)
    print('  Charge updated.')


def delete_charge():
    charge_id = ask_int('Charge ID')
    if yes('Delete charge %d?' % charge_id):
        charges.delete_charge(charge_id)
        print('  Charge deleted.')


def charges_menu():
    while True:
        print("\n=== Charges ===")
        print("1) A customer's charges (itemized)")
        print("2) A reservation's charges")
        print("3) Add a Room / Food charge")
        print("4) Charge a paid amenity")
        print("5) Post room charges")
        print("6) Change a charge")
        print("7) Delete / waive a charge")
        print("0) Back")

        choice = ask("Choose")

        try:
            if choice == "1":
                charges_for_customer()
            elif choice == "2":
                charges_for_reservation()
            elif choice == "3":
                add_charge()
            elif choice == "4":
                add_amenity_charge()
            elif choice == "5":
                post_room_charges()
            elif choice == "6":
                update_charge()
            elif choice == "7":
                delete_charge()
            elif choice == "0":
                return
            else:
                print("Please choose a number from the menu.")

        except (ValueError, pymysql.MySQLError) as e:
            print("\nError:", e)


if __name__ == "__main__":
    main()
