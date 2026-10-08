import re

from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields.ranges import RangeOperators
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Func, Q


def normalize_phone_number(value):
    if value is None:
        return ''
    digits = re.sub(r'\D+', '', str(value))
    if digits:
        return digits if digits.startswith('0') else digits
    return ''


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, unique=True)
    address = models.TextField()

    def clean(self):
        self.email = (self.email or '').strip().lower()
        self.phone_number = normalize_phone_number(self.phone_number)
        if not self.first_name.strip() or not self.last_name.strip():
            raise ValidationError('First and last name are required.')
        if not self.phone_number:
            raise ValidationError({'phone_number': 'Phone number is required.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class BookingStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    CONFIRMED = 'confirmed', 'Confirmed'
    CHECKED_IN = 'checked_in', 'Checked In'
    CHECKED_OUT = 'checked_out', 'Checked Out'
    CANCELED = 'canceled', 'Canceled'


class Booking(models.Model):
    booking_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='bookings')
    room = models.ForeignKey('rooms.Room', on_delete=models.PROTECT, related_name='bookings')
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    number_of_guests = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.PENDING)

    def clean(self):
        errors = {}

        if self.check_in_date and self.check_out_date and self.check_in_date >= self.check_out_date:
            errors['check_out_date'] = 'Check-out date must be after check-in date.'

        if self.number_of_guests is not None and self.number_of_guests < 1:
            errors['number_of_guests'] = 'Number of guests must be at least 1.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'Booking #{self.booking_id} - {self.customer.first_name} {self.customer.last_name}'

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(number_of_guests__gte=1),
                name='booking_guest_count_positive',
            ),
            models.CheckConstraint(
                condition=models.Q(check_in_date__lt=models.F('check_out_date')),
                name='booking_dates_valid',
            ),
            ExclusionConstraint(
                name='prevent_overlapping_bookings',
                expressions=[
                    ('room', RangeOperators.EQUAL),
                    (
                        Func(F('check_in_date'), F('check_out_date'), function='daterange'),
                        RangeOperators.OVERLAPS,
                    ),
                ],
                condition=~Q(status__in=[BookingStatus.CANCELED, BookingStatus.CHECKED_OUT]),
            ),
        ]
