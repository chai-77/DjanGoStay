from datetime import date, datetime, time, timedelta, timezone as datetime_timezone
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from billings.models import Bill, Charge, Payment
from rooms.models import Room, RoomType
from staff.models import Staff

from .forms import BookingForm
from .models import Booking, BookingStatus, Customer
from .services import BookingService


class BookingFixtureMixin:
	def setUp(self):
		self.today = date.today()
		self.check_in = self.today + timedelta(days=2)
		self.check_out = self.today + timedelta(days=5)
		self.user = User.objects.create_user(username='manager', password='password')
		Staff.objects.create(
			user=self.user,
			first_name='Hotel',
			last_name='Manager',
			phone_number='5551000001',
			role='manager',
			salary=Decimal('50000.00'),
			date_of_joining=self.today,
		)
		self.customer = Customer.objects.create(
			first_name='Guest',
			last_name='One',
			email='guest@example.com',
			phone_number='5551000002',
			address='Hotel address',
		)
		self.room_type = RoomType.objects.create(
			room_type_name='Standard',
			room_price=Decimal('100.00'),
			room_capacity=2,
		)
		self.room = Room.objects.create(room_number='101', room_type=self.room_type)
		self.booking = Booking.objects.create(
			customer=self.customer,
			room=self.room,
			check_in_date=self.check_in,
			check_out_date=self.check_out,
			number_of_guests=2,
		)

	def booking_form(self, *, room=None, check_in=None, check_out=None, guests=1):
		return BookingForm(data={
			'customer': self.customer.pk,
			'room': (room or self.room).pk,
			'check_in_date': (check_in or self.check_in).isoformat(),
			'check_out_date': (check_out or self.check_out).isoformat(),
			'number_of_guests': guests,
		})


class CustomerModelTests(TestCase):
	def test_save_normalizes_email_and_phone_number(self):
		customer = Customer.objects.create(
			first_name='Guest',
			last_name='Two',
			email='GUEST.TWO@EXAMPLE.COM',
			phone_number='+1 (555) 123-4567',
			address='Hotel address',
		)

		self.assertEqual(customer.email, 'guest.two@example.com')
		self.assertEqual(customer.phone_number, '15551234567')

	def test_save_rejects_a_missing_phone_number(self):
		customer = Customer(
			first_name='Guest',
			last_name='Three',
			email='guest.three@example.com',
			phone_number='letters only',
			address='Hotel address',
		)

		with self.assertRaises(ValidationError):
			customer.save()


class BookingFormTests(BookingFixtureMixin, TestCase):
	def test_rejects_overlapping_stay(self):
		form = self.booking_form(
			check_in=self.check_in + timedelta(days=1),
			check_out=self.check_out + timedelta(days=1),
		)

		self.assertFalse(form.is_valid())
		self.assertIn('__all__', form.errors)

	def test_allows_half_open_adjacent_stays(self):
		form = self.booking_form(
			check_in=self.check_out,
			check_out=self.check_out + timedelta(days=2),
		)

		self.assertTrue(form.is_valid(), form.errors)

	def test_ignores_canceled_and_checked_out_bookings_for_conflicts(self):
		for status in (BookingStatus.CANCELED, BookingStatus.CHECKED_OUT):
			with self.subTest(status=status):
				Booking.objects.filter(pk=self.booking.pk).update(status=status)
				form = self.booking_form()
				self.assertTrue(form.is_valid(), form.errors)
				Booking.objects.filter(pk=self.booking.pk).update(status=BookingStatus.PENDING)

	def test_rejects_unavailable_room_and_over_capacity(self):
		other_room = Room.objects.create(room_number='102', room_type=self.room_type)
		other_room.is_available = False
		other_room.save()

		unavailable_form = self.booking_form(room=other_room)
		self.assertFalse(unavailable_form.is_valid())
		self.assertIn('room', unavailable_form.errors)

		capacity_form = self.booking_form(guests=3)
		self.assertFalse(capacity_form.is_valid())
		self.assertIn('number_of_guests', capacity_form.errors)


class BookingServiceTests(BookingFixtureMixin, TestCase):
	def test_confirmation_requires_a_fully_paid_bill(self):
		bill = Bill.objects.create(booking=self.booking)
		Charge.objects.create(bill=bill, amount=Decimal('100.00'), description='Stay')

		with self.assertRaises(ValidationError):
			BookingService.confirm(self.booking.booking_id, user=self.user)

	def test_confirmation_succeeds_after_full_payment(self):
		bill = Bill.objects.create(booking_id=self.booking.booking_id)
		Charge.objects.create(bill=bill, amount=Decimal('100.00'), description='Stay')
		Payment.objects.create(
			bill=bill,
			amount=Decimal('100.00'),
			payment_method='cash',
		)

		confirmed = BookingService.confirm(
			self.booking.booking_id,
			user=self.user
		)

		self.assertEqual(confirmed.status, BookingStatus.CONFIRMED)

	def test_cancel_changes_pending_booking_to_canceled(self):
		canceled = BookingService.cancel(booking_id=self.booking.booking_id, user=self.user)

		self.assertEqual(canceled.status, BookingStatus.CANCELED)

	def test_check_in_rejects_before_arrival(self):
		self.booking.status = BookingStatus.CONFIRMED
		self.booking.save()
		before_arrival = datetime.combine(
			self.check_in - timedelta(days=1),
			time.min,
			tzinfo=datetime_timezone.utc,
		)

		with patch('bookings.services.timezone.now', return_value=before_arrival):
			with self.assertRaises(ValidationError):
				BookingService.check_in(self.booking.booking_id, self.user)

	def test_check_in_rejects_after_checkout(self):
		self.booking.status = BookingStatus.CONFIRMED
		self.booking.save()
		after_checkout = datetime.combine(
			self.check_out + timedelta(days=1),
			time.min,
			tzinfo=datetime_timezone.utc,
		)

		with patch('bookings.services.timezone.now', return_value=after_checkout):
			with self.assertRaises(ValidationError):
				BookingService.check_in(self.booking.booking_id, self.user)

	def test_status_change_requires_an_allowed_staff_role(self):
		user = User.objects.create_user(username='customer-account', password='password')

		with self.assertRaises(PermissionDenied):
			BookingService.cancel(self.booking.booking_id, user)
