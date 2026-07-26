from django.urls import path
from . import views


urlpatterns = [

    path(
        "",
        views.manager_dashboard,
        name="manager_dashboard"
    ),

    path(
        "employees/",
        views.employee_list,
        name="employee_list"
    ),

    path(
        "leave-requests/<int:request_id>/review/",
        views.review_leave_request,
        name="review_leave_request"
    ),

    path(
        "leave-requests/",
        views.leave_requests_manage,
        name="leave_requests_manage"
    ),

    path(
        "leave-requests/<int:request_id>/reassign-tasks/",
        views.reassign_tasks_for_leave,
        name="reassign_tasks_for_leave"
    ),

    path(
        "tasks/",
        views.tasks_list,
        name="tasks_list"
    ),

    path(
        "tasks/<int:task_id>/done/",
        views.mark_task_done,
        name="mark_task_done"
    ),

]
