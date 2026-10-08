# billing/admin.py
from django.contrib import admin
from .models import Bill, Charge, Discount, Payment

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('bill_id', 'booking', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('booking__booking_id', 'booking__customer__first_name', 'booking__customer__last_name')

@admin.register(Charge)
class ChargeAdmin(admin.ModelAdmin):
    list_display = ('charge_id', 'bill', 'amount', 'description', 'date')
    list_filter = ('date',)
    search_fields = ('description', 'bill__bill_id')

@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('discount_id', 'bill', 'amount', 'description', 'date')
    list_filter = ('date',)
    search_fields = ('description', 'bill__bill_id')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'bill', 'amount', 'payment_method', 'date')
    list_filter = ('payment_method', 'date')
    search_fields = ('bill__bill_id',)