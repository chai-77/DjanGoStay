from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse

from bookings.models import Booking, Customer
from rooms.models import Room, RoomType
from staff.models import Staff

from .forms import DiscountForm
from .models import Bill, Charge, Discount, Payment
from .services import BillingService, PaymentService


class BillingFixtureMixin:
	def setUp(self):
		today = date.today()
		self.manager_user = User.objects.create_user(
			username='manager',
			password='password',
		)
		Staff.objects.create(
			user=self.manager_user,
			first_name='Hotel',
			last_name='Manager',
			phone_number='5552000001',
			role='manager',
			salary=Decimal('50000.00'),
			date_of_joining=today,
		)
		self.finance_user = User.objects.create_user(
			username='finance',
			password='password',
		)
		Staff.objects.create(
			user=self.finance_user,
			first_name='Finance',
			last_name='Clerk',
			phone_number='5552000002',
			role='finance',
			salary=Decimal('35000.00'),
			date_of_joining=today,
		)
		self.customer = Customer.objects.create(
			first_name='Guest',
			last_name='One',
			email='billing.guest@example.com',
			phone_number='5552000003',
			address='Hotel address',
		)
		room_type = RoomType.objects.create(
			room_type_name='Billing Standard',
			room_price=Decimal('100.00'),
			room_capacity=2,
		)
		room = Room.objects.create(room_number='201', room_type=room_type)
		self.booking = Booking.objects.create(
			customer=self.customer,
			room=room,
			check_in_date=today + timedelta(days=1),
			check_out_date=today + timedelta(days=2),
			number_of_guests=1,
		)
		self.bill = Bill.objects.create(booking=self.booking)
		self.charge = Charge.objects.create(
			bill=self.bill,
			amount=Decimal('100.00'),
			description='Room charge',
		)


class BillingTotalsTests(BillingFixtureMixin, TestCase):
	def test_totals_include_only_posted_payments(self):
		Payment.objects.create(
			bill=self.bill,
			amount=Decimal('20.00'),
			payment_method='cash',
			status='posted',
		)
		Payment.objects.create(
			bill=self.bill,
			amount=Decimal('30.00'),
			payment_method='cash',
			status='refunded',
		)

		totals = BillingService.get_totals(self.bill)

		self.assertEqual(totals['payments'], Decimal('20.00'))
		self.assertEqual(totals['balance'], Decimal('80.00'))

	def test_discount_form_rejects_total_discounts_above_charges(self):
		form = DiscountForm(data={
			'bill': self.bill.pk,
			'amount': '100.01',
			'description': 'Over-limit discount',
		})

		self.assertFalse(form.is_valid())
		self.assertIn('__all__', form.errors)

	def test_discount_update_validates_replacement_amount_not_addition(self):
		discount = Discount.objects.create(
			bill=self.bill,
			amount=Decimal('80.00'),
			description='Original discount',
		)
		form = DiscountForm(
			instance=discount,
			data={
				'bill': self.bill.pk,
				'amount': '30.00',
				'description': 'Reduced discount',
			},
		)

		self.assertTrue(form.is_valid(), form.errors)


class PaymentServiceTests(BillingFixtureMixin, TestCase):
	def test_payment_service_creates_a_payment_within_balance(self):
		payment = PaymentService.create_payment(
			bill_id=self.bill.bill_id,
			amount=Decimal('40.00'),
			payment_method='cash',
			user=self.finance_user,
		)

		self.assertEqual(payment.status, 'posted')
		self.assertEqual(BillingService.get_totals(self.bill)['balance'], Decimal('60.00'))

	def test_payment_service_rejects_overpayment(self):
		with self.assertRaises(ValidationError):
			PaymentService.create_payment(
				bill_id=self.bill.bill_id,
				amount=Decimal('100.01'),
				payment_method='cash',
				user=self.finance_user,
			)

		self.assertEqual(Payment.objects.count(), 0)

	def test_payment_service_rejects_users_without_finance_role(self):
		receptionist = User.objects.create_user(
			username='receptionist',
			password='password',
		)
		Staff.objects.create(
			user=receptionist,
			first_name='Front',
			last_name='Desk',
			phone_number='5552000004',
			role='receptionist',
			salary=Decimal('30000.00'),
			date_of_joining=date.today(),
		)

		with self.assertRaises(PermissionDenied):
			PaymentService.create_payment(
				bill_id=self.bill.bill_id,
				amount=Decimal('10.00'),
				payment_method='cash',
				user=receptionist,
			)


class PaymentViewTests(BillingFixtureMixin, TestCase):
	def test_finance_user_can_create_payment(self):
		self.client.force_login(self.finance_user)

		response = self.client.post(
			reverse('payment_create'),
			{
				'bill': self.bill.pk,
				'amount': '25.00',
				'payment_method': 'cash',
			},
		)

		self.assertRedirects(response, reverse('payment_list'))
		self.assertEqual(Payment.objects.filter(bill=self.bill).count(), 1)

	def test_posted_payment_cannot_be_edited_or_deleted(self):
		payment = Payment.objects.create(
			bill=self.bill,
			amount=Decimal('25.00'),
			payment_method='cash',
		)
		self.client.force_login(self.manager_user)

		update_response = self.client.get(
			reverse('payment_update', kwargs={'payment_id': payment.payment_id})
		)
		delete_response = self.client.post(
			reverse('payment_delete', kwargs={'payment_id': payment.payment_id})
		)

		self.assertEqual(update_response.status_code, 403)
		self.assertEqual(delete_response.status_code, 302)
		self.assertTrue(Payment.objects.filter(pk=payment.pk).exists())

	def test_refunded_payment_cannot_be_edited_or_deleted(self):
		payment = Payment.objects.create(
			bill=self.bill,
			amount=Decimal('25.00'),
			payment_method='cash',
			status='refunded',
		)
		self.client.force_login(self.manager_user)

		update_response = self.client.get(
			reverse('payment_update', kwargs={'payment_id': payment.payment_id})
		)
		delete_response = self.client.post(
			reverse('payment_delete', kwargs={'payment_id': payment.payment_id})
		)

		self.assertEqual(update_response.status_code, 403)
		self.assertEqual(delete_response.status_code, 302)
		self.assertTrue(Payment.objects.filter(pk=payment.pk).exists())
