# Карта интеграций между приложениями

Таблица фиксирует текущие и планируемые интеграции между приложениями.

| from_app | to_app | тип | что передается | статус |
| --- | --- | --- | --- | --- |
| chat | rca | data | `ChatRoom.org` связывается с `rca.Org` | done |
| panel | core | data | аудит действий/просмотров через `core.SecurityEvent` | done |
| core | auth | data | связи моделей с `AUTH_USER_MODEL` | done |
| polls | core | data | пересечение домена рабочих мест (`Workplace` vs `Workstation`) | partial |
| blog | rca | data | связь новостей с орг.единицами (идея) | planned |
| blog | chat | notifications | уведомления о важных новостях (идея) | planned |
| chat | polls | notifications | анонсы опросов в чат (идея) | planned |
| rca | panel | data | орг.роли/должности для прав доступа (идея) | planned |
| rca | polls | data | аудитории опросов по орг.структуре (идея) | planned |
| core | rca | data | сопоставление IP-данных с кадрами | planned |
