import logging

from .environment import PROJECT_DIR

log = logging.getLogger("osiris")

# Определение путей
STATICFILES_DIRS_PATHS = [PROJECT_DIR / "static"]
STATIC_ROOT_PATH = PROJECT_DIR / "staticfiles"
MEDIA_ROOT_PATH = PROJECT_DIR / "media"


def ensure_directory(path):
    """Создает директорию, если она не существует"""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        log.info(f"Создана директория: {path}")
    return path


def setup_directories():
    """Создает все необходимые директории для проекта"""
    try:
        # Папки для статики
        for static_dir in STATICFILES_DIRS_PATHS:
            ensure_directory(static_dir)

        # Папка для собранной статики
        ensure_directory(STATIC_ROOT_PATH)

        # Папка для медиа
        ensure_directory(MEDIA_ROOT_PATH)

        log.debug("Все необходимые директории созданы/проверены")
        return True
    except Exception as e:
        log.error(f"Ошибка при создании директорий: {e}")
        return False


# Автоматически создаем директории при импорте
setup_directories()

# Преобразуем пути в строки для Django
STATICFILES_DIRS = [str(path) for path in STATICFILES_DIRS_PATHS]
STATIC_ROOT = str(STATIC_ROOT_PATH)
MEDIA_ROOT = str(MEDIA_ROOT_PATH)

# URL-префиксы
STATIC_URL = "/static/"
MEDIA_URL = "/media/"
