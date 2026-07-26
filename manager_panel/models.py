from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class LeaveRequest(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="leave_requests",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=255, blank=True)

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_leave_requests",
    )
    review_note = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- state machine ---
    # PENDING -> APPROVED    (manager only, via approve())
    # PENDING -> REJECTED    (manager only, via reject())
    # PENDING -> CANCELLED   (employee only — not wired into the UI yet)
    # APPROVED / REJECTED / CANCELLED are terminal: no further transitions allowed.

    def approve(self, reviewer, note=""):
        if self.status != self.Status.PENDING:
            raise ValidationError(f"Cannot approve a request that is already {self.status}.")
        self.status = self.Status.APPROVED
        self.reviewed_by = reviewer
        self.review_note = note
        self.save()

    def reject(self, reviewer, note=""):
        if self.status != self.Status.PENDING:
            raise ValidationError(f"Cannot reject a request that is already {self.status}.")
        self.status = self.Status.REJECTED
        self.reviewed_by = reviewer
        self.review_note = note
        self.save()

    def __str__(self):
        return f"{self.employee.username} [{self.start_date} -> {self.end_date}] ({self.status})"


class Task(models.Model):

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        DONE = "DONE", "Done"

    title = models.CharField(max_length=200)
    description = models.CharField(max_length=500, blank=True)

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks_assigned",
    )

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)

    # Set when a task is handed off because the original assignee went on
    # leave — a simple audit trail, not itself enforced by any rule.
    reassigned_from = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks_reassigned_away",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def reassign(self, new_assignee):
        self.reassigned_from = self.assigned_to
        self.assigned_to = new_assignee
        self.save()

    def mark_done(self):
        self.status = self.Status.DONE
        self.save()

    def __str__(self):
        return f"{self.title} -> {self.assigned_to.username} ({self.status})"
