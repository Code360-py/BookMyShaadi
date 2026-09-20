from accounts.auth import get_current_staff


def staff_context(request):
    return {"current_staff": get_current_staff(request)}
