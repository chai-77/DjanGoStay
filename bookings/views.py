from django.db import IntegrityError
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)

from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.views import View

from .services import BookingService
from .models import Customer, Booking
from .forms import CustomerForm, BookingForm
from django.core.exceptions import ValidationError, PermissionDenied
from staff.mixins import HotelRoleRequiredMixin


# CUSTOMER VIEWS

class CustomerListView(
    HotelRoleRequiredMixin,
    ListView
):
    model = Customer
    template_name = 'bookings/customer_list.html'
    context_object_name = 'customers'

    # Manager + Receptionist
    allowed_roles = [
        'manager',
        'receptionist',
    ]


class CustomerDetailView(
    HotelRoleRequiredMixin,
    DetailView
):
    model = Customer
    template_name = 'bookings/customer_detail.html'
    context_object_name = 'customer'
    pk_url_kwarg = 'customer_id'

    # Manager + Receptionist
    allowed_roles = [
        'manager',
        'receptionist',
    ]


class CustomerCreateView(
    HotelRoleRequiredMixin,
    CreateView
):
    model = Customer
    form_class = CustomerForm
    template_name = 'bookings/customer_form.html'
    success_url = reverse_lazy('customer_list')

    # Manager + Receptionist
    allowed_roles = [
        'manager',
        'receptionist',
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Create'

        return context


class CustomerUpdateView(
    HotelRoleRequiredMixin,
    UpdateView
):
    model = Customer
    form_class = CustomerForm
    template_name = 'bookings/customer_form.html'
    pk_url_kwarg = 'customer_id'

    # Manager + Receptionist
    allowed_roles = [
        'manager',
        'receptionist',
    ]

    def get_success_url(self):
        return reverse_lazy(
            'customer_detail',
            kwargs={
                'customer_id': self.object.customer_id
            }
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Update'

        return context


class CustomerDeleteView(
    HotelRoleRequiredMixin,
    DeleteView
):
    model = Customer
    template_name = 'bookings/customer_delete.html'
    context_object_name = 'customer'
    pk_url_kwarg = 'customer_id'
    success_url = reverse_lazy('customer_list')

    # DELETE = Manager only
    allowed_roles = [
        'manager',
    ]


# BOOKING VIEWS

class BookingListView(
    HotelRoleRequiredMixin,
    ListView
):
    model = Booking
    template_name = 'bookings/booking_list.html'
    context_object_name = 'bookings'

    # Manager + Receptionist
    allowed_roles = [
        'manager',
        'receptionist',
    ]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related('customer', 'room')
        )


class BookingDetailView(
    HotelRoleRequiredMixin,
    DetailView
):
    model = Booking
    template_name = 'bookings/booking_detail.html'
    context_object_name = 'booking'
    pk_url_kwarg = 'booking_id'

    # Manager + Receptionist
    allowed_roles = [
        'manager',
        'receptionist',
    ]


class BookingCreateView(
    HotelRoleRequiredMixin,
    CreateView
):
    model = Booking
    form_class = BookingForm
    template_name = 'bookings/booking_form.html'
    success_url = reverse_lazy('booking_list')

    allowed_roles = [
        'manager',
        'receptionist',
    ]

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except IntegrityError:
            form.add_error(None, 'This room is already booked for the selected dates.')
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Create'

        return context


class BookingUpdateView(
    HotelRoleRequiredMixin,
    UpdateView
):
    model = Booking
    form_class = BookingForm
    template_name = 'bookings/booking_form.html'
    pk_url_kwarg = 'booking_id'

    allowed_roles = [
        'manager',
        'receptionist',
    ]

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.status != 'pending':
            messages.error(
                request,
                'Only pending bookings can be edited.'
            )
            return redirect(
                'booking_detail',
                booking_id=self.object.booking_id,
            )

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except IntegrityError:
            form.add_error(None, 'This room is already booked for the selected dates.')
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy(
            'booking_detail',
            kwargs={
                'booking_id': self.object.booking_id
            }
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Update'

        return context


class BookingCancelView(
    HotelRoleRequiredMixin,
    View
):
    allowed_roles = [
        'manager',
        'receptionist',
    ]

    def post(self, request, booking_id):
        try:
            BookingService.cancel(
                booking_id=booking_id,
                user=request.user,
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
        else:
            messages.success(
                request,
                'Booking canceled successfully.'
            )

        return redirect(
            'booking_detail',
            booking_id=booking_id
        )


class BookingConfirmView(
    HotelRoleRequiredMixin,
    View
):
    allowed_roles = [
        'manager',
        'receptionist',
    ]

    def post(self, request, booking_id):
        # booking = get_object_or_404(
        #     Booking,
        #     booking_id=booking_id
        # )

        try:
            BookingService.confirm(
                booking_id=booking_id,
                user=request.user,
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
        else:
            messages.success(
                request,
                'Booking confirmed.'
            )

        return redirect(
            'booking_detail',
            booking_id=booking_id
        )


class BookingCheckInView(
    HotelRoleRequiredMixin,
    View
):
    allowed_roles = [
        'manager',
        'receptionist',
    ]

    def post(self, request, booking_id):
        try:
            BookingService.check_in(
                booking_id=booking_id,
                user=request.user,
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
        else:
            messages.success(
                request,
                'Guest checked in.'
            )

        return redirect(
            'booking_detail',
            booking_id=booking_id
        )


class BookingCheckOutView(
    HotelRoleRequiredMixin,
    View
):
    allowed_roles = [
        'manager',
        'receptionist',
    ]

    def post(self, request, booking_id):
        try:
            BookingService.check_out(
                booking_id=booking_id,
                user=request.user,
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))
        else:
            messages.success(
                request,
                'Guest checked out.'
            )

        return redirect(
            'booking_detail',
            booking_id=booking_id
        )
