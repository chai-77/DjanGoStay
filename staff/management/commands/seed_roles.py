import os
from datetime import date

from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand
from django.db import transaction

from staff.models import Staff


ROLE_USERS = [
    {
        'username': 'arjun_manager',
        'email': 'arjun.manager@example.com',
        'first_name': 'Arjun',
        'last_name': 'Mehta',
        'phone_number': '9000000001',
        'role': 'manager',
    },
    {
        'username': 'priya_receptionist',
        'email': 'priya.receptionist@example.com',
        'first_name': 'Priya',
        'last_name': 'Sharma',
        'phone_number': '9000000002',
        'role': 'receptionist',
    },
    {
        'username': 'asha_housekeeping',
        'email': 'asha.housekeeping@example.com',
        'first_name': 'Asha',
        'last_name': 'Patel',
        'phone_number': '9000000003',
        'role': 'housekeeping',
    },
    {
        'username': 'rohan_finance',
        'email': 'rohan.finance@example.com',
        'first_name': 'Rohan',
        'last_name': 'Gupta',
        'phone_number': '9000000004',
        'role': 'finance',
    },
    {
        'username': 'neha_cook',
        'email': 'neha.cook@example.com',
        'first_name': 'Neha',
        'last_name': 'Iyer',
        'phone_number': '9000000005',
        'role': 'cook',
    },
    {
        'username': 'vikram_server',
        'email': 'vikram.server@example.com',
        'first_name': 'Vikram',
        'last_name': 'Singh',
        'phone_number': '9000000006',
        'role': 'server',
    },
    {
        'username': 'kavya_maintenance',
        'email': 'kavya.maintenance@example.com',
        'first_name': 'Kavya',
        'last_name': 'Nair',
        'phone_number': '9000000007',
        'role': 'maintenance',
    },
]

ROLE_PERMISSIONS = {
    'manager': {
        'rooms': ['room', 'roomtype', 'housekeepingassignment'],
        'bookings': ['customer', 'booking'],
        'billings': ['bill', 'charge', 'discount', 'payment'],
        'staff': ['staff'],
    },
    'receptionist': {
        'rooms': ['room'],
        'bookings': ['customer', 'booking'],
    },
    'housekeeping': {
        'rooms': ['room', 'roomtype', 'housekeepingassignment'],
    },
    'finance': {
        'billings': ['bill', 'charge', 'discount', 'payment'],
    },
    'cook': {},
    'server': {},
    'maintenance': {},
}


class Command(BaseCommand):
    help = 'Create the standard hotel role users, staff profiles, groups, and permissions.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            default=os.getenv('DJANGO_SEED_PASSWORD', 'DjangoStay1'),
            help='Password for accounts created or updated by this command.',
        )
        parser.add_argument(
            '--salary',
            default='30000.00',
            help='Initial salary assigned to generated staff profiles.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options['password']
        salary = options['salary']
        created_users = []

        self._configure_groups()

        for account in ROLE_USERS:
            user, created = User.objects.get_or_create(
                username=account['username'],
                defaults={'email': account['email']},
            )
            user.email = account['email']
            user.first_name = account['first_name']
            user.last_name = account['last_name']
            user.set_password(password)
            user.is_active = True
            user.is_staff = account['role'] == 'manager'
            user.save()

            staff, _ = Staff.objects.get_or_create(
                user=user,
                defaults={
                    'first_name': account['first_name'],
                    'last_name': account['last_name'],
                    'phone_number': account['phone_number'],
                    'role': account['role'],
                    'salary': salary,
                    'date_of_joining': date.today(),
                },
            )
            staff.first_name = account['first_name']
            staff.last_name = account['last_name']
            staff.role = account['role']
            staff.salary = salary
            staff.save(update_fields=[
                'first_name',
                'last_name',
                'role',
                'salary',
            ])

            user.groups.set([Group.objects.get(name=account['role'].title())])
            created_users.append((account['username'], account['role'], created))

        self.stdout.write(self.style.SUCCESS('Role accounts are ready:'))
        for username, role, created in created_users:
            state = 'created' if created else 'updated'
            self.stdout.write(f'  {username}: {role} ({state})')
        self.stdout.write(
            'Password used for these seeded accounts: '
            f'{password}'
        )
        self.stdout.write(
            self.style.WARNING(
                'Cook, server, and maintenance currently have no CRUD landing page '
                'because no views grant those roles access.'
            )
        )

    def _configure_groups(self):
        for role, model_map in ROLE_PERMISSIONS.items():
            group, _ = Group.objects.get_or_create(name=role.title())
            permissions = []
            for app_label, model_names in model_map.items():
                for model_name in model_names:
                    permissions.extend(
                        Permission.objects.filter(
                            content_type__app_label=app_label,
                            content_type__model=model_name,
                            codename__in=[
                                f'{action}_{model_name}'
                                for action in ('add', 'change', 'delete', 'view')
                            ],
                        )
                    )
            group.permissions.set(permissions)
