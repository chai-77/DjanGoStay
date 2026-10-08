from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from billings.models import Bill
from bookings.models import Booking, Customer
from staff.models import Staff

from .forms import HousekeepingAssignmentForm
from .models import HousekeepingAssignment, Room, RoomType


class DemoSeedCommandTests(TestCase):
	def test_demo_seed_is_repeatable_without_duplicates(self):
		call_command('seed_demo', verbosity=0)
		call_command('seed_demo', verbosity=0)

		self.assertEqual(RoomType.objects.count(), 3)
		self.assertEqual(Room.objects.count(), 3)
		self.assertEqual(Customer.objects.count(), 3)
		self.assertEqual(Booking.objects.count(), 3)
		self.assertEqual(HousekeepingAssignment.objects.count(), 2)
		self.assertEqual(Bill.objects.count(), 2)


class RoomModelTests(TestCase):
	def setUp(self):
		self.room_type = RoomType.objects.create(
			room_type_name='Standard',
			room_price=Decimal('100.00'),
			room_capacity=2,
		)

	def test_room_number_is_normalized_before_save(self):
		room = Room.objects.create(
			room_number='  3   b  ',
			room_type=self.room_type,
		)

		self.assertEqual(room.room_number, '3 B')

	def test_normalized_room_numbers_must_be_unique(self):
		Room.objects.create(room_number='3 B', room_type=self.room_type)

		with self.assertRaises(ValidationError):
			Room.objects.create(room_number=' 3   b ', room_type=self.room_type)

	def test_room_type_rejects_non_positive_price_or_capacity(self):
		for room_price, room_capacity in (
			(Decimal('0.00'), 2),
			(Decimal('100.00'), 0),
		):
			with self.subTest(room_price=room_price, room_capacity=room_capacity):
				room_type = RoomType(
					room_type_name='Invalid',
					room_price=room_price,
					room_capacity=room_capacity,
				)
				with self.assertRaises(ValidationError):
					room_type.save()


class HousekeepingFormTests(TestCase):
	def test_assignment_form_only_offers_housekeeping_staff(self):
		housekeeping_user = User.objects.create_user(username='housekeeping')
		manager_user = User.objects.create_user(username='manager')
		housekeeping_staff = Staff.objects.create(
			user=housekeeping_user,
			first_name='House',
			last_name='Keeper',
			phone_number='5553000001',
			role='housekeeping',
			salary=Decimal('28000.00'),
			date_of_joining=date.today(),
		)
		manager_staff = Staff.objects.create(
			user=manager_user,
			first_name='Hotel',
			last_name='Manager',
			phone_number='5553000002',
			role='manager',
			salary=Decimal('50000.00'),
			date_of_joining=date.today(),
		)

		form = HousekeepingAssignmentForm()

		self.assertIn(housekeeping_staff, form.fields['assigned_to'].queryset)
		self.assertNotIn(manager_staff, form.fields['assigned_to'].queryset)

	def test_assignment_form_rejects_duplicate_room_staff_and_date(self):
		user = User.objects.create_user(username='housekeeping_duplicate')
		staff = Staff.objects.create(
			user=user,
			first_name='House',
			last_name='Keeper',
			phone_number='5553000010',
			role='housekeeping',
			salary=Decimal('28000.00'),
			date_of_joining=date.today(),
		)
		room_type = RoomType.objects.create(
			room_type_name='Duplicate Test Room',
			room_price=Decimal('100.00'),
			room_capacity=2,
		)
		room = Room.objects.create(room_number='DUP-101', room_type=room_type)
		assignment_date = date(2026, 9, 29)
		HousekeepingAssignment.objects.create(
			room=room,
			assigned_to=staff,
			assignment_date=assignment_date,
		)

		form = HousekeepingAssignmentForm(data={
			'room': room.pk,
			'assigned_to': staff.pk,
			'assignment_date': assignment_date.isoformat(),
			'is_completed': False,
		})

		self.assertFalse(form.is_valid())
		self.assertIn('__all__', form.errors)


class RoomRoleAccessTests(TestCase):
	def test_housekeeping_can_open_rooms_but_not_room_type_management(self):
		user = User.objects.create_user(username='housekeeping', password='password')
		Staff.objects.create(
			user=user,
			first_name='House',
			last_name='Keeper',
			phone_number='5553000003',
			role='housekeeping',
			salary=Decimal('28000.00'),
			date_of_joining=date.today(),
		)
		self.client.force_login(user)

		self.assertEqual(self.client.get(reverse('room_list')).status_code, 200)
		self.assertEqual(self.client.get(reverse('room_type_list')).status_code, 403)
