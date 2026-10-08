from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class HotelRoleRequiredMixin(LoginRequiredMixin):
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        # User must be logged in
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # User must have a Staff profile
        try:
            staff = request.user.staff_profile
        except AttributeError:
            raise PermissionDenied(
                "You do not have a staff profile."
            )

        # User's role must be allowed
        if staff.role not in self.allowed_roles:
            raise PermissionDenied(
                "You do not have permission to access this page."
            )

        return super().dispatch(request, *args, **kwargs)