from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Sum

from .models import Bill, Charge, Discount, Payment


class BillingService:

    @staticmethod
    def get_bill_for_booking(booking):
        return (
            Bill.objects
            .filter(booking=booking)
            .prefetch_related('charges', 'discounts', 'payments')
            .first()
        )

    @staticmethod
    def get_totals(bill):
        if bill is None:
            return {
                'charges': Decimal('0.00'),
                'discounts': Decimal('0.00'),
                'amount_due': Decimal('0.00'),
                'payments': Decimal('0.00'),
                'balance': Decimal('0.00'),
            }

        charges = bill.charges.aggregate(
            total=Sum('amount', default=Decimal('0.00'))
        )['total']

        discounts = bill.discounts.aggregate(
            total=Sum('amount', default=Decimal('0.00'))
        )['total']

        posted_payments = bill.payments.filter(
            status='posted'
        ).aggregate(
            total=Sum('amount', default=Decimal('0.00'))
        )['total']

        amount_due = max(
            charges - discounts,
            Decimal('0.00')
        )

        balance = max(
            amount_due - posted_payments,
            Decimal('0.00')
        )

        return {
            'charges': charges,
            'discounts': discounts,
            'amount_due': amount_due,
            'payments': posted_payments,
            'balance': balance,
        }

    @classmethod
    def is_fully_paid(cls, bill):
        totals = cls.get_totals(bill)
        return totals['balance'] <= Decimal('0.00')

    @classmethod
    def can_accept_payment(cls, bill, amount):
        totals = cls.get_totals(bill)

        if amount <= 0:
            raise ValidationError(
                'Payment amount must be greater than zero.'
            )

        if amount > totals['balance']:
            raise ValidationError(
                'Payment cannot exceed the outstanding balance.'
            )

        return True

    @classmethod
    def can_add_discount(cls, bill, amount, discount=None):
        if amount <= 0:
            raise ValidationError(
                'Discount amount must be greater than zero.'
            )

        discounts = bill.discounts.all()

        if discount is not None:
            discounts = discounts.exclude(
                discount_id=discount.discount_id
            )

        existing = discounts.aggregate(
            total=Sum('amount', default=Decimal('0.00'))
        )['total']

        charges = bill.charges.aggregate(
            total=Sum('amount', default=Decimal('0.00'))
        )['total']

        if existing + amount > charges:
            raise ValidationError(
                'Discount cannot exceed the bill charges.'
            )

        return True


class PaymentService:
    @classmethod
    @transaction.atomic
    def create_payment(cls, *, bill_id, amount, payment_method, user):
        cls._require_role(user, ['manager', 'finance'])
        bill = Bill.objects.select_for_update().get(bill_id=bill_id)
        totals = BillingService.get_totals(bill)
        if amount <= Decimal('0.00'):
            raise ValidationError('Payment amount must be greater than zero.')
        if amount > totals['balance']:
            raise ValidationError(f'Payment cannot exceed the outstanding balance of {totals["balance"]}.')
        return Payment.objects.create(
            bill=bill,
            amount=amount,
            payment_method=payment_method,
            status='posted',
        )

    @staticmethod
    def _require_role(user, allowed_roles):
        if not getattr(user, 'is_authenticated', False):
            raise PermissionDenied('Authentication is required.')
        role = getattr(user, 'role', None)
        if role is None and hasattr(user, 'staff_profile'):
            role = user.staff_profile.role
        if role not in allowed_roles:
            raise PermissionDenied('You do not have permission to record payments.')

class DiscountService:

    @classmethod
    @transaction.atomic
    def create_discount(cls, *, bill_id, amount, description, user):
        cls._require_role(user, ['manager', 'finance'])

        bill = (
            Bill.objects
            .select_for_update()
            .get(bill_id=bill_id)
        )

        BillingService.can_add_discount(
            bill,
            amount,
        )

        return Discount.objects.create(
            bill=bill,
            amount=amount,
            description=description,
        )

    @classmethod
    @transaction.atomic
    def update_discount(
        cls,
        *,
        discount_id,
        amount,
        description,
        user,
    ):
        cls._require_role(user, ['manager', 'finance'])

        discount = (
            Discount.objects
            .select_related('bill')
            .get(discount_id=discount_id)
        )

        # Lock the parent bill.
        bill = (
            Bill.objects
            .select_for_update()
            .get(bill_id=discount.bill_id)
        )

        BillingService.can_add_discount(
            bill,
            amount,
            discount=discount,
        )

        discount.amount = amount
        discount.description = description
        discount.save(
            update_fields=[
                'amount',
                'description',
            ]
        )

        return discount

    @staticmethod
    def _require_role(user, allowed_roles):
        if not getattr(user, 'is_authenticated', False):
            raise PermissionDenied(
                'Authentication is required.'
            )

        role = getattr(user, 'role', None)

        if role is None and hasattr(user, 'staff_profile'):
            role = user.staff_profile.role

        if role not in allowed_roles:
            raise PermissionDenied(
                'You do not have permission to manage discounts.'
            )



class ChargeService:

    @classmethod
    @transaction.atomic
    def create_charge(
        cls,
        *,
        bill_id,
        amount,
        description,
        user,
    ):
        cls._require_role(user, ['manager', 'finance'])

        if amount <= Decimal('0.00'):
            raise ValidationError(
                'Charge amount must be greater than zero.'
            )

        bill = (
            Bill.objects
            .select_for_update()
            .get(bill_id=bill_id)
        )

        return Charge.objects.create(
            bill=bill,
            amount=amount,
            description=description,
        )

    @classmethod
    @transaction.atomic
    def update_charge(
        cls,
        *,
        charge_id,
        amount,
        description,
        user,
    ):
        cls._require_role(user, ['manager', 'finance'])

        if amount <= Decimal('0.00'):
            raise ValidationError(
                'Charge amount must be greater than zero.'
            )

        charge = (
            Charge.objects
            .select_related('bill')
            .get(charge_id=charge_id)
        )

        bill = (
            Bill.objects
            .select_for_update()
            .get(bill_id=charge.bill_id)
        )

        discounts = bill.discounts.aggregate(
            total=Sum(
                'amount',
                default=Decimal('0.00')
            )
        )['total']

        other_charges = (
            bill.charges
            .exclude(charge_id=charge.charge_id)
            .aggregate(
                total=Sum(
                    'amount',
                    default=Decimal('0.00')
                )
            )['total']
        )

        if other_charges + amount < discounts:
            raise ValidationError(
                'Charge cannot be reduced because '
                'the total charges would be less '
                'than the total discounts.'
            )

        charge.amount = amount
        charge.description = description
        charge.save(
            update_fields=[
                'amount',
                'description',
            ]
        )

        return charge

    @classmethod
    @transaction.atomic
    def delete_charge(
        cls,
        *,
        charge_id,
        user,
    ):
        cls._require_role(user, ['manager'])

        charge = (
            Charge.objects
            .select_related('bill')
            .get(charge_id=charge_id)
        )

        bill = (
            Bill.objects
            .select_for_update()
            .get(bill_id=charge.bill_id)
        )

        discounts = bill.discounts.aggregate(
            total=Sum(
                'amount',
                default=Decimal('0.00')
            )
        )['total']

        remaining_charges = (
            bill.charges
            .exclude(charge_id=charge.charge_id)
            .aggregate(
                total=Sum(
                    'amount',
                    default=Decimal('0.00')
                )
            )['total']
        )
        if remaining_charges < discounts:
            raise ValidationError(
                'Charge cannot be deleted because '
                'the remaining charges are less '
                'than the total discounts.'
            )

        charge.delete()

    @staticmethod
    def _require_role(user, allowed_roles):
        if not getattr(user, 'is_authenticated', False):
            raise PermissionDenied(
                'Authentication is required.'
            )

        role = getattr(user, 'role', None)

        if role is None and hasattr(user, 'staff_profile'):
            role = user.staff_profile.role

        if role not in allowed_roles:
            raise PermissionDenied(
                'You do not have permission to manage charges.'
            )
