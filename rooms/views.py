# rooms/views.py
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Room, RoomType, HousekeepingAssignment
from .forms import RoomForm , RoomTypeForm, HousekeepingAssignmentForm

from staff.mixins import HotelRoleRequiredMixin


# ROOM VIEWS


class RoomListView(
    HotelRoleRequiredMixin,
    ListView
):
    model = Room
    template_name = 'rooms/room_list.html'
    context_object_name = 'rooms'

    allowed_roles = [
        'manager',
        'housekeeping',
    ]

    def get_queryset(self):
        queryset = super().get_queryset().select_related('room_type')

        # Filtering by availability
        # Example: ?is_available=true
        is_available = self.request.GET.get('is_available')

        if is_available is not None and is_available != '':
            available_bool = is_available.lower() == 'true'
            queryset = queryset.filter(
                is_available=available_bool
            )

        # Filtering by room type
        # Example: ?room_type=1
        room_type_id = self.request.GET.get('room_type')

        if room_type_id:
            queryset = queryset.filter(
                room_type_id=room_type_id
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['room_types'] = RoomType.objects.all()

        return context


class RoomDetailView(
    HotelRoleRequiredMixin,
    DetailView
):
    model = Room
    template_name = 'rooms/room_detail.html'
    # tells template call the object "room" 
    context_object_name = 'room'
    # tells Django which URL parameter contains the Room's primary key
    pk_url_kwarg = 'room_id'

    allowed_roles = [
        'manager',
        'housekeeping',
    ]


class RoomCreateView(
    HotelRoleRequiredMixin,
    CreateView
):
    model = Room
    form_class = RoomForm
    template_name = 'rooms/room_form.html'
    success_url = reverse_lazy('room_list')

    allowed_roles = [
        'manager',
        'housekeeping',
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Create'
        return context


class RoomUpdateView(
    HotelRoleRequiredMixin,
    UpdateView
):
    model = Room
    form_class = RoomForm
    template_name = 'rooms/room_form.html'
    pk_url_kwarg = 'room_id'

    allowed_roles = [
        'manager',
        'housekeeping',
    ]

    def get_success_url(self):
        return reverse_lazy(
            'room_detail',
            kwargs={
                'room_id': self.object.room_id
            }
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Update'
        return context


class RoomDeleteView(
    HotelRoleRequiredMixin,
    DeleteView
):
    model = Room
    template_name = 'rooms/room_delete.html'
    context_object_name = 'room'
    pk_url_kwarg = 'room_id'
    success_url = reverse_lazy('room_list')

    # Delete is manager-only
    allowed_roles = [
        'manager',
    ]



# ROOM TYPE VIEWS


class RoomTypeListView(
    HotelRoleRequiredMixin,
    ListView
):
    model = RoomType
    template_name = 'rooms/room_types/room_type_list.html'
    context_object_name = 'room_types'

    allowed_roles = [
        'manager',
    ]


class RoomTypeDetailView(
    HotelRoleRequiredMixin,
    DetailView
):
    model = RoomType
    template_name = 'rooms/room_types/room_type_detail.html'
    context_object_name = 'room_type'
    pk_url_kwarg = 'room_type_id'

    allowed_roles = [
        'manager',
    ]


class RoomTypeCreateView(
    HotelRoleRequiredMixin,
    CreateView
):
    model = RoomType
    form_class = RoomTypeForm
    template_name = 'rooms/room_types/room_type_form.html'
    success_url = reverse_lazy('room_type_list')

    allowed_roles = [
        'manager',
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Create'
        return context


class RoomTypeUpdateView(
    HotelRoleRequiredMixin,
    UpdateView
):
    model = RoomType
    form_class = RoomTypeForm
    template_name = 'rooms/room_types/room_type_form.html'
    pk_url_kwarg = 'room_type_id'

    allowed_roles = [
        'manager',
    ]

    def get_success_url(self):
        return reverse_lazy(
            'room_type_detail',
            kwargs={
                'room_type_id': self.object.room_type_id
            }
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Update'
        return context


class RoomTypeDeleteView(
    HotelRoleRequiredMixin,
    DeleteView
):
    model = RoomType
    template_name = 'rooms/room_types/room_type_delete.html'
    context_object_name = 'room_type'
    pk_url_kwarg = 'room_type_id'
    success_url = reverse_lazy('room_type_list')

    # Delete is manager-only
    allowed_roles = [
        'manager',
    ]


# ============================================================
# HOUSEKEEPING ASSIGNMENT VIEWS
# ============================================================

class HousekeepingListView(
    HotelRoleRequiredMixin,
    ListView
):
    model = HousekeepingAssignment
    template_name = (
        'rooms/house_keeping_assignment/'
        'housekeeping_list.html'
    )
    context_object_name = 'assignments'

    allowed_roles = [
        'manager',
        'housekeeping',
    ]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related('room', 'assigned_to')
        )


class HousekeepingDetailView(
    HotelRoleRequiredMixin,
    DetailView
):
    model = HousekeepingAssignment
    template_name = (
        'rooms/house_keeping_assignment/'
        'housekeeping_detail.html'
    )
    context_object_name = 'assignment'
    pk_url_kwarg = 'assignment_id'

    allowed_roles = [
        'manager',
        'housekeeping',
    ]


class HousekeepingCreateView(
    HotelRoleRequiredMixin,
    CreateView
):
    model = HousekeepingAssignment
    form_class = HousekeepingAssignmentForm
    template_name = (
        'rooms/house_keeping_assignment/'
        'housekeeping_form.html'
    )
    success_url = reverse_lazy('housekeeping_list')

    allowed_roles = [
        'manager',
        'housekeeping',
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Create'
        return context


class HousekeepingUpdateView(
    HotelRoleRequiredMixin,
    UpdateView
):
    model = HousekeepingAssignment
    form_class = HousekeepingAssignmentForm
    template_name = (
        'rooms/house_keeping_assignment/'
        'housekeeping_form.html'
    )
    pk_url_kwarg = 'assignment_id'

    allowed_roles = [
        'manager',
        'housekeeping',
    ]

    def get_success_url(self):
        return reverse_lazy(
            'housekeeping_detail',
            kwargs={
                'assignment_id': self.object.assignment_id
            }
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Update'
        return context


class HousekeepingDeleteView(
    HotelRoleRequiredMixin,
    DeleteView
):
    model = HousekeepingAssignment
    template_name = (
        'rooms/house_keeping_assignment/'
        'housekeeping_delete.html'
    )
    context_object_name = 'assignment'
    pk_url_kwarg = 'assignment_id'
    success_url = reverse_lazy('housekeeping_list')

    # Delete is manager-only
    allowed_roles = [
        'manager',
    ]
