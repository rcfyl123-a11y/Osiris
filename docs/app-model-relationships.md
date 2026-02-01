# Связи моделей между приложениями

Документ фиксирует связи между моделями Django (ForeignKey/ManyToMany) по приложениям, чтобы проще искать дубли/лишние зависимости.

## Общие перекрёстные зависимости между приложениями

- `core.SecurityEvent.user` → `AUTH_USER_MODEL` (пользователь) (`core` ↔ auth). 
- `core.Workstation.allowed_users` (M2M) → `AUTH_USER_MODEL` (`core` ↔ auth). 
- `core.UserIPRecord.user` → `AUTH_USER_MODEL` (`core` ↔ auth). 
- `chat.ChatRoom.org` → `rca.Org` (`chat` ↔ `rca`). 
- `chat.ChatRoom.created_by` → `AUTH_USER_MODEL` (`chat` ↔ auth). 
- `chat.ChatMembership.user` → `AUTH_USER_MODEL` (`chat` ↔ auth). 
- `chat.ChatMessage.sender` → `AUTH_USER_MODEL` (`chat` ↔ auth). 

## Приложение blog

- `blog.News` — нет связей с другими моделями.

## Приложение core

- `SecurityEvent.user` → `AUTH_USER_MODEL` (FK, SET_NULL).
- `Workstation.allowed_users` → `AUTH_USER_MODEL` (M2M).
- `UserIPRecord.user` → `AUTH_USER_MODEL` (FK, CASCADE).
- `AppInventoryHistory.app_inventory` → `core.AppInventory` (FK, CASCADE).

## Приложение polls

- `Poll.audience_workplaces` → `polls.Workplace` (M2M).
- `Question.poll` → `polls.Poll` (FK, CASCADE).
- `Choice.question` → `polls.Question` (FK, CASCADE).
- `Vote.poll` → `polls.Poll` (FK, CASCADE).
- `Vote.workplace` → `polls.Workplace` (FK, SET_NULL).
- `VoteAnswer.vote` → `polls.Vote` (FK, CASCADE).
- `VoteAnswer.question` → `polls.Question` (FK, CASCADE).
- `VoteAnswer.choice` → `polls.Choice` (FK, CASCADE, nullable).

## Приложение chat

- `ChatRoom.org` → `rca.Org` (FK, PROTECT, nullable).
- `ChatRoom.created_by` → `AUTH_USER_MODEL` (FK, SET_NULL, nullable).
- `ChatMembership.room` → `chat.ChatRoom` (FK, CASCADE).
- `ChatMembership.user` → `AUTH_USER_MODEL` (FK, CASCADE).
- `ChatMessage.room` → `chat.ChatRoom` (FK, CASCADE).
- `ChatMessage.sender` → `AUTH_USER_MODEL` (FK, SET_NULL, nullable).
- `ChatMessage.reply_to` → `chat.ChatMessage` (self FK, SET_NULL, nullable).
- `ChatAttachment.message` → `chat.ChatMessage` (FK, CASCADE).

## Приложение panel

- `panel.PanelPermission` — модель только для регистрации permissions; связей с другими моделями нет.

## Приложение rca

- `OrgVersion.org` → `rca.Org` (FK, PROTECT).
- `PostVersion.post` → `rca.Post` (FK, PROTECT).
- `EmployeeSnapshot.employee` → `rca.Employee` (FK, PROTECT).
- `EmployeeSnapshot.batch` → `rca.ImportBatch` (FK, PROTECT).
- `EmployeeSnapshot.org` → `rca.Org` (FK, PROTECT).
- `EmployeeSnapshot.post` → `rca.Post` (FK, PROTECT).
- `VacationPeriod.employee` → `rca.Employee` (FK, PROTECT).
- `VacationPeriod.batch` → `rca.ImportBatch` (FK, PROTECT).
- `VacationPeriod.source_snapshot` → `rca.EmployeeSnapshot` (FK, PROTECT).

## Потенциальные дубли/перекрытия доменных сущностей

- `core.Workstation` и `polls.Workplace` обе описывают рабочие места (IP/label/department). Имеет смысл сравнить поля и назначение, чтобы понять, нужно ли объединение или явное разделение домена.
