# staff/admin.py
from django.contrib import admin
from .models import Staff

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('staff_id', 'first_name', 'last_name', 'role', 'phone_number', 'salary', 'date_of_joining')
    list_filter = ('role', 'date_of_joining')
    search_fields = ('first_name', 'last_name', 'phone_number', 'user__username')