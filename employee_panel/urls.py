from django.urls import path
from . import views


urlpatterns = [

    path(
        "",
        views.employee_dashboard,
        name="employee_dashboard"
    ),

    path(
        "leave/",
        views.leave_requests,
        name="employee_leave_requests"
    ),

]
