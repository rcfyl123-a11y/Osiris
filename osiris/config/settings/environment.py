import os
import sys
from pathlib import Path

from loguru import logger

log = logger  # один общий логгер проекта

# Переменные каталогов проекта
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent  # D:\Projects\gitea\Osiris\src\osiris
BASE_DIR = PROJECT_DIR.parent  # D:\Projects\gitea\Osiris\src
VAR_DIR = PROJECT_DIR / "var"  # D:\Projects\gitea\Osiris\src\var
VAR_DIR.mkdir(exist_ok=True)

# Настройки проекта
# IBM DB2
USE_IBM = False
IBM_DB_HOME = PROJECT_DIR / "data" / "clidriver"

# RCA
RCA_APP_DIR = PROJECT_DIR / "apps" / "rca"
RCA_DUCKDB_PATH = RCA_APP_DIR / "data" / "rca.duckdb"

# где лежат XML выгрузки (дефолт — каталог внутри проекта, но можно переопределить через env)
# Ожидаем структуру PROJECT_DIR/data/rca_xml с выгрузками по умолчанию.
RCA_XML_DIR = Path(os.environ.get("RCA_XML_DIR", str(PROJECT_DIR / "data" / "rca_xml")))


if USE_IBM and IBM_DB_HOME.exists() and IBM_DB_HOME.is_dir():
    log.debug("Включено использование драйвера IBM")
    try:
        os.environ["IBM_DB_HOME"] = str(IBM_DB_HOME)
        log.debug(f"IBM_DB_HOME установлено: {os.environ['IBM_DB_HOME']}")

        # Добавляем lib и bin в PATH
        clidriver_lib_path = IBM_DB_HOME / "lib"
        clidriver_bin_path = IBM_DB_HOME / "bin"
        # Windows-специфичный хук для поиска DLL; на других платформах он недоступен.
        if os.name == "nt" or hasattr(os, "add_dll_directory"):
            os.add_dll_directory(clidriver_bin_path)
        paths_to_add = [clidriver_lib_path, clidriver_bin_path]

        current_path = os.environ.get("PATH", "")
        new_paths = []

        for path in paths_to_add:
            if path.exists() and path.is_dir() and str(path) not in current_path:
                new_paths.append(str(path))

        if new_paths:
            new_paths_str = ";".join(new_paths)
            os.environ["PATH"] = f"{new_paths_str};{current_path}"
            log.debug(f"Добавлены пути в PATH: {new_paths_str}")
        else:
            log.debug("Все необходимые пути уже присутствуют в PATH")

    except Exception as e:
        log.error("Не удалось установить IBM CLI Driver")
        log.error("IBM_DB_HOME")
        log.error(e)


log.debug(f"PROJECT_DIR: {PROJECT_DIR}")
log.debug(f"BASE_DIR: {BASE_DIR}")
log.debug(f"VAR_DIR: {VAR_DIR}")

__NEV = PROJECT_DIR / "config" / "docker" / ".env"

try:
    if __NEV.exists():
        from dotenv import load_dotenv

        load_dotenv(dotenv_path=__NEV)
        log.debug(".env - Загружен")
        log.debug(f"Путь к .env: {__NEV}")
except Exception as e:
    log.error(f"Не удалось найти и загрузить .env. Путь: {__NEV}, ошибка: {e}")

def _env_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


# Базовые настройки
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY") or os.getenv("SECRET_KEY", "dev-insecure-key-change-me")

_debug_env = os.getenv("DJANGO_DEBUG") or os.getenv("DEBUG")
if _debug_env is None:
    DEBUG = "runserver" in sys.argv
else:
    DEBUG = _env_bool(_debug_env)

ENABLE_DEBUG_TOOLBAR = DEBUG and _env_bool(os.getenv("DJANGO_ENABLE_DEBUG_TOOLBAR", "0"))

_default_allowed_hosts = "localhost,127.0.0.1,0.0.0.0"
_allowed_hosts_env = os.getenv("DJANGO_ALLOWED_HOSTS") or os.getenv("ALLOWED_HOSTS")
ALLOWED_HOSTS = [h.strip() for h in (_allowed_hosts_env or _default_allowed_hosts).split(",") if h.strip()]

log.debug(f"DEBUG: {DEBUG}")

# Язык и время
LANGUAGE_CODE = os.getenv("DJANGO_LANGUAGE_CODE", "ru-ru")
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "Europe/Moscow")
USE_I18N = True
USE_TZ = True

# URLs
ROOT_URLCONF = "config.urls"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# База данных
POSTGRES_READY = all(
    os.getenv(k) for k in ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST")
)

# Безопасность
CSRF_TRUSTED_ORIGINS = [
    o for o in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o
]

# Debug Toolbar
INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}
