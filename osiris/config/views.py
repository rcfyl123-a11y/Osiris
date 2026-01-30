"""Project-level views for Osiris.

Path: osiris/config/views.py
"""

from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone


def health_check(request):
    """Return health status as JSON or HTML depending on the request headers."""
    payload = {
        "status": "ok",
        "details": {
            "timestamp": timezone.now().isoformat(),
            "service": "osiris",
        },
    }

    accepts_json = "application/json" in request.headers.get("Accept", "")
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if accepts_json or is_ajax:
        return JsonResponse(payload)

    return render(request, "health/index.html", {"health": payload})
