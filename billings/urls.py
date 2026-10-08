# billing/urls.py
from django.urls import path
from .views import (
    BillListView, BillDetailView, BillCreateView, BillUpdateView, BillDeleteView,
    ChargeListView, ChargeDetailView, ChargeCreateView, ChargeUpdateView, ChargeDeleteView,
    DiscountListView, DiscountDetailView, DiscountCreateView, DiscountUpdateView, DiscountDeleteView,
    PaymentListView, PaymentDetailView, PaymentCreateView, PaymentUpdateView, PaymentDeleteView
)

urlpatterns = [
    # Bill URLs
    path('bills/', BillListView.as_view(), name='bill_list'),
    path('bills/<int:bill_id>/', BillDetailView.as_view(), name='bill_detail'),
    path('bills/create/', BillCreateView.as_view(), name='bill_create'),
    path('bills/<int:bill_id>/update/', BillUpdateView.as_view(), name='bill_update'),
    path('bills/<int:bill_id>/delete/', BillDeleteView.as_view(), name='bill_delete'),

    # Charge URLs
    path('charges/', ChargeListView.as_view(), name='charge_list'),
    path('charges/<int:charge_id>/', ChargeDetailView.as_view(), name='charge_detail'),
    path('charges/create/', ChargeCreateView.as_view(), name='charge_create'),
    path('charges/<int:charge_id>/update/', ChargeUpdateView.as_view(), name='charge_update'),
    path('charges/<int:charge_id>/delete/', ChargeDeleteView.as_view(), name='charge_delete'),

    # Discount URLs
    path('discounts/', DiscountListView.as_view(), name='discount_list'),
    path('discounts/<int:discount_id>/', DiscountDetailView.as_view(), name='discount_detail'),
    path('discounts/create/', DiscountCreateView.as_view(), name='discount_create'),
    path('discounts/<int:discount_id>/update/', DiscountUpdateView.as_view(), name='discount_update'),
    path('discounts/<int:discount_id>/delete/', DiscountDeleteView.as_view(), name='discount_delete'),

    # Payment URLs
    path('payments/', PaymentListView.as_view(), name='payment_list'),
    path('payments/<int:payment_id>/', PaymentDetailView.as_view(), name='payment_detail'),
    path('payments/create/', PaymentCreateView.as_view(), name='payment_create'),
    path('payments/<int:payment_id>/update/', PaymentUpdateView.as_view(), name='payment_update'),
    path('payments/<int:payment_id>/delete/', PaymentDeleteView.as_view(), name='payment_delete'),
]