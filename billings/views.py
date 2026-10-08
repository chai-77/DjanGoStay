from django.contrib import messages
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse_lazy

from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)

from .models import (
    Bill,
    Charge,
    Discount,
    Payment,
)

from .forms import (
    BillForm,
    ChargeForm,
    DiscountForm,
    PaymentForm,
)

from staff.mixins import HotelRoleRequiredMixin


# BILL VIEWS


class BillListView(
    HotelRoleRequiredMixin,
    ListView
):
    model = Bill
    template_name = 'billings/bill_list.html'
    context_object_name = 'bills'

    allowed_roles = [
        'manager',
        'finance',
    ]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related('booking')
        )


class BillDetailView(
    HotelRoleRequiredMixin,
    DetailView
):
    model = Bill
    template_name = 'billings/bill_detail.html'
    context_object_name = 'bill'
    pk_url_kwarg = 'bill_id'

    allowed_roles = [
        'manager',
        'finance',
    ]


class BillCreateView(
    HotelRoleRequiredMixin,
    CreateView
):
    model = Bill
    form_class = BillForm
    template_name = 'billings/bill_form.html'
    success_url = reverse_lazy('bill_list')

    allowed_roles = [
        'manager',
        'finance',
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Create'
        return context


class BillUpdateView(
    HotelRoleRequiredMixin,
    UpdateView
):
    model = Bill
    form_class = BillForm
    template_name = 'billings/bill_form.html'
    pk_url_kwarg = 'bill_id'

    allowed_roles = [
        'manager',
        'finance',
    ]

    def get_success_url(self):
        return reverse_lazy(
            'bill_detail',
            kwargs={
                'bill_id': self.object.bill_id
            }
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Update'
        return context


class BillDeleteView(
    HotelRoleRequiredMixin,
    DeleteView
):
    model = Bill
    template_name = 'billings/bill_delete.html'
    context_object_name = 'bill'
    pk_url_kwarg = 'bill_id'
    success_url = reverse_lazy('bill_list')

    # Delete = manager only
    allowed_roles = [
        'manager',
    ]


# ============================================================
# CHARGE VIEWS
# ============================================================

class ChargeListView(
    HotelRoleRequiredMixin,
    ListView
):
    model = Charge
    template_name = 'billings/charge_list.html'
    context_object_name = 'charges'

    allowed_roles = [
        'manager',
        'finance',
    ]


class ChargeDetailView(
    HotelRoleRequiredMixin,
    DetailView
):
    model = Charge
    template_name = 'billings/charge_detail.html'
    context_object_name = 'charge'
    pk_url_kwarg = 'charge_id'

    allowed_roles = [
        'manager',
        'finance',
    ]


class ChargeCreateView(
    HotelRoleRequiredMixin,
    CreateView
):
    model = Charge
    form_class = ChargeForm
    template_name = 'billings/charge_form.html'
    success_url = reverse_lazy('charge_list')

    allowed_roles = [
        'manager',
        'finance',
    ]

    def form_valid(self, form):
        from .services import ChargeService

        bill = form.cleaned_data['bill']
        amount = form.cleaned_data['amount']
        description = form.cleaned_data['description']

        try:
            self.object = ChargeService.create_charge(
                bill_id=bill.bill_id,
                amount=amount,
                description=description,
                user=self.request.user,
            )
        except (ValidationError, PermissionDenied) as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Create'
        return context


class ChargeUpdateView(
    HotelRoleRequiredMixin,
    UpdateView
):
    model = Charge
    form_class = ChargeForm
    template_name = 'billings/charge_form.html'
    pk_url_kwarg = 'charge_id'

    allowed_roles = [
        'manager',
        'finance',
    ]

    def form_valid(self, form):
        from .services import ChargeService

        try:
            self.object = ChargeService.update_charge(
                charge_id=self.object.charge_id,
                amount=form.cleaned_data['amount'],
                description=form.cleaned_data['description'],
                user=self.request.user,
            )
        except (ValidationError, PermissionDenied) as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy(
            'charge_detail',
            kwargs={
                'charge_id': self.object.charge_id
            }
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Update'
        return context


class ChargeDeleteView(
    HotelRoleRequiredMixin,
    DeleteView
):
    model = Charge
    template_name = 'billings/charge_delete.html'
    context_object_name = 'charge'
    pk_url_kwarg = 'charge_id'
    success_url = reverse_lazy('charge_list')

    allowed_roles = [
        'manager',
    ]

    def post(self, request, *args, **kwargs):
        from .services import ChargeService

        self.object = self.get_object()

        try:
            ChargeService.delete_charge(
                charge_id=self.object.charge_id,
                user=request.user,
            )
        except ValidationError as exc:
            messages.error(request, str(exc))
            return redirect(
                'charge_detail',
                charge_id=self.object.charge_id,
            )

        return redirect(self.success_url)


# DISCOUNT VIEWS


class DiscountListView(
    HotelRoleRequiredMixin,
    ListView
):
    model = Discount
    template_name = 'billings/discount_list.html'
    context_object_name = 'discounts'

    allowed_roles = [
        'manager',
        'finance',
    ]


class DiscountDetailView(
    HotelRoleRequiredMixin,
    DetailView
):
    model = Discount
    template_name = 'billings/discount_detail.html'
    context_object_name = 'discount'
    pk_url_kwarg = 'discount_id'

    allowed_roles = [
        'manager',
        'finance',
    ]


class DiscountCreateView(
    HotelRoleRequiredMixin,
    CreateView
):
    model = Discount
    form_class = DiscountForm
    template_name = 'billings/discount_form.html'
    success_url = reverse_lazy('discount_list')

    allowed_roles = [
        'manager',
        'finance',
    ]

    def form_valid(self, form):
        from .services import DiscountService

        bill = form.cleaned_data['bill']
        amount = form.cleaned_data['amount']
        description = form.cleaned_data['description']

        try:
            DiscountService.create_discount(
                bill_id=bill.bill_id,
                amount=amount,
                description=description,
                user=self.request.user,
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Create'
        return context


class DiscountUpdateView(
    HotelRoleRequiredMixin,
    UpdateView
):
    model = Discount
    form_class = DiscountForm
    template_name = 'billings/discount_form.html'
    pk_url_kwarg = 'discount_id'

    allowed_roles = [
        'manager',
        'finance',
    ]

    def form_valid(self, form):
        from .services import DiscountService

        try:
            DiscountService.update_discount(
                discount_id=self.object.discount_id,
                amount=form.cleaned_data['amount'],
                description=form.cleaned_data['description'],
                user=self.request.user,
            )
        except (ValidationError, PermissionDenied) as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy(
            'discount_detail',
            kwargs={
                'discount_id': self.object.discount_id
            }
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Update'
        return context


class DiscountDeleteView(
    HotelRoleRequiredMixin,
    DeleteView
):
    model = Discount
    template_name = 'billings/discount_delete.html'
    context_object_name = 'discount'
    pk_url_kwarg = 'discount_id'
    success_url = reverse_lazy('discount_list')

    # Delete = manager only
    allowed_roles = [
        'manager',
    ]


# PAYMENT VIEWS


class PaymentListView(
    HotelRoleRequiredMixin,
    ListView
):
    model = Payment
    template_name = 'billings/payment_list.html'
    context_object_name = 'payments'

    allowed_roles = [
        'manager',
        'finance',
    ]


class PaymentDetailView(
    HotelRoleRequiredMixin,
    DetailView
):
    model = Payment
    template_name = 'billings/payment_detail.html'
    context_object_name = 'payment'
    pk_url_kwarg = 'payment_id'

    allowed_roles = [
        'manager',
        'finance',
    ]


class PaymentCreateView(
    HotelRoleRequiredMixin,
    CreateView
):
    model = Payment
    form_class = PaymentForm
    template_name = 'billings/payment_form.html'
    success_url = reverse_lazy('payment_list')

    allowed_roles = [
        'manager',
        'finance',
    ]

    def form_valid(self, form):
        from .services import PaymentService

        bill = form.cleaned_data['bill']
        amount = form.cleaned_data['amount']

        try:
            self.object = PaymentService.create_payment(
                        bill_id=bill.bill_id,
                        amount=amount,
                        payment_method=form.cleaned_data['payment_method'],
                        user=self.request.user,
                    )
        except ValidationError as exc:
            form.add_error('amount', exc)
            return self.form_invalid(form)

        return redirect(self.get_success_url())


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Create'
        return context


class PaymentUpdateView(
    HotelRoleRequiredMixin,
    UpdateView
):
    model = Payment
    form_class = PaymentForm
    template_name = 'billings/payment_form.html'
    pk_url_kwarg = 'payment_id'

    allowed_roles = [
        'manager',
        'finance',
    ]

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.status in ['posted', 'refunded']:
            raise PermissionDenied(
            'Posted or refunded payments cannot be edited.'
    )   
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            'payment_detail',
            kwargs={
                'payment_id': self.object.payment_id
            }
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Update'
        return context


class PaymentDeleteView(
    HotelRoleRequiredMixin,
    DeleteView
):
    model = Payment
    template_name = 'billings/payment_delete.html'
    context_object_name = 'payment'
    pk_url_kwarg = 'payment_id'
    success_url = reverse_lazy('payment_list')

    allowed_roles = [
        'manager',
    ]

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.status in ['posted', 'refunded']:
            messages.error(
                request,
                'Posted or refunded payments cannot be deleted.'
            )
            return redirect(
                'payment_detail',
                payment_id=self.object.payment_id
            )

        return super().post(request, *args, **kwargs)
