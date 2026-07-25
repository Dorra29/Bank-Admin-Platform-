from django.contrib import admin
from .models import LeaveRequest


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ("employee", "start_date", "end_date", "status", "reviewed_by", "created_at")
    list_filter = ("status",)
    search_fields = ("employee__username",)
