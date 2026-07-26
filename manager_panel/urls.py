from django.urls import path
from . import views


urlpatterns = [

    path(
        "",
        views.manager_dashboard,
        name="manager_dashboard"
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

]
