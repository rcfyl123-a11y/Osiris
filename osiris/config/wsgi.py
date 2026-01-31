"""
WSGI-конфигурация проекта Osiris.
Путь: osiris/config/wsgi.py

Экспортирует WSGI-приложение как переменную уровня модуля ``application``.

Подробнее:
https://docs.djangoproject.com/en/stable/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
