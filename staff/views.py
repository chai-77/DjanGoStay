from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    TemplateView,
)

from .models import Staff
from .forms import StaffCreateForm, StaffForm
from .mixins import HotelRoleRequiredMixin


class RoleLoginView(LoginView):
    """Send each hotel role to its first permitted workflow."""

    role_destinations = {
        'manager': 'room_type_list',
        'receptionist': 'booking_list',
        'housekeeping': 'housekeeping_list',
        'finance': 'bill_list',
        'cook': 'role_home',
        'server': 'role_home',
        'maintenance': 'role_home',
    }

    def get_success_url(self):
        redirect_url = self.get_redirect_url()
        if redirect_url:
            return redirect_url

        try:
            role = self.request.user.staff_profile.role
        except AttributeError as error:
            raise PermissionDenied(
                'Your account does not have a staff profile.'
            ) from error

        destination = self.role_destinations.get(role)
        if destination is None:
            raise PermissionDenied(
                'Your staff role does not have an application landing page.'
            )
        return reverse(destination)


class RoleHomeView(TemplateView):
    template_name = 'staff/role_home.html'


class StaffListView(
    HotelRoleRequiredMixin,
    ListView
):
    model = Staff
    template_name = 'staff/staff_list.html'
    context_object_name = 'staff_list'

    allowed_roles = [
        'manager',
    ]


class StaffDetailView(
    HotelRoleRequiredMixin,
    DetailView
):
    model = Staff
    template_name = 'staff/staff_detail.html'
    context_object_name = 'staff'
    pk_url_kwarg = 'staff_id'

    allowed_roles = [
        'manager',
    ]


class StaffCreateView(
    HotelRoleRequiredMixin,
    CreateView
):
    model = Staff
    form_class = StaffCreateForm
    template_name = 'staff/staff_form.html'
    success_url = reverse_lazy('staff_list')

    allowed_roles = [
        'manager',
    ]

    @transaction.atomic
    def form_valid(self, form):
        staff_user = User.objects.create_user(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password1'],
            first_name=form.instance.first_name,
            last_name=form.instance.last_name,
        )
        form.instance.user = staff_user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Create'
        return context


class StaffUpdateView(
    HotelRoleRequiredMixin,
    UpdateView
):
    model = Staff
    form_class = StaffForm
    template_name = 'staff/staff_form.html'
    pk_url_kwarg = 'staff_id'

    allowed_roles = [
        'manager',
    ]

    def get_success_url(self):
        return reverse_lazy(
            'staff_detail',
            kwargs={'staff_id': self.object.staff_id}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Update'
        return context


class StaffDeleteView(
    HotelRoleRequiredMixin,
    DeleteView
):
    model = Staff
    template_name = 'staff/staff_delete.html'
    context_object_name = 'staff'
    pk_url_kwarg = 'staff_id'
    success_url = reverse_lazy('staff_list')

    allowed_roles = [
        'manager',
    ]
