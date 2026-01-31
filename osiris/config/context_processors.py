"""Контекстные процессоры для Django-проекта Osiris.

Путь: osiris/config/context_processors.py
"""

from django.contrib import messages


def toast_messages(request):
    """Вернуть ленивые Django-сообщения для toast-уведомлений в шаблонах."""
    return {"toast_messages": messages.get_messages(request)}
