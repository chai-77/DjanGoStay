
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

from staff.views import RoleHomeView, RoleLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path(
        'login/',
        RoleLoginView.as_view(template_name='registration/login.html'),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('home/', RoleHomeView.as_view(), name='role_home'),
    path('rooms/', include('rooms.urls')), 
    path('staff/', include('staff.urls')),
    path('bookings/', include('bookings.urls')),
    path('billings/', include('billings.urls')),
]