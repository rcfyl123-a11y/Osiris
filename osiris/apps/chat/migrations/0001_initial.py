"""Initial migration for chat app."""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

import osiris.apps.chat.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("rca", "__first__"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChatRoom",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("room_type", models.CharField(choices=[("direct", "Личный"), ("group", "Групповой")], default="group", max_length=16, verbose_name="Тип комнаты")),
                ("name", models.CharField(blank=True, help_text="Название для групповых комнат", max_length=255, null=True, verbose_name="Название")),
                ("description", models.TextField(blank=True, help_text="Короткое описание чата", verbose_name="Описание")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, verbose_name="Дата создания")),
                ("is_archived", models.BooleanField(default=False, verbose_name="Архивирован")),
                ("direct_key", models.CharField(blank=True, help_text="Нормализованный ключ участников для личных комнат", max_length=64, null=True, unique=True, verbose_name="Ключ личного чата")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_chat_rooms", to=settings.AUTH_USER_MODEL, verbose_name="Создатель")),
                ("org", models.ForeignKey(blank=True, help_text="Орг.единица, к которой относится чат", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="chat_rooms", to="rca.org", verbose_name="Организационная единица")),
            ],
            options={
                "verbose_name": "Чат",
                "verbose_name_plural": "Чаты",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ChatMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("body", models.TextField(blank=True, verbose_name="Текст сообщения")),
                ("body_format", models.CharField(choices=[("plain", "Текст"), ("markdown", "Markdown")], default="markdown", max_length=16, verbose_name="Формат текста")),
                ("metadata", models.JSONField(blank=True, default=dict, verbose_name="Метаданные")),
                ("sent_at", models.DateTimeField(default=django.utils.timezone.now, verbose_name="Отправлено")),
                ("edited_at", models.DateTimeField(blank=True, null=True, verbose_name="Отредактировано")),
                ("is_deleted", models.BooleanField(default=False, verbose_name="Удалено")),
                ("reply_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="replies", to="chat.chatmessage", verbose_name="Ответ на сообщение")),
                ("room", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="chat.chatroom", verbose_name="Комната")),
                ("sender", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="chat_messages", to=settings.AUTH_USER_MODEL, verbose_name="Отправитель")),
            ],
            options={
                "verbose_name": "Сообщение",
                "verbose_name_plural": "Сообщения",
                "ordering": ["sent_at"],
            },
        ),
        migrations.CreateModel(
            name="ChatMembership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("owner", "Владелец"), ("admin", "Администратор"), ("member", "Участник")], default="member", max_length=16, verbose_name="Роль")),
                ("joined_at", models.DateTimeField(default=django.utils.timezone.now, verbose_name="Дата вступления")),
                ("left_at", models.DateTimeField(blank=True, null=True, verbose_name="Дата выхода")),
                ("last_read_at", models.DateTimeField(blank=True, null=True, verbose_name="Последнее прочтение")),
                ("is_muted", models.BooleanField(default=False, verbose_name="Отключены уведомления")),
                ("room", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to="chat.chatroom", verbose_name="Комната")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chat_memberships", to=settings.AUTH_USER_MODEL, verbose_name="Пользователь")),
            ],
            options={
                "verbose_name": "Участник чата",
                "verbose_name_plural": "Участники чата",
            },
        ),
        migrations.CreateModel(
            name="ChatAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to=osiris.apps.chat.models.chat_upload_path, verbose_name="Файл")),
                ("content_type", models.CharField(blank=True, max_length=128, verbose_name="Тип содержимого")),
                ("original_name", models.CharField(blank=True, max_length=255, verbose_name="Исходное имя")),
                ("size", models.PositiveIntegerField(default=0, verbose_name="Размер (байты)")),
                ("is_image", models.BooleanField(default=False, verbose_name="Изображение")),
                ("uploaded_at", models.DateTimeField(default=django.utils.timezone.now, verbose_name="Дата загрузки")),
                ("message", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="chat.chatmessage", verbose_name="Сообщение")),
            ],
            options={
                "verbose_name": "Вложение",
                "verbose_name_plural": "Вложения",
            },
        ),
        migrations.AddIndex(
            model_name="chatmembership",
            index=models.Index(fields=["room", "user"], name="chat_membership_room_user_idx"),
        ),
        migrations.AddIndex(
            model_name="chatmessage",
            index=models.Index(fields=["room", "sent_at"], name="chat_message_room_sent_at_idx"),
        ),
        migrations.AddConstraint(
            model_name="chatmembership",
            constraint=models.UniqueConstraint(fields=("room", "user"), name="chat_membership_unique_room_user"),
        ),
        migrations.AddConstraint(
            model_name="chatroom",
            constraint=models.CheckConstraint(condition=models.Q(models.Q(("room_type", "direct"), ("direct_key__isnull", False)), models.Q(("room_type", "group")), _connector="OR"), name="chat_room_direct_key_required"),
        ),
        migrations.AddConstraint(
            model_name="chatroom",
            constraint=models.CheckConstraint(condition=models.Q(models.Q(("room_type", "group"), ("name__isnull", False)), models.Q(("room_type", "direct")), _connector="OR"), name="chat_room_group_name_required"),
        ),
    ]
