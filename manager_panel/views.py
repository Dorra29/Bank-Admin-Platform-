from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import ValidationError

from core.decorators import role_required
from ad_management.services import get_admin_dashboard_stats, get_employee_list
from .models import LeaveRequest, Task


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


@login_required
@role_required("GG_Managers")
def tasks_list(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        assigned_to_username = request.POST.get("assigned_to")
        description = request.POST.get("description", "")

        if not title or not assigned_to_username:
            messages.error(request, "Title and assignee are required.")
        else:
            try:
                assignee = User.objects.get(username=assigned_to_username)
                Task.objects.create(
                    title=title,
                    description=description,
                    assigned_to=assignee,
                    assigned_by=request.user,
                )
                messages.success(request, f"Task assigned to {assignee.username}.")
            except User.DoesNotExist:
                messages.error(request, "That employee hasn't logged into the site yet, so they have no account here.")

        return redirect("tasks_list")

    tasks = Task.objects.select_related("assigned_to", "assigned_by", "reassigned_from").order_by("status", "-created_at")
    employees = get_employee_list()

    return render(
        request,
        "manage_tasks.html",
        {"tasks": tasks, "employees": employees},
    )


@login_required
@role_required("GG_Managers")
def mark_task_done(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    if request.method == "POST":
        task.mark_done()
        messages.success(request, f"Marked '{task.title}' as done.")
    return redirect("tasks_list")


@login_required
@role_required("GG_Managers")
def reassign_tasks_for_leave(request, request_id):
    leave_request = get_object_or_404(LeaveRequest, pk=request_id)
    open_tasks = Task.objects.filter(assigned_to=leave_request.employee, status=Task.Status.OPEN)
    employees = [e for e in get_employee_list() if e["username"] != leave_request.employee.username]

    if request.method == "POST":
        reassigned_count = 0
        for task in open_tasks:
            new_username = request.POST.get(f"assignee_{task.id}")
            if new_username and new_username != "skip":
                try:
                    new_user = User.objects.get(username=new_username)
                    task.reassign(new_user)
                    reassigned_count += 1
                except User.DoesNotExist:
                    pass

        messages.success(request, f"Reassigned {reassigned_count} task(s).")
        return redirect("leave_requests_manage")

    return render(
        request,
        "reassign_tasks.html",
        {
            "leave_request": leave_request,
            "open_tasks": open_tasks,
            "employees": employees,
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

                has_open_tasks = Task.objects.filter(
                    assigned_to=leave_request.employee, status=Task.Status.OPEN
                ).exists()
                if has_open_tasks:
                    return redirect("reassign_tasks_for_leave", request_id=leave_request.id)

            elif action == "reject":
                leave_request.reject(reviewer=request.user, note=note)
                messages.success(request, f"Rejected leave request for {leave_request.employee.username}.")
        except ValidationError as e:
            messages.error(request, str(e))

    return redirect(next_view)
