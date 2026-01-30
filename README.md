# Проект Osiris (Django)

## Обзор
Osiris — Django-проект с модульной архитектурой и автоматическим
обнаружением приложений в каталоге `osiris/apps`.

## Архитектура
- **Основной каталог проекта**: `/workspace/Osiris/osiris` — настройки и конфигурация.
- **Каталог приложений**: `/workspace/Osiris/osiris/apps` — Django‑приложения,
  которые автоматически регистрируются.
- **Конфигурация**: модульный подход через пакет `config`.

## Возможности
- Автоматическое обнаружение приложений и добавление в `INSTALLED_APPS`.
- Модульная сборка настроек из `osiris/config/settings`.
- Динамическая маршрутизация URL для приложений.

## Приложения
- **core** — базовые страницы, домашний экран и базовые middleware/инфраструктура.
- **blog** — новости и блог: публикация, редактирование и просмотр новостных записей.
- **chat** — чаты с комнатами, участниками, сообщениями и вложениями
  (поддерживает личные и групповые комнаты).
- **panel** — внутренний административный интерфейс и вспомогательные страницы.
- **polls** — пример приложения с опросами/голосованиями.
- **rca** — импорт и хранение штатного расписания/оргструктуры с историчностью (SCD2),
  включая команды синхронизации и загрузки данных.

## Быстрый старт

1. **Установить зависимости**:
   ```bash
   pip install -r osiris/requirements.txt
   ```

2. **Выполнить миграции**:
   ```bash
   cd osiris
   python manage.py migrate
   ```

3. **Запустить сервер разработки**:
   ```bash
   python manage.py runserver
   ```

## Локальные проверки (как в CI)

```bash
python -m compileall osiris
python osiris/manage.py check
python osiris/manage.py test
```

При необходимости переменные окружения можно задать через
`osiris/config/docker/.env` на основе примера
`osiris/config/docker/.env.example`.

## Добавление новых приложений

Чтобы добавить новое приложение:
1. Создайте каталог в `/workspace/Osiris/osiris/apps/`.
2. Инициализируйте Django‑приложение с `apps.py` и `__init__.py`.
3. При необходимости добавьте `urls.py`.
4. Приложение будет автоматически обнаружено, а его `AppConfig` добавится в `INSTALLED_APPS`.
5. Если у приложения есть `urls.py`, то оно будет автоматически подключено в общий роутер.

## Конфигурационные файлы

- `osiris/config/`: пакет конфигурации с настройками окружения.
- `osiris/config/urls.py`: главная маршрутизация URL с подключением приложений.
- `osiris/config/asgi.py`: конфигурация ASGI.
- `osiris/config/wsgi.py`: конфигурация WSGI.
- `osiris/manage.py`: точка входа Django management.

## Структура проекта
```
/workspace/
├── Osiris/                 # Корень репозитория
│   ├── osiris/             # Пакет Django проекта
│   │   ├── config/         # Настройки и ASGI/WSGI
│   │   ├── manage.py       # Management-утилита
│   │   ├── apps/           # Каталог приложений
│   │   │   ├── core/       # Базовые страницы и middleware
│   │   │   ├── blog/       # Новости и блог
│   │   │   ├── chat/       # Чат
│   │   │   ├── panel/      # Внутренний интерфейс
│   │   │   ├── polls/      # Пример опросов
│   │   │   └── rca/        # Штатное расписание (SCD2)
│   │   └── templates/      # Общие шаблоны
│   └── README.md           # Этот файл
```

## Переменные окружения
### Базовые
- `DJANGO_SECRET_KEY` (или `SECRET_KEY`): секретный ключ Django (по умолчанию — заглушка).
- `DJANGO_DEBUG` (или `DEBUG`): режим отладки (`true/false`, по умолчанию зависит от команды `runserver`).
- `DJANGO_ALLOWED_HOSTS` (или `ALLOWED_HOSTS`): список разрешённых хостов через запятую
  (по умолчанию `localhost,127.0.0.1,0.0.0.0`).
- `DJANGO_ENABLE_DEBUG_TOOLBAR`: включить Debug Toolbar (`1/true/yes`, по умолчанию `0`).

### База данных
- `DATABASE_URL`: строка подключения (поддерживаются `postgresql://` и `sqlite:///`).
- `DB_ENGINE`: явный выбор движка (`postgresql` или `sqlite`), если нет `DATABASE_URL`.
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: параметры для `DB_ENGINE=postgresql`.
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`:
  используются как резерв для PostgreSQL, если не задан `DATABASE_URL` и `DB_ENGINE`.

### Логи
- `DJANGO_LOG_LEVEL` (или `LOG_LEVEL`): уровень логирования (по умолчанию `DEBUG` в dev и `INFO` в остальных случаях).
