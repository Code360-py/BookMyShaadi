from django.db import models


class AuditLog(models.Model):
    ACTION_LOGIN = "LOGIN"
    ACTION_LOGIN_FAILED = "LOGIN_FAILED"
    ACTION_LOGOUT = "LOGOUT"
    ACTION_CREATE = "CREATE"
    ACTION_UPDATE = "UPDATE"
    ACTION_DELETE = "DELETE"
    ACTION_PASSWORD_CHANGE = "PASSWORD_CHANGE"
    ACTION_PASSWORD_RESET = "PASSWORD_RESET"
    ACTION_TOGGLE = "TOGGLE"
    ACTION_CONVERT = "CONVERT"
    ACTION_OTHER = "OTHER"

    ACTION_CHOICES = (
        (ACTION_LOGIN, "Login"),
        (ACTION_LOGIN_FAILED, "Login failed"),
        (ACTION_LOGOUT, "Logout"),
        (ACTION_CREATE, "Create"),
        (ACTION_UPDATE, "Update"),
        (ACTION_DELETE, "Delete"),
        (ACTION_PASSWORD_CHANGE, "Password change"),
        (ACTION_PASSWORD_RESET, "Password reset"),
        (ACTION_TOGGLE, "Toggle"),
        (ACTION_CONVERT, "Convert"),
        (ACTION_OTHER, "Other"),
    )

    actor = models.ForeignKey(
        "accounts.Staff",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="audit_entries",
    )
    actor_email = models.CharField(max_length=255, blank=True)  # fallback if staff deleted

    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)

    success = models.BooleanField(default=True)
    detail = models.TextField(blank=True)

    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {self.action} {self.model_name}#{self.object_id}"
