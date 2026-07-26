from django.contrib import admin
from .models import LeaveRequest, Task


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ("employee", "start_date", "end_date", "status", "reviewed_by", "created_at")
    list_filter = ("status",)
    search_fields = ("employee__username",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "assigned_to", "status", "assigned_by", "reassigned_from", "created_at")
    list_filter = ("status",)
    search_fields = ("title", "assigned_to__username")
