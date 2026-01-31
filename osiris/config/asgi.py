"""
ASGI-конфигурация проекта Osiris.
Путь: osiris/config/asgi.py

Экспортирует ASGI-приложение как переменную уровня модуля ``application``.

Подробнее:
https://docs.djangoproject.com/en/stable/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
