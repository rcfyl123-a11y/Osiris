# config/settings/logging.py
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from loguru import logger

from .environment import PROJECT_DIR, DEBUG


# === Пути и уровень логирования ===

LOG_DIR: Path = PROJECT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_LEVEL = os.getenv("DJANGO_LOG_LEVEL", "DEBUG" if DEBUG else "INFO").upper()


# === Адаптер: стандартный logging -> loguru ===

class LoguruHandler(logging.Handler):
    """
    Хендлер, который принимает записи стандартного logging
    и прокидывает их в loguru.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            # пытаемся использовать уровень по имени (INFO, WARNING и т.п.)
            level = logger.level(record.levelname).name
        except ValueError:
            # если такого уровня нет в loguru — используем числовой
            level = record.levelno

        # поднимаемся по стеку, чтобы источник лога был не из logging-модуля
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(
            depth=depth,
            exception=record.exc_info,
        ).log(level, record.getMessage())


# === Конфигурируем сам loguru ===

# убираем все дефолтные sinks
logger.remove()

# консоль
logger.add(
    sys.stderr,
    level=LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>",
    enqueue=True,
    backtrace=True,
    diagnose=DEBUG,
)

# файл с ротацией/retention/compression
logger.add(
    LOG_DIR / "django.log",
    level=LOG_LEVEL,
    rotation="10 MB",  # новый файл при 10 МБ
    retention="30 days",  # хранить 30 дней
    compression="gz",  # старые архивировать
    enqueue=True,
    backtrace=True,
    diagnose=DEBUG,
)


# === Django LOGGING: всё отправляем в LoguruHandler ===

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,  # не рубим чужие логгеры, а перенастраиваем нужные
    "handlers": {
        "loguru": {
            # вместо "class": "..." — фабрика "()": передаём сам класс
            "()": LoguruHandler,
            "level": "INFO",  # сюда пускаем всё, режет уже Loguru
        },
    },
    "root": {
        "handlers": ["loguru"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        # основной django-логгер
        "django": {
            "handlers": ["loguru"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        # вот эти ребята как раз печатают строки типа "[03/Dec/2025 ...] ..."
        # "django.server": {
        #     "handlers": ["loguru"],
        #     "level": LOG_LEVEL,
        #     "propagate": False,
        # },
        # "django.request": {
        #     "handlers": ["loguru"],
        #     "level": LOG_LEVEL,
        #     "propagate": False,
        # },
    },
}
