from django.urls import path
from . import views


urlpatterns = [

    path(
        "",
        views.employee_dashboard,
        name="employee_dashboard"
    ),

]