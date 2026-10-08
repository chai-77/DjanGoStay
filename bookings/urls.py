# bookings/urls.py
from django.urls import path
from .views import (
    CustomerListView, CustomerDetailView, CustomerCreateView, CustomerUpdateView, CustomerDeleteView,
    BookingListView, BookingDetailView, BookingCreateView, BookingUpdateView, BookingConfirmView, BookingCheckInView, BookingCheckOutView, BookingCancelView
)

urlpatterns = [
    # Customer URLs
    path('customers/', CustomerListView.as_view(), name='customer_list'),
    path('customers/<int:customer_id>/', CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/create/', CustomerCreateView.as_view(), name='customer_create'),
    path('customers/<int:customer_id>/update/', CustomerUpdateView.as_view(), name='customer_update'),
    path('customers/<int:customer_id>/delete/', CustomerDeleteView.as_view(), name='customer_delete'),

    # Booking URLs
    path('', BookingListView.as_view(), name='booking_list'),
    path('<int:booking_id>/', BookingDetailView.as_view(), name='booking_detail'),
    path('create/', BookingCreateView.as_view(), name='booking_create'),
    path('<int:booking_id>/update/', BookingUpdateView.as_view(), name='booking_update'),
    # path('<int:booking_id>/delete/', BookingDeleteView.as_view(), name='booking_delete'),

    path(
        '<int:booking_id>/confirm/',
        BookingConfirmView.as_view(),
        name='booking_confirm',
    ),

    path(
        '<int:booking_id>/check-in/',
        BookingCheckInView.as_view(),
        name='booking_check_in',
    ),

    path(
        '<int:booking_id>/check-out/',
        BookingCheckOutView.as_view(),
        name='booking_check_out',
    ),

    path(
        '<int:booking_id>/cancel/',
        BookingCancelView.as_view(),
        name='booking_cancel',
    ),
]