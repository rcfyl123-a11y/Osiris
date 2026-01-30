"""osiris.apps.polls.models — модели для корпоративных голосований."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


def validate_image_file(image):
    if not image:
        return
    max_size = 5 * 1024 * 1024
    if image.size > max_size:
        raise ValidationError("Размер изображения не должен превышать 5MB.")
    content_type = getattr(image.file, "content_type", None)
    allowed_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if content_type and content_type not in allowed_types:
        raise ValidationError("Разрешены только изображения JPEG/PNG/GIF/WebP.")


class Workplace(models.Model):
    ip_address = models.GenericIPAddressField(unique=True, verbose_name="IP-адрес")
    label = models.CharField(max_length=255, verbose_name="Метка", blank=True)
    department = models.CharField(max_length=255, blank=True, verbose_name="Подразделение")
    is_active = models.BooleanField(default=True, verbose_name="Активно")

    class Meta:
        verbose_name = "Рабочее место"
        verbose_name_plural = "Рабочие места"
        ordering = ["ip_address"]

    def __str__(self) -> str:
        return self.label or self.ip_address


class Poll(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        PUBLISHED = "published", "Опубликовано"
        CLOSED = "closed", "Закрыто"
        ARCHIVED = "archived", "Архив"

    class IdentityMode(models.TextChoices):
        ANON_IP = "anon_ip", "Анонимно (по IP)"
        NAME_REQUIRED = "name_required", "С ФИО (обязательно)"

    class VotePolicy(models.TextChoices):
        SINGLE = "single", "Один голос"
        REVOTE_UNTIL_END = "revote_until_end", "Переголосование до конца"

    title = models.CharField(max_length=255, verbose_name="Название")
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name="Описание")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    start_at = models.DateTimeField(null=True, blank=True, verbose_name="Начало")
    end_at = models.DateTimeField(null=True, blank=True, verbose_name="Окончание")
    identity_mode = models.CharField(
        max_length=30, choices=IdentityMode.choices, default=IdentityMode.ANON_IP
    )
    vote_policy = models.CharField(
        max_length=30, choices=VotePolicy.choices, default=VotePolicy.SINGLE
    )
    show_results_to_users = models.BooleanField(default=False, verbose_name="Показывать результаты")
    audience_all = models.BooleanField(default=True, verbose_name="Вся аудитория")
    audience_workplaces = models.ManyToManyField(
        Workplace, blank=True, related_name="polls", verbose_name="Аудитория"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Голосование"
        verbose_name_plural = "Голосования"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title

    def clean(self) -> None:
        super().clean()
        if self.start_at and self.end_at and self.end_at <= self.start_at:
            raise ValidationError({"end_at": "Дата окончания должна быть позже даты начала."})

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "poll"
            slug = base_slug
            counter = 1
            while Poll.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def is_published(self) -> bool:
        return self.status == self.Status.PUBLISHED

    @property
    def has_started(self) -> bool:
        if not self.start_at:
            return True
        return timezone.now() >= self.start_at

    @property
    def has_ended(self) -> bool:
        if not self.end_at:
            return False
        return timezone.now() >= self.end_at

    @property
    def is_active(self) -> bool:
        return self.is_published and self.has_started and not self.has_ended

    def audience_queryset(self) -> models.QuerySet[Workplace]:
        if self.audience_all:
            return Workplace.objects.filter(is_active=True)
        return self.audience_workplaces.filter(is_active=True)


class Question(models.Model):
    class QuestionType(models.TextChoices):
        SINGLE_CHOICE = "single", "Один вариант"
        MULTI_CHOICE = "multi", "Несколько вариантов"
        TEXT = "text", "Текст"
        SELECT = "select", "Выпадающий список"

    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="questions")
    text = models.CharField(max_length=500, verbose_name="Вопрос")
    help_text = models.CharField(max_length=500, blank=True, verbose_name="Подсказка")
    type = models.CharField(max_length=20, choices=QuestionType.choices)
    required = models.BooleanField(default=True, verbose_name="Обязательный")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    image = models.ImageField(
        upload_to="polls/questions/",
        blank=True,
        null=True,
        validators=[validate_image_file],
        verbose_name="Изображение",
    )
    video_url = models.URLField(blank=True, verbose_name="Видео ссылка")

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.text


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=255, verbose_name="Вариант")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        verbose_name = "Вариант"
        verbose_name_plural = "Варианты"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.text


class Vote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="votes")
    voter_ip = models.GenericIPAddressField(verbose_name="IP-адрес")
    workplace = models.ForeignKey(
        Workplace, on_delete=models.SET_NULL, null=True, blank=True, related_name="votes"
    )
    full_name = models.CharField(max_length=255, blank=True, verbose_name="ФИО")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Голос"
        verbose_name_plural = "Голоса"
        constraints = [
            models.UniqueConstraint(fields=["poll", "voter_ip"], name="polls_unique_vote")
        ]
        indexes = [models.Index(fields=["poll", "voter_ip"], name="polls_vote_ip_idx")]

    def __str__(self) -> str:
        return f"{self.poll} @ {self.voter_ip}"


class VoteAnswer(models.Model):
    vote = models.ForeignKey(Vote, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE, null=True, blank=True)
    answer_text = models.TextField(blank=True)

    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"
        indexes = [
            models.Index(fields=["question"], name="polls_answer_question_idx"),
            models.Index(fields=["choice"], name="polls_answer_choice_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.question}"
