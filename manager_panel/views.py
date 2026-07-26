from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError

from core.decorators import role_required
from ad_management.services import get_admin_dashboard_stats, get_employee_list
from .models import LeaveRequest


@login_required
@role_required("GG_Managers")
def manager_dashboard(request):
    stats = get_admin_dashboard_stats()
    pending_requests = (
        LeaveRequest.objects
        .filter(status=LeaveRequest.Status.PENDING)
        .select_related("employee")
        .order_by("start_date")
    )

    return render(
        request,
        "manager_dashboard.html",
        {
            "stats": stats,
            "pending_requests": pending_requests,
        },
    )


@login_required
@role_required("GG_Managers")
def employee_list(request):
    employees = get_employee_list()
    return render(
        request,
        "manage_employees.html",
        {"employees": employees},
    )


@login_required
@role_required("GG_Managers")
def leave_requests_manage(request):
    status_filter = request.GET.get("status", "").upper()
    valid_statuses = dict(LeaveRequest.Status.choices)

    requests_qs = LeaveRequest.objects.select_related("employee", "reviewed_by").order_by("-created_at")
    if status_filter in valid_statuses:
        requests_qs = requests_qs.filter(status=status_filter)

    return render(
        request,
        "manage_leave_requests.html",
        {
            "leave_requests": requests_qs,
            "status_filter": status_filter,
            "statuses": LeaveRequest.Status.choices,
        },
    )


SAFE_NEXT_VIEWS = {"manager_dashboard", "leave_requests_manage"}


@login_required
@role_required("GG_Managers")
def review_leave_request(request, request_id):
    leave_request = get_object_or_404(LeaveRequest, pk=request_id)

    next_view = request.POST.get("next", "manager_dashboard")
    if next_view not in SAFE_NEXT_VIEWS:
        next_view = "manager_dashboard"

    if request.method == "POST":
        action = request.POST.get("action")
        note = request.POST.get("note", "")

        try:
            if action == "approve":
                leave_request.approve(reviewer=request.user, note=note)
                messages.success(request, f"Approved leave request for {leave_request.employee.username}.")
            elif action == "reject":
                leave_request.reject(reviewer=request.user, note=note)
                messages.success(request, f"Rejected leave request for {leave_request.employee.username}.")
        except ValidationError as e:
            messages.error(request, str(e))

    return redirect(next_view)
