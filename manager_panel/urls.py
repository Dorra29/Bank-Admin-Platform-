from django.urls import path
from . import views


urlpatterns = [

    path(
        "",
        views.manager_dashboard,
        name="manager_dashboard"
    ),

]