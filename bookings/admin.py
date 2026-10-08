# bookings/admin.py
from django.contrib import admin
from .models import Customer, Booking

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'first_name', 'last_name', 'email', 'phone_number')
    search_fields = ('first_name', 'last_name', 'email', 'phone_number')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'customer', 'room', 'check_in_date', 'check_out_date', 'number_of_guests', 'status')
    list_filter = ('status', 'check_in_date', 'check_out_date')
    search_fields = ('customer__first_name', 'customer__last_name', 'room__room_number')