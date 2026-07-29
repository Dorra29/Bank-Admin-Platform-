from django.conf import settings
from django.db import models
from django.utils import timezone


class PasswordExpiration(models.Model):
    """Tracks an admin-assigned expiration date for an AD account's password.

    AD itself doesn't expose a simple per-user "expires on this date" field
    (that requires Fine-Grained Password Policies), so this is enforced at
    our application's login step instead: once expires_on has passed, the
    user is blocked from logging in until an Admin / Support Admin resets
    their password or clears/extends the expiration.
    """

    username = models.CharField(max_length=150, unique=True)
    expires_on = models.DateField()

    set_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="password_expirations_set",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_expired(self):
        return timezone.localdate() >= self.expires_on

    def __str__(self):
        return f"{self.username} expires {self.expires_on}"
