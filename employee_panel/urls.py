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

    path(
        "tasks/",
        views.my_tasks,
        name="employee_tasks"
    ),

    path(
        "tasks/<int:task_id>/done/",
        views.mark_my_task_done,
        name="mark_my_task_done"
    ),

]
