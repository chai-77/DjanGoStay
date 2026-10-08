# staff/urls.py
from django.urls import path
from .views import (
    StaffListView, StaffDetailView, StaffCreateView, StaffUpdateView, StaffDeleteView
)

urlpatterns = [
    path('', StaffListView.as_view(), name='staff_list'),
    path('<int:staff_id>/', StaffDetailView.as_view(), name='staff_detail'),
    path('create/', StaffCreateView.as_view(), name='staff_create'),
    path('<int:staff_id>/update/', StaffUpdateView.as_view(), name='staff_update'),
    path('<int:staff_id>/delete/', StaffDeleteView.as_view(), name='staff_delete'),
]