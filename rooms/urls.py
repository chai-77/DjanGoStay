from django.urls import path
from .views import (
    RoomListView, RoomDetailView, RoomCreateView, RoomUpdateView, RoomDeleteView,
    RoomTypeListView, RoomTypeDetailView, RoomTypeCreateView, RoomTypeUpdateView, RoomTypeDeleteView,
    HousekeepingListView, HousekeepingDetailView, HousekeepingCreateView, HousekeepingUpdateView, HousekeepingDeleteView
)

urlpatterns = [
    # Room URLs
    path('', RoomListView.as_view(), name='room_list'),
    path('<int:room_id>/', RoomDetailView.as_view(), name='room_detail'),
    path('create/', RoomCreateView.as_view(), name='room_create'),
    path('<int:room_id>/update/', RoomUpdateView.as_view(), name='room_update'),
    path('<int:room_id>/delete/', RoomDeleteView.as_view(), name='room_delete'),

    # RoomType URLs
    path('types/', RoomTypeListView.as_view(), name='room_type_list'),
    path('types/<int:room_type_id>/', RoomTypeDetailView.as_view(), name='room_type_detail'),
    path('types/create/', RoomTypeCreateView.as_view(), name='room_type_create'),
    path('types/<int:room_type_id>/update/', RoomTypeUpdateView.as_view(), name='room_type_update'),
    path('types/<int:room_type_id>/delete/', RoomTypeDeleteView.as_view(), name='room_type_delete'),

path('housekeeping/', HousekeepingListView.as_view(), name='housekeeping_list'),
    path('housekeeping/<int:assignment_id>/', HousekeepingDetailView.as_view(), name='housekeeping_detail'),
    path('housekeeping/create/', HousekeepingCreateView.as_view(), name='housekeeping_create'),
    path('housekeeping/<int:assignment_id>/update/', HousekeepingUpdateView.as_view(), name='housekeeping_update'),
    path('housekeeping/<int:assignment_id>/delete/', HousekeepingDeleteView.as_view(), name='housekeeping_delete'),
]