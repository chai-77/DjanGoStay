from django.core.exceptions import ValidationError
from django.db import models


class Bill(models.Model):
    bill_id = models.AutoField(primary_key=True)
    booking = models.OneToOneField(
        'bookings.Booking',
        on_delete=models.PROTECT,
        related_name='bill',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['booking'], name='unique_bill_per_booking'),
        ]

    def __str__(self):
        return f'Bill #{self.bill_id}'


class Charge(models.Model):
    charge_id = models.AutoField(primary_key=True)
    bill = models.ForeignKey(Bill, on_delete=models.PROTECT, related_name='charges')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name='charge_amount_positive'),
        ]

    def clean(self):
        if self.amount <= 0:
            raise ValidationError({'amount': 'Charge amount must be greater than zero.'})

    def __str__(self):
        return f'Charge #{self.charge_id}'


class Discount(models.Model):
    discount_id = models.AutoField(primary_key=True)
    bill = models.ForeignKey(Bill, on_delete=models.PROTECT, related_name='discounts')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name='discount_amount_positive'),
        ]

    def clean(self):
        if self.amount <= 0:
            raise ValidationError({'amount': 'Discount amount must be greater than zero.'})

    def __str__(self):
        return f'Discount #{self.discount_id}'


class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True)
    bill = models.ForeignKey(Bill, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method_choices = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
    ]
    payment_method = models.CharField(max_length=20, choices=payment_method_choices)
    status = models.CharField(
        max_length=20,
        default='posted',
        choices=[('posted', 'Posted'), ('refunded', 'Refunded')],
    )
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name='payment_amount_positive'),
        ]

    def clean(self):
        if self.amount <= 0:
            raise ValidationError({'amount': 'Payment amount must be greater than zero.'})

    def __str__(self):
        return f'Payment #{self.payment_id}'