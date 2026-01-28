"""osiris.config.settings — агрегатор модулей настроек Django-проекта."""

# Конфигурация логирования
from .logging import *

# Базовые настройки окружения - пути, переменные, флаги
from .environment import *

# Настройки директорий для статики и медиа с автосозданием папок
from .directories import *

# Регистрация приложений Django
from .installed_apps import *

# Middleware компоненты
from .middleware import *

# Настройки базы данных (PostgreSQL/SQLite)
from .database import *

# Настройки шаблонов и тегов сообщений
from .templates import *

# Валидаторы паролей
from .password_validators import *



# Настройки Debug Toolbar
from .debug_toolbar import *
