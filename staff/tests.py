from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from bookings.forms import BookingForm
from bookings.models import Customer
from rooms.forms import RoomForm
from rooms.models import Room, RoomType

from .forms import StaffCreateForm, StaffForm
from .models import Staff


class AuthenticationFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='manager',
            password='correct-password',
        )
        self.staff = Staff.objects.create(
            user=self.user,
            first_name='Hotel',
            last_name='Manager',
            phone_number='5550000001',
            role='manager',
            salary='50000.00',
            date_of_joining=date(2026, 1, 1),
        )

    def test_anonymous_crud_request_redirects_to_login(self):
        response = self.client.get(reverse('room_list'))

        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("room_list")}',
        )

    def test_login_renders_csrf_protected_form_and_redirects(self):
        response = self.client.get(reverse('login'))

        self.assertContains(response, 'csrfmiddlewaretoken')
        self.assertContains(response, 'Log in')

        response = self.client.post(
            reverse('login'),
            {'username': 'manager', 'password': 'correct-password'},
        )
        self.assertRedirects(response, reverse('room_type_list'))

    def test_logout_requires_post_and_redirects_to_login(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('logout'))

        self.assertRedirects(response, reverse('login'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_non_manager_cannot_open_manager_only_endpoint(self):
        receptionist = User.objects.create_user(
            username='receptionist',
            password='password',
        )
        Staff.objects.create(
            user=receptionist,
            first_name='Front',
            last_name='Desk',
            phone_number='5550000002',
            role='receptionist',
            salary='30000.00',
            date_of_joining=date(2026, 1, 1),
        )
        self.client.force_login(receptionist)

        response = self.client.get(reverse('staff_list'))

        self.assertEqual(response.status_code, 403)

    def test_base_template_has_post_logout_and_no_public_crud_links(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('room_list'))

        self.assertContains(response, 'action="/logout/"')

    def test_housekeeping_login_lands_on_assignments_and_sees_only_its_navigation(self):
        user = User.objects.create_user(
            username='housekeeping',
            password='password',
        )
        Staff.objects.create(
            user=user,
            first_name='Asha',
            last_name='Patel',
            phone_number='5550000005',
            role='housekeeping',
            salary='28000.00',
            date_of_joining=date(2026, 1, 1),
        )

        response = self.client.post(
            reverse('login'),
            {'username': 'housekeeping', 'password': 'password'},
        )

        self.assertRedirects(response, reverse('housekeeping_list'))
        page = self.client.get(reverse('housekeeping_list'))
        self.assertContains(page, 'Housekeeping Assignments')
        self.assertContains(page, 'Housekeeping')
        self.assertNotContains(page, 'Bookings')
        self.assertNotContains(page, 'Billing')
        self.assertNotContains(page, 'Room Types')

    def test_receptionist_login_lands_on_bookings(self):
        user = User.objects.create_user(
            username='receptionist_two',
            password='password',
        )
        Staff.objects.create(
            user=user,
            first_name='Ravi',
            last_name='Sharma',
            phone_number='5550000006',
            role='receptionist',
            salary='30000.00',
            date_of_joining=date(2026, 1, 1),
        )

        response = self.client.post(
            reverse('login'),
            {'username': 'receptionist_two', 'password': 'password'},
        )

        self.assertRedirects(response, reverse('booking_list'))

    def test_manager_can_create_staff_with_new_account(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('staff_create'),
            {
                'first_name': 'New',
                'last_name': 'Housekeeper',
                'phone_number': '5550000011',
                'role': 'housekeeping',
                'salary': '28000.00',
                'date_of_joining': '2026-01-01',
                'username': 'new_housekeeper',
                'password1': 'StrongUniquePassword!827',
                'password2': 'StrongUniquePassword!827',
            },
        )

        self.assertRedirects(response, reverse('staff_list'))
        new_staff = Staff.objects.get(user__username='new_housekeeper')
        self.assertTrue(new_staff.user.check_password('StrongUniquePassword!827'))

        self.client.logout()
        login_response = self.client.post(
            reverse('login'),
            {
                'username': 'new_housekeeper',
                'password': 'StrongUniquePassword!827',
            },
        )
        self.assertRedirects(login_response, reverse('housekeeping_list'))


class ProtectedFormTests(TestCase):
    def test_booking_form_does_not_allow_status_changes(self):
        self.assertNotIn('status', BookingForm().fields)

    def test_room_form_does_not_allow_availability_changes(self):
        self.assertNotIn('is_available', RoomForm().fields)

    def test_staff_forms_do_not_expose_the_user_relation(self):
        assigned = User.objects.create_user(username='assigned')
        Staff.objects.create(
            user=assigned,
            first_name='Assigned',
            last_name='Staff',
            phone_number='5550000003',
            role='housekeeping',
            salary='25000.00',
            date_of_joining=date(2026, 1, 1),
        )

        self.assertNotIn('user', StaffForm().fields)
        self.assertNotIn('user', StaffCreateForm().fields)
        self.assertIn('username', StaffCreateForm().fields)
        self.assertIn('password1', StaffCreateForm().fields)

    def test_staff_create_form_requires_matching_passwords(self):
        form = StaffCreateForm(data={
            'first_name': 'New',
            'last_name': 'Staff',
            'phone_number': '5550000010',
            'role': 'housekeeping',
            'salary': '28000.00',
            'date_of_joining': '2026-01-01',
            'username': 'new_staff',
            'password1': 'GoodPassword123!',
            'password2': 'DifferentPassword123!',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)


class StaffModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='staff-member')

    def test_save_normalizes_phone_number(self):
        staff = Staff.objects.create(
            user=self.user,
            first_name='House',
            last_name='Keeper',
            phone_number='+1 (555) 400-0001',
            role='housekeeping',
            salary=Decimal('28000.00'),
            date_of_joining=date(2026, 1, 1),
        )

        self.assertEqual(staff.phone_number, '15554000001')

    def test_save_rejects_negative_salary(self):
        staff = Staff(
            user=self.user,
            first_name='House',
            last_name='Keeper',
            phone_number='5554000002',
            role='housekeeping',
            salary=Decimal('-1.00'),
            date_of_joining=date(2026, 1, 1),
        )

        with self.assertRaises(ValidationError):
            staff.save()


class StaffLoginEdgeCaseTests(TestCase):
    def test_account_without_staff_profile_cannot_complete_login(self):
        User.objects.create_user(username='unassigned', password='password')

        response = self.client.post(
            reverse('login'),
            {'username': 'unassigned', 'password': 'password'},
        )

        self.assertEqual(response.status_code, 403)

    def test_booking_form_rejects_invalid_dates_and_room_capacity(self):
        customer = Customer.objects.create(
            first_name='Guest',
            last_name='One',
            email='guest@example.com',
            phone_number='5550000004',
            address='Hotel address',
        )
        room_type = RoomType.objects.create(
            room_type_name='Single',
            room_price='100.00',
            room_capacity=1,
        )
        room = Room.objects.create(room_number='101', room_type=room_type)

        form = BookingForm(data={
            'customer': customer.pk,
            'room': room.pk,
            'check_in_date': '2026-09-20',
            'check_out_date': '2026-09-21',
            'number_of_guests': 2,
        })

        self.assertFalse(form.is_valid())
        self.assertIn('number_of_guests', form.errors)

        invalid_dates_form = BookingForm(data={
            'customer': customer.pk,
            'room': room.pk,
            'check_in_date': '2026-09-20',
            'check_out_date': '2026-09-20',
            'number_of_guests': 1,
        })
        self.assertFalse(invalid_dates_form.is_valid())
        self.assertIn('check_out_date', invalid_dates_form.errors)
