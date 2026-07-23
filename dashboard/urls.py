from django.urls import path
from . import views


urlpatterns = [
    path(
        "",
        views.dashboard_redirect,
        name="dashboard"
    ),

     path(
        "no-access/",
        views.no_access,
        name="no_access"
    ),
]