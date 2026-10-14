from .models import AuditLog


def _client_ip(request) -> str | None:
    if request is None:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log(
    request,
    action: str,
    *,
    staff=None,
    model_name: str = "",
    object_id=None,
    object_repr: str = "",
    success: bool = True,
    detail: str = "",
) -> AuditLog:
    """Write a single audit entry. Never raises."""
    try:
        if staff is None:
            # try to pull from request session
            try:
                from accounts.models import Staff
                sid = request.session.get("staff_id") if request else None
                if sid:
                    staff = Staff.objects.filter(pk=sid).first()
            except Exception:
                staff = None

        ua = ""
        if request is not None:
            ua = (request.META.get("HTTP_USER_AGENT") or "")[:255]

        return AuditLog.objects.create(
            actor=staff,
            actor_email=getattr(staff, "email", "") or "",
            action=action,
            model_name=model_name or "",
            object_id=str(object_id) if object_id is not None else "",
            object_repr=object_repr or "",
            success=success,
            detail=detail or "",
            ip=_client_ip(request),
            user_agent=ua,
        )
    except Exception:
        # never let audit failures break the request
        return None
