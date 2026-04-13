from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import ClassVar

from app.services.util import (
    generate_unique_id,
    guest_not_found_error,
    room_not_available_error,
    reservation_not_found_error, room_already_exists_error, date_lower_than_today_error, room_not_found_error
)

@dataclass
class Guest:
    REGULAR: ClassVar = "regular"
    VIP: ClassVar = "vip"

    name: str
    email: str
    type_: str = REGULAR

    def __str__(self) -> str:
        return f"Guest {self.name} ({self.email}) of type {self.type_}"


@dataclass
class Reservation:
    guest_name: str
    description: str
    check_in: date
    check_out: date
    guests: list[Guest] = field(default_factory=list)
    id: str = field(default_factory=generate_unique_id)

    def add_guest(self, name: str, email: str, type_: str = Guest.REGULAR):
        self.guests.append(Guest(name, email, type_))

    def delete_guest(self, guest_index: int):
        if 0 <= guest_index < len(self.guests):
            self.guests.pop(guest_index)
        else:
            guest_not_found_error()

    def __len__(self) -> int:
        return (self.check_out - self.check_in).days

    def __str__(self) -> str:
        return (
            f"ID: {self.id}\n"
            f"Guest: {self.guest_name}\n"
            f"Description: {self.description}\n"
            f"Dates: {self.check_in} - {self.check_out}"
        )


class Room:
    def __init__(self, number: int, type_: str, price_per_night: float):
        self.number = number
        self.type_ = type_
        self.price_per_night = price_per_night
        self.availability: dict[date, str | None] = {}
        self._init_availability()

    def _init_availability(self):
        today = datetime.now().date()
        for i in range(365):
            self.availability[today + timedelta(days=i)] = None

    def book(self, reservation_id: str, check_in: date, check_out: date):
        current = check_in
        while current < check_out:
            if self.availability.get(current) is not None:
                room_not_available_error()
            current += timedelta(days=1)

        current = check_in
        while current < check_out:
            self.availability[current] = reservation_id
            current += timedelta(days=1)

    def release(self, reservation_id: str):
        released = False
        for d, saved_id in self.availability.items():
            if saved_id == reservation_id:
                self.availability[d] = None
                released = True
        if not released:
            reservation_not_found_error()

    def update_booking(self, reservation_id: str, check_in: date, check_out: date):
        for d in self.availability:
            if self.availability[d] == reservation_id:
                self.availability[d] = None

        current = check_in
        while current < check_out:
            if self.availability.get(current) is not None:
                room_not_available_error()
            self.availability[current] = reservation_id
            current += timedelta(days=1)

class Hotel:
    def __init__(self):
        self.rooms: dict[int, Room] = {}
        self.reservations: dict[str, Reservation] = {}

    def add_room(self, number: int, type_: str, price_per_night: float):
        if number in self.rooms:
            room_already_exists_error()
        else:
            self.rooms[number] = Room(number, type_, price_per_night)

    def make_reservation(self, guest_name: str, description: str, room_number: int, check_in: date, check_out: date):
        today = datetime.now().date()
        if check_in < today:
            date_lower_than_today_error()

        elif room_number not in self.rooms:
            room_not_found_error()
        else:
            reservation = Reservation(guest_name, description, check_in, check_out)

            self.rooms[room_number].book(reservation.id, check_in, check_out)

            self.reservations[reservation.id] = reservation

            return reservation.id

    def add_guest(self, reservation_id: str, name: str, email: str, type_, str):
        if reservation_id not in self.reservations:
            reservation_not_found_error()
        else:
            self.reservations[reservation_id].add_guest(name, email, type_)

    def find_available_rooms(self, check_in: date, check_out: date) -> list[int]:
       pass

    def update_reservation(self, reservation_id: str, guest_name: str, description: str,
                           room_number: int, check_in: date, check_out: date):
        reservation = self.reservations.get(reservation_id)
        if not reservation:
            reservation_not_found_error()

        current_room_number = None
        for number, room in self.rooms.items():
            if reservation_id in room.availability.values():
                current_room_number = number
                break

        is_new_room = False

        if current_room_number != room_number:
            self.cancel_reservation(reservation_id)
            reservation = Reservation(guest_name=guest_name, description=description,
                                      check_in=check_in, check_out=check_out)
            reservation.id = reservation_id
            self.reservations[reservation_id] = reservation
            is_new_room = True
            if room_number not in self.rooms:
                room_not_found_error()
            self.rooms[room_number].book(reservation_id, check_in, check_out)
        else:
            reservation.guest_name = guest_name
            reservation.description = description
            reservation.check_in = check_in
            reservation.check_out = check_out

        if not is_new_room and current_room_number is not None:
            self.rooms[current_room_number].update_booking(reservation_id, check_in, check_out)

    def cancel_reservation(self, reservation_id: str):
        if reservation_id not in self.reservations:
            reservation_not_found_error()

        self.reservations.pop(reservation_id)

        for room in self.rooms.values():
            if reservation_id in room.availability.values():
                room.release(reservation_id)
                break

    def find_reservations(self, start_date: date, end_date: date) -> dict[date, list[Reservation]]:
        reservations: dict[date, list[Reservation]] = {}
        for reservation in self.reservations.values():
            if start_date <= reservation.check_in <= end_date:
                if reservation.check_in not in reservations:
                    reservations[reservation.check_in] = []
                reservations[reservation.check_in].append(reservation)
        return reservations

    def delete_guest(self, reservation_id: str, guest_index: int):
        reservation = self.reservations.get(reservation_id)
        if not reservation:
            reservation_not_found_error()

        reservation.delete_guest(guest_index)

    def list_guests(self, reservation_id: str) -> list[Guest]:
        reservation = self.reservations.get(reservation_id)
        if not reservation:
            reservation_not_found_error()

        return reservation.guests