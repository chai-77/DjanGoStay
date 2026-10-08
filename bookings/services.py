from datetime import date

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from billings.services import BillingService
from .models import Booking, BookingStatus


class BookingService:
    TRANSITIONS = {
        BookingStatus.PENDING: {BookingStatus.CONFIRMED, BookingStatus.CANCELED},
        BookingStatus.CONFIRMED: {BookingStatus.CHECKED_IN, BookingStatus.CANCELED},
        BookingStatus.CHECKED_IN: {BookingStatus.CHECKED_OUT},
        BookingStatus.CHECKED_OUT: set(),
        BookingStatus.CANCELED: set(),
    }

    @classmethod
    def _change_status(cls, booking, new_status):
        allowed = cls.TRANSITIONS.get(booking.status, set())
        if new_status not in allowed:
            raise ValidationError(f'Cannot change booking from "{booking.status}" to "{new_status}".')
        booking.status = new_status
        booking.save(update_fields=['status'])
        return booking

    @classmethod
    def _resolve_role(cls, user):
        if not getattr(user, 'is_authenticated', False):
            raise PermissionDenied('Authentication is required.')
        role = getattr(user, 'role', None)
        if role is None and hasattr(user, 'staff_profile'):
            role = user.staff_profile.role
        return role

    @classmethod
    def _require_role(cls, user, allowed_roles):
        role = cls._resolve_role(user)
        if role not in allowed_roles:
            raise PermissionDenied('You do not have permission for this operation.')

    @classmethod
    @transaction.atomic
    def confirm(cls, booking_id, user):
        cls._require_role(
            user,
            ['manager', 'receptionist']
        )

        booking = (
            Booking.objects
            .select_for_update()
            .get(booking_id=booking_id)
        )

        if booking.status != BookingStatus.PENDING:
            raise ValidationError(
                'Only pending bookings can be confirmed.'
            )

        bill = BillingService.get_bill_for_booking(booking)

        if bill is None:
            raise ValidationError(
                'This booking does not have a bill.'
            )

        if not BillingService.is_fully_paid(bill):
            totals = BillingService.get_totals(bill)
            raise ValidationError(
                f'Booking has an outstanding balance '
                f'of {totals["balance"]}.'
            )

        return cls._change_status(
            booking,
            BookingStatus.CONFIRMED
        )

    @classmethod
    @transaction.atomic
    def check_in(cls, booking_id, user):
        cls._require_role(user, ['manager', 'receptionist'])
        booking = Booking.objects.select_for_update().get(booking_id=booking_id)
        if booking.status != BookingStatus.CONFIRMED:
            raise ValidationError('Only confirmed bookings can be checked in.')
        today = timezone.now().date()
        if today < booking.check_in_date:
            raise ValidationError(
                'Cannot check in before the scheduled check-in date.'
        )
        if today > booking.check_out_date:
            raise ValidationError(
                'Cannot check in after the scheduled checkout date.'
            )
        return cls._change_status(booking, BookingStatus.CHECKED_IN)

    @classmethod
    @transaction.atomic
    def check_out(cls, booking_id, user):
        cls._require_role(user, ['manager', 'receptionist'])
        booking = Booking.objects.select_for_update().get(booking_id=booking_id)
        if booking.status != BookingStatus.CHECKED_IN:
            raise ValidationError('Only checked-in bookings can be checked out.')
        today = timezone.now().date()
        if today < booking.check_in_date or today > booking.check_out_date:
            raise ValidationError('Check-out must occur within the booking stay dates.')
        return cls._change_status(booking, BookingStatus.CHECKED_OUT)

    @classmethod
    @transaction.atomic
    def cancel(cls, booking_id, user):
        cls._require_role(user, ['manager', 'receptionist'])
        booking = Booking.objects.select_for_update().get(booking_id=booking_id)
        if booking.status not in {BookingStatus.PENDING, BookingStatus.CONFIRMED}:
            raise ValidationError('Only pending or confirmed bookings can be canceled.')
        return cls._change_status(booking, BookingStatus.CANCELED)
