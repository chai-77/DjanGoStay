# rooms/admin.py
from django.contrib import admin
from .models import Room, RoomType, HousekeepingAssignment

@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ('room_type_id', 'room_type_name', 'room_price', 'room_capacity')
    search_fields = ('room_type_name',)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_id', 'room_number', 'room_type', 'is_available')
    list_filter = ('is_available', 'room_type')
    search_fields = ('room_number',)

@admin.register(HousekeepingAssignment)
class HousekeepingAssignmentAdmin(admin.ModelAdmin):
    list_display = ('assignment_id', 'room', 'assigned_to', 'assignment_date', 'is_completed')
    list_filter = ('is_completed', 'assignment_date')
    search_fields = ('room__room_number', 'assigned_to__first_name', 'assigned_to__last_name')