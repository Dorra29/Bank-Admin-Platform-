from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from core.decorators import role_required
from ad_management.services import get_ad_user_profile
from manager_panel.models import LeaveRequest, Task


@login_required
@role_required("GG_Employees")
def employee_dashboard(request):
    profile = get_ad_user_profile(request.user.username)
    return render(
        request,
        "employee_dashboard.html",
        {"profile": profile},
    )


@login_required
@role_required("GG_Employees")
def leave_requests(request):

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

        return redirect("employee_leave_requests")

    my_requests = LeaveRequest.objects.filter(employee=request.user).order_by("-created_at")

    return render(
        request,
        "employee_leave.html",
        {"my_requests": my_requests},
    )


@login_required
@role_required("GG_Employees")
def my_tasks(request):
    tasks = (
        Task.objects
        .filter(assigned_to=request.user)
        .select_related("assigned_by", "reassigned_from")
        .order_by("status", "-created_at")
    )
    return render(
        request,
        "employee_tasks.html",
        {"tasks": tasks},
    )


@login_required
@role_required("GG_Employees")
def mark_my_task_done(request, task_id):
    # assigned_to=request.user in the lookup itself — an employee can only
    # ever mark their own tasks done, not anyone else's, even by guessing IDs.
    task = get_object_or_404(Task, pk=task_id, assigned_to=request.user)
    if request.method == "POST":
        task.mark_done()
        messages.success(request, f"Marked '{task.title}' as done.")
    return redirect("employee_tasks")
