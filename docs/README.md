# Документация Osiris

## Навигация
- Начинайте с этого файла и переходите к паспортам приложений в `about-*.md`.
- Все ссылки внутри docs относительные и должны оставаться валидными.
- Новые паспорта приложений создавайте по шаблону из `_templates/about-app-template.md`.

## Оглавление: паспорта приложений
- [Blog](about-blog.md)
- [Chat](about-chat.md)
- [Core](about-core.md)
- [Panel](about-panel.md)
- [Polls](about-polls.md)
- [RCA](about-rca.md)

## Общие документы
- [Performance baseline](perf-baseline.md)
- [Связи моделей между приложениями](app-model-relationships.md)
- [Карта интеграций](integrations.md)
- [ADR 0001: Workstation vs Workplace](adr/0001-workstation-vs-workplace.md)
- [Шаблон паспорта приложения](_templates/about-app-template.md)

## Проверки качества документации

```bash
python scripts/docs/check_links.py
```
