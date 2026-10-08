# billing/forms.py
from django import forms

from .models import Bill, Charge, Discount, Payment


class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['booking']


class ChargeForm(forms.ModelForm):
    class Meta:
        model = Charge
        fields = ['bill', 'amount', 'description']


class DiscountForm(forms.ModelForm):
    class Meta:
        model = Discount
        fields = ['bill', 'amount', 'description']

    def clean(self):
        cleaned_data = super().clean()

        bill = cleaned_data.get('bill')
        amount = cleaned_data.get('amount')

        if bill and amount is not None:
            from .services import BillingService

            BillingService.can_add_discount(
                bill,
                amount,
                discount=(
                    self.instance
                    if self.instance.pk
                    else None
                ),
            )
        return cleaned_data


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['bill', 'amount', 'payment_method']

    def clean(self):
        cleaned_data = super().clean()

        bill = cleaned_data.get('bill')
        amount = cleaned_data.get('amount')

        if bill and amount is not None:
            from .services import BillingService

            BillingService.can_accept_payment(
                bill,
                amount,
            )

        return cleaned_data

