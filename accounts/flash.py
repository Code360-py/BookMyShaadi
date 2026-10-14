"""
Tiny session-based flash message system.
One-shot: read + clear on the next request.
"""

KEY = "_flash"


def add_flash(request, message: str, level: str = "info") -> None:
    """level: info | success | warning | error"""
    request.session.setdefault(KEY, []).append({"message": message, "level": level})


def pop_flashes(request) -> list:
    return request.session.pop(KEY, [])
