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
    employees = get_employee_list()
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
            "employees": employees,
            "pending_requests": pending_requests,
        },
    )


@login_required
@role_required("GG_Managers")
def review_leave_request(request, request_id):
    leave_request = get_object_or_404(LeaveRequest, pk=request_id)

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

    return redirect("manager_dashboard")
