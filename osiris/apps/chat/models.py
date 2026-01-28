"""Модели базовых сущностей чата."""
from __future__ import annotations

from typing import Iterable

from django.conf import settings
from django.db import models
from django.utils import timezone

from osiris.apps.rca.models import Org


class RoomType(models.TextChoices):
    DIRECT = "direct", "Личный"
    GROUP = "group", "Групповой"


def chat_upload_path(instance: "ChatAttachment", filename: str) -> str:
    date_path = timezone.now().strftime("%Y/%m/%d")
    room_id = instance.message.room_id or "unknown"
    return f"chat/{room_id}/{date_path}/{filename}"


class ChatRoom(models.Model):
    """Комната чата (личная или групповая)."""

    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чаты"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                name="chat_room_direct_key_required",
                condition=(
                    models.Q(room_type="direct", direct_key__isnull=False)
                    | models.Q(room_type="group")
                ),
            ),
            models.CheckConstraint(
                name="chat_room_group_name_required",
                condition=(
                    models.Q(room_type="group", name__isnull=False)
                    | models.Q(room_type="direct")
                ),
            ),
        ]

    room_type = models.CharField(
        verbose_name="Тип комнаты",
        max_length=16,
        choices=RoomType.choices,
        default=RoomType.GROUP,
    )
    name = models.CharField(
        verbose_name="Название",
        max_length=255,
        null=True,
        blank=True,
        help_text="Название для групповых комнат",
    )
    description = models.TextField(
        verbose_name="Описание",
        blank=True,
        help_text="Короткое описание чата",
    )
    org = models.ForeignKey(
        Org,
        verbose_name="Организационная единица",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="chat_rooms",
        help_text="Орг.единица, к которой относится чат",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Создатель",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_chat_rooms",
    )
    created_at = models.DateTimeField(
        verbose_name="Дата создания",
        default=timezone.now,
    )
    is_archived = models.BooleanField(
        verbose_name="Архивирован",
        default=False,
    )
    direct_key = models.CharField(
        verbose_name="Ключ личного чата",
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        help_text="Нормализованный ключ участников для личных комнат",
    )

    def __str__(self) -> str:
        if self.room_type == RoomType.DIRECT:
            return f"Личный чат {self.direct_key}"
        return self.name or "Групповой чат"

    @staticmethod
    def build_direct_key(user_ids: Iterable[int]) -> str:
        normalized = sorted(str(user_id) for user_id in user_ids)
        return ":".join(normalized)


class ChatMembership(models.Model):
    """Участие пользователя в комнате."""

    class Role(models.TextChoices):
        OWNER = "owner", "Владелец"
        ADMIN = "admin", "Администратор"
        MEMBER = "member", "Участник"

    class Meta:
        verbose_name = "Участник чата"
        verbose_name_plural = "Участники чата"
        constraints = [
            models.UniqueConstraint(
                fields=["room", "user"],
                name="chat_membership_unique_room_user",
            ),
        ]
        indexes = [
            models.Index(fields=["room", "user"], name="chat_membership_room_user_idx"),
        ]

    room = models.ForeignKey(
        ChatRoom,
        verbose_name="Комната",
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="chat_memberships",
    )
    role = models.CharField(
        verbose_name="Роль",
        max_length=16,
        choices=Role.choices,
        default=Role.MEMBER,
    )
    joined_at = models.DateTimeField(
        verbose_name="Дата вступления",
        default=timezone.now,
    )
    left_at = models.DateTimeField(
        verbose_name="Дата выхода",
        null=True,
        blank=True,
    )
    last_read_at = models.DateTimeField(
        verbose_name="Последнее прочтение",
        null=True,
        blank=True,
    )
    is_muted = models.BooleanField(
        verbose_name="Отключены уведомления",
        default=False,
    )

    def __str__(self) -> str:
        return f"{self.user} -> {self.room}"


class ChatMessage(models.Model):
    """Сообщение в комнате."""

    class BodyFormat(models.TextChoices):
        PLAIN = "plain", "Текст"
        MARKDOWN = "markdown", "Markdown"

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ["sent_at"]
        indexes = [
            models.Index(fields=["room", "sent_at"], name="chat_message_room_sent_at_idx"),
        ]

    room = models.ForeignKey(
        ChatRoom,
        verbose_name="Комната",
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Отправитель",
        on_delete=models.SET_NULL,
        null=True,
        related_name="chat_messages",
    )
    body = models.TextField(
        verbose_name="Текст сообщения",
        blank=True,
    )
    body_format = models.CharField(
        verbose_name="Формат текста",
        max_length=16,
        choices=BodyFormat.choices,
        default=BodyFormat.MARKDOWN,
    )
    metadata = models.JSONField(
        verbose_name="Метаданные",
        default=dict,
        blank=True,
    )
    sent_at = models.DateTimeField(
        verbose_name="Отправлено",
        default=timezone.now,
    )
    edited_at = models.DateTimeField(
        verbose_name="Отредактировано",
        null=True,
        blank=True,
    )
    is_deleted = models.BooleanField(
        verbose_name="Удалено",
        default=False,
    )
    reply_to = models.ForeignKey(
        "self",
        verbose_name="Ответ на сообщение",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="replies",
    )

    def __str__(self) -> str:
        return f"{self.room} @ {self.sent_at:%Y-%m-%d %H:%M}"


class ChatAttachment(models.Model):
    """Файл или изображение, прикрепленное к сообщению."""

    class Meta:
        verbose_name = "Вложение"
        verbose_name_plural = "Вложения"

    message = models.ForeignKey(
        ChatMessage,
        verbose_name="Сообщение",
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file = models.FileField(
        verbose_name="Файл",
        upload_to=chat_upload_path,
    )
    content_type = models.CharField(
        verbose_name="Тип содержимого",
        max_length=128,
        blank=True,
    )
    original_name = models.CharField(
        verbose_name="Исходное имя",
        max_length=255,
        blank=True,
    )
    size = models.PositiveIntegerField(
        verbose_name="Размер (байты)",
        default=0,
    )
    is_image = models.BooleanField(
        verbose_name="Изображение",
        default=False,
    )
    uploaded_at = models.DateTimeField(
        verbose_name="Дата загрузки",
        default=timezone.now,
    )

    def __str__(self) -> str:
        return self.original_name or self.file.name
