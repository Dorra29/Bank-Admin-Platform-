from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from accounts import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path("", include("accounts.urls")),

    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='login.html'
        ),
        name='login'
    ),

    path(
        'logout/',
        auth_views.LogoutView.as_view(),
        name='logout'
    ),

     path(
        "dashboard/",
        include("dashboard.urls")
    ),


    path(
        "admin-dashboard/",
        include("admin_panel.urls")
    ),


    path(
        "manager-dashboard/",
        include("manager_panel.urls")
    ),


    path(
        "employee-dashboard/",
        include("employee_panel.urls")
    ),

    path(
        "no-access/",
        include("core.urls")
    ),
    path(
        "admin-panel/",
        include("admin_panel.urls")
    ),
    
]