from datetime import date
from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from billings.models import Bill, Charge, Discount, Payment
from bookings.models import Booking, Customer
from rooms.models import HousekeepingAssignment, Room, RoomType
from staff.models import Staff


ROOM_TYPES = [
    {
        'room_type_name': 'Standard Room',
        'room_price': Decimal('100.00'),
        'room_capacity': 2,
    },
    {
        'room_type_name': 'Deluxe Room',
        'room_price': Decimal('175.00'),
        'room_capacity': 3,
    },
    {
        'room_type_name': 'Family Suite',
        'room_price': Decimal('300.00'),
        'room_capacity': 4,
    },
]

ROOMS = [
    {'room_number': '101', 'room_type': 'Standard Room', 'is_available': True},
    {'room_number': '102', 'room_type': 'Deluxe Room', 'is_available': True},
    {'room_number': '201', 'room_type': 'Family Suite', 'is_available': False},
]

CUSTOMERS = [
    {
        'email': 'demo.ananya@example.com',
        'first_name': 'Ananya',
        'last_name': 'Rao',
        'phone_number': '9100000001',
        'address': '12 MG Road, Bengaluru',
    },
    {
        'email': 'demo.rohit@example.com',
        'first_name': 'Rohit',
        'last_name': 'Kapoor',
        'phone_number': '9100000002',
        'address': '45 Park Street, Kolkata',
    },
    {
        'email': 'demo.meera@example.com',
        'first_name': 'Meera',
        'last_name': 'Joshi',
        'phone_number': '9100000003',
        'address': '8 FC Road, Pune',
    },
]

BOOKINGS = [
    {
        'customer_email': 'demo.ananya@example.com',
        'room_number': '101',
        'check_in_date': date(2026, 9, 20),
        'check_out_date': date(2026, 9, 23),
        'number_of_guests': 2,
        'status': 'confirmed',
    },
    {
        'customer_email': 'demo.rohit@example.com',
        'room_number': '102',
        'check_in_date': date(2026, 9, 25),
        'check_out_date': date(2026, 9, 28),
        'number_of_guests': 1,
        'status': 'pending',
    },
    {
        'customer_email': 'demo.meera@example.com',
        'room_number': '201',
        'check_in_date': date(2026, 9, 14),
        'check_out_date': date(2026, 9, 18),
        'number_of_guests': 3,
        'status': 'checked_in',
    },
]


class Command(BaseCommand):
    help = 'Restore the repeatable demonstration dataset without deleting other data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            default='DjangoStay1',
            help='Password used if the role accounts need to be created.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        call_command(
            'seed_roles',
            password=options['password'],
            verbosity=0,
        )

        room_types = self._seed_room_types()
        rooms = self._seed_rooms(room_types)
        customers = self._seed_customers()
        bookings = self._seed_bookings(customers, rooms)
        self._seed_housekeeping(rooms)
        self._seed_billing(bookings)

        self.stdout.write(self.style.SUCCESS(
            'Demo data is ready. Existing non-demo data was not deleted.'
        ))
        self.stdout.write(
            'Run `python manage.py seed_demo` again to restore/update it.'
        )

    def _seed_room_types(self):
        room_types = {}
        for values in ROOM_TYPES:
            room_type, _ = RoomType.objects.update_or_create(
                room_type_name=values['room_type_name'],
                defaults=values,
            )
            room_types[room_type.room_type_name] = room_type
        return room_types

    def _seed_rooms(self, room_types):
        rooms = {}
        for values in ROOMS:
            room, _ = Room.objects.update_or_create(
                room_number=values['room_number'],
                defaults={
                    'room_type': room_types[values['room_type']],
                    'is_available': values['is_available'],
                },
            )
            rooms[room.room_number] = room
        return rooms

    def _seed_customers(self):
        customers = {}
        for values in CUSTOMERS:
            customer, _ = Customer.objects.update_or_create(
                email=values['email'],
                defaults=values,
            )
            customers[customer.email] = customer
        return customers

    def _seed_bookings(self, customers, rooms):
        bookings = []
        for values in BOOKINGS:
            customer = customers[values['customer_email']]
            room = rooms[values['room_number']]
            booking, _ = Booking.objects.update_or_create(
                customer=customer,
                room=room,
                check_in_date=values['check_in_date'],
                defaults={
                    'check_out_date': values['check_out_date'],
                    'number_of_guests': values['number_of_guests'],
                    'status': values['status'],
                },
            )
            bookings.append(booking)
        return bookings

    def _seed_housekeeping(self, rooms):
        housekeeper = Staff.objects.get(user__username='asha_housekeeping')
        assignments = [
            {
                'room': rooms['101'],
                'assignment_date': date(2026, 9, 16),
                'is_completed': False,
            },
            {
                'room': rooms['102'],
                'assignment_date': date(2026, 9, 15),
                'is_completed': True,
            },
        ]
        for values in assignments:
            HousekeepingAssignment.objects.update_or_create(
                room=values['room'],
                assignment_date=values['assignment_date'],
                defaults={
                    'assigned_to': housekeeper,
                    'is_completed': values['is_completed'],
                },
            )

    def _seed_billing(self, bookings):
        bill, _ = Bill.objects.get_or_create(booking=bookings[0])
        charge, _ = Charge.objects.get_or_create(
            bill=bill,
            description='Three-night room charge',
            defaults={'amount': Decimal('300.00')},
        )
        charge.amount = Decimal('300.00')
        charge.save(update_fields=['amount'])
        discount, _ = Discount.objects.get_or_create(
            bill=bill,
            description='Demo loyalty discount',
            defaults={'amount': Decimal('25.00')},
        )
        discount.amount = Decimal('25.00')
        discount.save(update_fields=['amount'])
        payment, _ = Payment.objects.get_or_create(
            bill=bill,
            payment_method='credit_card',
            defaults={'amount': Decimal('100.00')},
        )
        payment.amount = Decimal('100.00')
        payment.save(update_fields=['amount'])

        second_bill, _ = Bill.objects.get_or_create(booking=bookings[1])
        Charge.objects.get_or_create(
            bill=second_bill,
            description='Estimated room charge',
            defaults={'amount': Decimal('525.00')},
        )
