from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from core.decorators import role_required
from ad_management.services import get_ad_user_profile
from manager_panel.models import LeaveRequest


@login_required
@role_required("GG_Employees")
def employee_dashboard(request):

    if request.method == "POST":
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        reason = request.POST.get("reason", "")

        if not start_date or not end_date:
            messages.error(request, "Start and end dates are required.")
        elif start_date > end_date:
            messages.error(request, "Start date must be before end date.")
        else:
            LeaveRequest.objects.create(
                employee=request.user,
                start_date=start_date,
                end_date=end_date,
                reason=reason,
            )
            messages.success(request, "Leave request submitted.")

        return redirect("employee_dashboard")

    profile = get_ad_user_profile(request.user.username)
    my_requests = LeaveRequest.objects.filter(employee=request.user).order_by("-created_at")

    return render(
        request,
        "employee_dashboard.html",
        {"profile": profile, "my_requests": my_requests},
    )
