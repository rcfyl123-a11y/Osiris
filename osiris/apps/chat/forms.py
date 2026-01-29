"""Формы для приложения чатов."""
from __future__ import annotations

from dataclasses import dataclass
import mimetypes
from pathlib import Path

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import ChatMessage


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultiFileField(forms.FileField):
    def clean(self, data, initial=None):
        if data in (None, "", []):
            return []
        if not isinstance(data, (list, tuple)):
            data = [data]
        return [super().clean(item, initial) for item in data]


@dataclass(frozen=True)
class AttachmentPolicy:
    max_size: int
    allowed_types: tuple[str, ...]
    forbidden_extensions: tuple[str, ...]

    @classmethod
    def from_settings(cls) -> "AttachmentPolicy":
        return cls(
            max_size=settings.CHAT_ATTACHMENT_MAX_SIZE,
            allowed_types=tuple(settings.CHAT_ALLOWED_CONTENT_TYPES),
            forbidden_extensions=tuple(settings.CHAT_FORBIDDEN_EXTENSIONS),
        )


class ChatMessageForm(forms.Form):
    body = forms.CharField(
        label="Сообщение",
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Введите сообщение...",
                "class": "form-control",
            }
        ),
        required=False,
    )
    reply_to = forms.IntegerField(widget=forms.HiddenInput, required=False)
    attachments = MultiFileField(
        label="Вложения",
        required=False,
        widget=MultiFileInput(attrs={"multiple": True, "class": "form-control"}),
    )

    def __init__(self, *args, policy: AttachmentPolicy | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.policy = policy or AttachmentPolicy.from_settings()

    def clean(self) -> dict:
        cleaned = super().clean()
        body = (cleaned.get("body") or "").strip()
        files = cleaned.get("attachments") or []
        if not body and not files:
            raise ValidationError("Нужно добавить текст или вложение.")
        return cleaned

    def clean_attachments(self):
        files = self.cleaned_data.get("attachments") or []
        for file in files:
            self._validate_file(file)
        return files

    def _validate_file(self, file) -> None:
        if file.size > self.policy.max_size:
            raise ValidationError("Превышен максимальный размер файла.")

        extension = Path(file.name).suffix.lower()
        if extension in self.policy.forbidden_extensions:
            raise ValidationError("Запрещенный тип файла.")

        content_type = getattr(file, "content_type", "") or ""
        guessed_type, _ = mimetypes.guess_type(file.name)
        if not content_type or content_type == "application/octet-stream":
            content_type = guessed_type or content_type

        if self.policy.allowed_types and content_type not in self.policy.allowed_types:
            if guessed_type and guessed_type in self.policy.allowed_types:
                return
            raise ValidationError("Тип файла не поддерживается.")


class ChatMessageEditForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 3, "class": "form-control"})}

    def clean_body(self):
        body = (self.cleaned_data.get("body") or "").strip()
        if not body:
            raise ValidationError("Сообщение не может быть пустым.")
        return body

    def save(self, commit=True):
        message = super().save(commit=False)
        message.edited_at = timezone.now()
        if commit:
            message.save(update_fields=["body", "edited_at"])
        return message


class ChatMemberAddForm(forms.Form):
    user_id = forms.IntegerField(
        label="ID пользователя",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    def clean_user_id(self):
        user_id = self.cleaned_data["user_id"]
        user_model = get_user_model()
        if not user_model.objects.filter(pk=user_id).exists():
            raise ValidationError("Пользователь не найден.")
        return user_id


class DirectChatForm(forms.Form):
    user_id = forms.IntegerField(
        label="ID пользователя",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, current_user=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.current_user = current_user

    def clean_user_id(self):
        user_id = self.cleaned_data["user_id"]
        user_model = get_user_model()
        if not user_model.objects.filter(pk=user_id).exists():
            raise ValidationError("Пользователь не найден.")
        if self.current_user and self.current_user.pk == user_id:
            raise ValidationError("Нельзя создать чат с самим собой.")
        return user_id
