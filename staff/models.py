import re

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


class Staff(models.Model):
    staff_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.PROTECT, related_name='staff_profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, unique=True)

    role_choices = [
        ('manager', 'Manager'),
        ('receptionist', 'Receptionist'),
        ('housekeeping', 'Housekeeping'),
        ('finance', 'Finance'),
        ('cook', 'Cook'),
        ('server', 'Server'),
        ('maintenance', 'Maintenance'),
    ]

    role = models.CharField(max_length=20, choices=role_choices)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    date_of_joining = models.DateField()

    def clean(self):
        if not self.first_name.strip() or not self.last_name.strip():
            raise ValidationError('First and last name are required.')
        digits = re.sub(r'\D+', '', str(self.phone_number or ''))
        self.phone_number = digits
        if not self.phone_number:
            raise ValidationError({'phone_number': 'Phone number is required.'})
        if self.salary < 0:
            raise ValidationError({'salary': 'Salary cannot be negative.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.role})'