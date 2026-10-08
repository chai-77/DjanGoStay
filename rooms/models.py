import re

from django.core.exceptions import ValidationError
from django.db import models


class Room(models.Model):
    room_id = models.AutoField(primary_key=True)
    room_number = models.CharField(max_length=20, unique=True)
    is_available = models.BooleanField(default=True)
    room_type = models.ForeignKey(
        'RoomType',
        on_delete=models.PROTECT,
        related_name='rooms'
    )
    # permissions and constraints
    class Meta:
        permissions = [
            ('manage_room', 'Can manage rooms'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(room_number__regex=r'^[A-Z0-9][A-Z0-9 -]*$'),
                name='room_number_format_valid',
            )
        ]
    # validation rules
    def clean(self):
        value = (self.room_number or '').strip()
        value = re.sub(r'\s+', ' ', value).upper()
        self.room_number = value
        if not value:
            raise ValidationError({'room_number': 'Room number is required.'})
        if len(value) > 20:
            raise ValidationError({'room_number': 'Room number must be 20 characters or fewer.'})

    def save(self, *args, **kwargs):
        self.full_clean()  # Django checks the field rules (max_length, required fields, types, etc.) and then calls clean
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.room_number


class RoomType(models.Model):
    room_type_id = models.AutoField(primary_key=True)
    room_type_name = models.CharField(max_length=100)
    room_price = models.DecimalField(max_digits=10, decimal_places=2)
    room_capacity = models.IntegerField()

    class Meta:
        permissions = [
            ('manage_room_type', 'Can manage room types'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(room_capacity__gte=1),
                name='room_capacity_positive',
            ),
            models.CheckConstraint(
                condition=models.Q(room_price__gt=0),
                name='room_price_positive',
            ),
        ]

    def clean(self):
        if self.room_capacity < 1:
            raise ValidationError({'room_capacity': 'Room capacity must be at least 1.'})
        if self.room_price <= 0:
            raise ValidationError({'room_price': 'Room price must be greater than zero.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.room_type_name


class HousekeepingAssignment(models.Model):
    assignment_id = models.AutoField(primary_key=True)
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name='housekeeping_assignments')
    assigned_to = models.ForeignKey(
        'staff.Staff',
        on_delete=models.PROTECT,
        related_name='housekeeping_assignments'
    )
    assignment_date = models.DateField()
    is_completed = models.BooleanField(default=False)

    class Meta:
        permissions = [
            ('manage_housekeeping', 'Can manage housekeeping assignments'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['room', 'assigned_to', 'assignment_date'],
                name='unique_housekeeping_room_staff_date',
            ),
        ]
