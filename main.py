from collections import UserDict
from datetime import datetime, date, timedelta
from typing import Optional, List


class AddressBookError(Exception):
    """Base exception class for Address Book application."""
    pass


class PhoneValidationError(AddressBookError):
    """Raised when the phone number validation fails."""
    pass


class BirthdayValidationError(AddressBookError):
    """Raised when the birthday validation fails."""
    pass


class Field:
    """Base class for record fields."""
    def __init__(self, value: str):
        self._value = None
        self.value = value

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, new_value: str):
        self._value = new_value

    def __str__(self) -> str:
        return str(self.value)


class Name(Field):
    """Field for storing a contact name. Mandatory field."""
    pass


class Phone(Field):
    """Field for storing a phone number with 10-digit validation."""
    @Field.value.setter
    def value(self, new_value: str):
        clean_phone = new_value.strip()
        if not (len(clean_phone) == 10 and clean_phone.isdigit()):
            raise PhoneValidationError("Phone number must contain exactly 10 digits.")
        self._value = clean_phone


class Birthday(Field):
    """Field for storing a birthday in DD.MM.YYYY format."""

    @Field.value.setter
    def value(self, new_value: str):
        try:
            self._value = datetime.strptime(new_value, "%d.%m.%Y").date()
        except ValueError:
            raise BirthdayValidationError("Birthday must be in DD.MM.YYYY format.")

    def __str__(self):
        """Return the date formatted as DD.MM.YYYY."""
        return self.value.strftime("%d.%m.%Y")


class Record:
    """Class for managing contact information and phone numbers."""
    def __init__(self, name: str):
        self.name: Name = Name(name)
        self.phones: List[Phone] = []
        self.birthday: Optional[Birthday] = None

    def add_phone(self, phone_number: str) -> None:
        """Adds a new phone number if it doesn't already exist."""
        if not self.find_phone(phone_number):
            self.phones.append(Phone(phone_number))

    def remove_phone(self, phone_number: str) -> None:
        """Removes a phone number. Silent if not found for safety."""
        phone_obj = self.find_phone(phone_number)
        if phone_obj:
            self.phones.remove(phone_obj)

    def edit_phone(self, old_phone: str, new_phone: str) -> None:
        """Updates an existing phone number. Validates new phone before changing."""
        old_phone_obj = self.find_phone(old_phone)
        if old_phone_obj:
            new_phone_obj = Phone(new_phone)
            index = self.phones.index(old_phone_obj)
            self.phones[index] = new_phone_obj

    def find_phone(self, phone_number: str) -> Optional[Phone]:
        """Searches for a phone number and returns the Phone object."""
        for phone in self.phones:
            if phone.value == phone_number.strip():
                return phone
        return None

    def add_birthday(self, birthday_str: str):
        """Add or update the birthday for the contact."""
        self.birthday = Birthday(birthday_str)

    def __str__(self):
        """Return a string representation of the contact record."""
        phones = "; ".join(p.value for p in self.phones)
        birthday = f", birthday: {self.birthday}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {phones}{birthday}"


class AddressBook(UserDict):
    """Storage for contact records, inheriting from UserDict."""
    def add_record(self, record: Record) -> None:
        """Adds a record to the address book."""
        self.data[record.name.value] = record

    def find(self, name: str) -> Optional[Record]:
        """Finds a record by name."""
        return self.data.get(name)

    def delete(self, name: str) -> None:
        """Deletes a record by name. Silent if not found."""
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self) -> List[dict]:
        """Return a list of contacts to congratulate within the next 7 days."""
        today = date.today()
        upcoming = []

        for record in self.data.values():
            if not record.birthday:
                continue

            bday = record.birthday.value
            bday_this_year = bday.replace(year=today.year)

            if bday_this_year < today:
                bday_this_year = bday_this_year.replace(year=today.year + 1)

            if 0 <= (bday_this_year - today).days <= 7:
                congrats_date = bday_this_year
                if congrats_date.weekday() == 5:
                    congrats_date += timedelta(days=2)
                elif congrats_date.weekday() == 6:
                    congrats_date += timedelta(days=1)

                upcoming.append({
                    "name": record.name.value,
                    "congratulation_date": congrats_date.strftime("%d.%m.%Y")
                })
        return upcoming


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (PhoneValidationError, BirthdayValidationError) as e:
            return str(e)
        except KeyError:
            return "Contact not found."
        except ValueError:
            return "Give me valid arguments please."
        except IndexError:
            return "Not enough arguments."
    return inner


def parse_input(user_input: str):
    user_input = user_input.strip()
    if not user_input:
        return "", []
    parts = user_input.split()
    command = parts[0].lower()
    args = parts[1:]
    return command, args


@input_error
def add_contact(args, book: AddressBook):
    name, phone = args[0], args[1]
    record = book.find(name)
    if record is None:
        record = Record(name)
        book.add_record(record)
    record.add_phone(phone)
    return "Contact added."


@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone = args[0], args[1], args[2]
    record = book.find(name)
    if record is None:
        raise KeyError
    record.edit_phone(old_phone, new_phone)
    return "Contact updated."


@input_error
def show_phone(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError
    return "; ".join(p.value for p in record.phones)


@input_error
def show_all(args, book: AddressBook):
    if not book.data:
        return "No contacts."

    lines = []
    for record in book.data.values():
        phones = "; ".join(p.value for p in record.phones)
        birthday = str(record.birthday) if record.birthday else "-"
        lines.append(f"{record.name.value}: {phones} | birthday: {birthday}")

    return "\n".join(lines)


@input_error
def add_birthday(args, book: AddressBook):
    name, birthday_str = args[0], args[1]
    record = book.find(name)
    if record is None:
        raise KeyError
    record.add_birthday(birthday_str)
    return "Birthday added."


@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError
    if record.birthday is None:
        return "Birthday is not set."
    return str(record.birthday)


@input_error
def birthdays(args, book: AddressBook):
    """Handle 'birthdays' command: show upcoming birthdays for the next week."""
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No upcoming birthdays in the next 7 days."
    return "\n".join(f"{i['name']}: {i['congratulation_date']}" for i in upcoming)


def main():
    book = AddressBook()
    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all(args, book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        elif command == "":
            continue

        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()