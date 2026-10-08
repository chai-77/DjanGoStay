from datetime import date

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from staff.models import Staff


DEMO_ROLES = [
    {
        'username': 'arjun_manager',
        'first_name': 'Arjun',
        'last_name': 'Mehta',
        'phone_number': '9100000011',
        'role': 'manager',
        'salary': '60000.00',
    },
    {
        'username': 'priya_receptionist',
        'first_name': 'Priya',
        'last_name': 'Shah',
        'phone_number': '9100000012',
        'role': 'receptionist',
        'salary': '35000.00',
    },
    {
        'username': 'asha_housekeeping',
        'first_name': 'Asha',
        'last_name': 'Patel',
        'phone_number': '9100000013',
        'role': 'housekeeping',
        'salary': '28000.00',
    },
    {
        'username': 'rohan_finance',
        'first_name': 'Rohan',
        'last_name': 'Kapoor',
        'phone_number': '9100000014',
        'role': 'finance',
        'salary': '50000.00',
    },
    {
        'username': 'neha_cook',
        'first_name': 'Neha',
        'last_name': 'Iyer',
        'phone_number': '9100000015',
        'role': 'cook',
        'salary': '30000.00',
    },
    {
        'username': 'vikram_server',
        'first_name': 'Vikram',
        'last_name': 'Rao',
        'phone_number': '9100000016',
        'role': 'server',
        'salary': '27000.00',
    },
    {
        'username': 'kavya_maintenance',
        'first_name': 'Kavya',
        'last_name': 'Nair',
        'phone_number': '9100000017',
        'role': 'maintenance',
        'salary': '29000.00',
    },
]


class Command(BaseCommand):
    help = 'Create or update the repeatable demonstration staff accounts.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            default='DjangoStay1',
            help='Password assigned to each demonstration account.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options['password']
        for values in DEMO_ROLES:
            username = values['username']
            user, _ = User.objects.get_or_create(username=username)
            user.first_name = values['first_name']
            user.last_name = values['last_name']
            user.is_active = True
            user.set_password(password)
            user.save()

            Staff.objects.update_or_create(
                user=user,
                defaults={
                    'first_name': values['first_name'],
                    'last_name': values['last_name'],
                    'phone_number': values['phone_number'],
                    'role': values['role'],
                    'salary': values['salary'],
                    'date_of_joining': date(2026, 1, 1),
                },
            )

        self.stdout.write(self.style.SUCCESS('Demo role accounts are ready.'))
