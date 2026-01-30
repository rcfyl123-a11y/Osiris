"""Context processors for Osiris Django project.

Path: osiris/config/context_processors.py
"""

from django.contrib import messages


def toast_messages(request):
    """Return lazily evaluated Django messages for template toast rendering."""
    return {"toast_messages": messages.get_messages(request)}
