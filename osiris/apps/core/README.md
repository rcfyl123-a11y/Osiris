# IP Security (core)

Подсистема контролирует доступ по IP, проверяет привязку пользователя к рабочему месту и фиксирует события аудита.

## Режимы

* `DJANGO_IP_MODE=audit` — никого не блокируем, только пишем аудит.
* `DJANGO_IP_MODE=perimeter` — блокируем IP вне allowlist.
* `DJANGO_IP_MODE=bind` — perimeter + проверка, что пользователь привязан к рабочему месту.

## Настройки окружения

* `DJANGO_IP_ALLOWLIST` — список IP/CIDR через запятую.
* `DJANGO_TRUST_X_FORWARDED_FOR` — доверять `X-Forwarded-For` (только для trusted proxies).
* `DJANGO_TRUSTED_PROXIES` — список подсетей доверенных прокси.
* `DJANGO_IP_FAIL_CLOSED_EMPTY_ALLOWLIST` — блокировать всех при пустом allowlist.
* `DJANGO_IP_EXEMPT_PATHS` — пути, исключенные из проверки (например `/health/`).
* `DJANGO_IP_APPLY_TO_STATIC_MEDIA` — применять ли perimeter к `/static/` и `/media/`.
* `DJANGO_IP_RECORD_THROTTLE_SECONDS` — троттлинг обновлений `UserIPRecord`.
* `DJANGO_BIND_ENFORCE` — в режиме bind блокировать пользователя (1) или только писать событие (0).
* `DJANGO_SECURITY_RETENTION_DAYS` — срок хранения событий.
* `DJANGO_DOWNLOAD_REQUIRE_AUTH` — требовать аутентификацию для загрузок.
* `DJANGO_DOWNLOAD_REQUIRE_BIND` — требовать bind для загрузок (в режиме bind).
* `DJANGO_DOWNLOAD_PATHS` — список путей/префиксов загрузок.

## Обслуживание

Для очистки старых событий:

```bash
python manage.py purge_security_events --days 90
```

Можно запускать по cron/Task Scheduler с нужным периодом.
