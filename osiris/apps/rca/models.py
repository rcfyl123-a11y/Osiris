"""
Модели для системы учета штатного расписания (RCA).
SCD2 (Slowly Changing Dimensions Type 2) для истории изменений.
"""
from __future__ import annotations

from typing import Optional

from django.db import models
from django.utils import timezone


FIRE_SENTINEL = timezone.datetime(9999, 12, 31).date()


class ImportBatch(models.Model):
    """Факт импорта дневного комплекта (ORG/POST/EMPLOYEE) в Django."""

    class Meta:
        verbose_name = "Пакет импорта"
        verbose_name_plural = "Пакеты импорта"
        ordering = ["-set_date"]

    set_date = models.DateField(
        verbose_name="Дата набора данных",
        unique=True,
        db_index=True,
        help_text="Дата, за которую был выполнен импорт данных",
    )
    set_hash = models.CharField(
        verbose_name="Хеш набора",
        max_length=64,
        db_index=True,
        help_text="Контрольная сумма всего набора данных",
    )
    org_hash = models.CharField(
        verbose_name="Хеш организаций",
        max_length=64,
        null=True,
        blank=True,
        help_text="Хеш данных по организационным единицам",
    )
    post_hash = models.CharField(
        verbose_name="Хеш должностей",
        max_length=64,
        null=True,
        blank=True,
        help_text="Хеш данных по должностям",
    )
    employee_hash = models.CharField(
        verbose_name="Хеш сотрудников",
        max_length=64,
        null=True,
        blank=True,
        help_text="Хеш данных по сотрудникам",
    )
    imported_at = models.DateTimeField(
        verbose_name="Время импорта",
        default=timezone.now,
        help_text="Дата и время загрузки данных в систему",
    )
    source = models.CharField(
        verbose_name="Источник данных",
        max_length=50,
        default="duckdb",
        help_text="Система-источник данных (duckdb, 1C и т.д.)",
    )

    def __str__(self) -> str:
        return f"{self.set_date} {self.set_hash[:10]}..."


class Org(models.Model):
    """Орг.единица по коду (ORG.id). Базовая сущность."""

    class Meta:
        verbose_name = "Организационная единица"
        verbose_name_plural = "Организационные единицы"
        ordering = ["code"]

    code = models.CharField(
        verbose_name="Код орг.единицы",
        max_length=64,
        unique=True,
        help_text="Уникальный идентификатор организационной единицы",
    )
    created_at = models.DateTimeField(
        verbose_name="Дата создания",
        default=timezone.now,
        help_text="Дата и время создания записи",
    )

    def __str__(self) -> str:
        return self.code


class OrgVersion(models.Model):
    """SCD2 история орг.единицы."""

    class Meta:
        verbose_name = "Версия орг.единицы"
        verbose_name_plural = "Версии орг.единиц"
        ordering = ["org", "-valid_from"]
        indexes = [
            models.Index(fields=["org", "is_current"]),
            models.Index(fields=["org", "valid_from"]),
        ]

    org = models.ForeignKey(
        Org,
        verbose_name="Организационная единица",
        on_delete=models.PROTECT,
        related_name="versions",
        help_text="Ссылка на базовую орг.единицу",
    )
    name = models.CharField(
        verbose_name="Название",
        max_length=255,
        help_text="Краткое наименование организационной единицы",
    )
    full_name = models.CharField(
        verbose_name="Полное наименование",
        max_length=512,
        help_text="Полное официальное наименование",
    )
    parent_code = models.CharField(
        verbose_name="Код родительской орг.единицы",
        max_length=64,
        null=True,
        blank=True,
        help_text="Код орг.единицы, в которую входит данная",
    )
    is_top = models.BooleanField(
        verbose_name="Является вершиной",
        default=False,
        help_text="Флаг, указывающий что это верхнеуровневая орг.единица",
    )
    row_hash = models.CharField(
        verbose_name="Хеш строки данных",
        max_length=64,
        db_index=True,
        help_text="Контрольная сумма данных версии",
    )
    valid_from = models.DateField(
        verbose_name="Действует с",
        db_index=True,
        help_text="Дата начала действия данной версии",
    )
    valid_to = models.DateField(
        verbose_name="Действует до",
        null=True,
        blank=True,
        db_index=True,
        help_text="Дата окончания действия данной версии",
    )
    is_current = models.BooleanField(
        verbose_name="Текущая версия",
        default=True,
        db_index=True,
        help_text="Флаг актуальной (последней) версии",
    )

    def __str__(self) -> str:
        return f"{self.org.code} [{self.valid_from}..{self.valid_to or '∞'}]"


class Post(models.Model):
    """Должность по коду (POST.id)."""

    class Meta:
        verbose_name = "Должность"
        verbose_name_plural = "Должности"
        ordering = ["code"]

    code = models.CharField(
        verbose_name="Код должности",
        max_length=32,
        unique=True,
        help_text="Уникальный идентификатор должности",
    )
    created_at = models.DateTimeField(
        verbose_name="Дата создания",
        default=timezone.now,
        help_text="Дата и время создания записи",
    )

    def __str__(self) -> str:
        return self.code


class PostVersion(models.Model):
    """SCD2 история должности."""

    class Meta:
        verbose_name = "Версия должности"
        verbose_name_plural = "Версии должностей"
        ordering = ["post", "-valid_from"]
        indexes = [
            models.Index(fields=["post", "is_current"]),
        ]

    post = models.ForeignKey(
        Post,
        verbose_name="Должность",
        on_delete=models.PROTECT,
        related_name="versions",
        help_text="Ссылка на базовую должность",
    )
    name = models.CharField(
        verbose_name="Наименование должности",
        max_length=512,
        help_text="Полное наименование должности",
    )
    row_hash = models.CharField(
        verbose_name="Хеш строки данных",
        max_length=64,
        db_index=True,
        help_text="Контрольная сумма данных версии",
    )
    valid_from = models.DateField(
        verbose_name="Действует с",
        db_index=True,
        help_text="Дата начала действия данной версии",
    )
    valid_to = models.DateField(
        verbose_name="Действует до",
        null=True,
        blank=True,
        db_index=True,
        help_text="Дата окончания действия данной версии",
    )
    is_current = models.BooleanField(
        verbose_name="Текущая версия",
        default=True,
        db_index=True,
        help_text="Флаг актуальной (последней) версии",
    )

    def __str__(self) -> str:
        return f"{self.post.code} [{self.valid_from}..{self.valid_to or '∞'}]"


class Employee(models.Model):
    """
    Сотрудник как сущность. Ключ — СНИЛС (11 цифр).
    Хранит базовые/редкоизменяемые атрибуты.
    """

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ["snils_norm"]
        indexes = [
            models.Index(fields=["tab_norm_current"]),
            models.Index(fields=["is_fired_current"]),
        ]

    snils_norm = models.CharField(
        verbose_name="СНИЛС (нормализованный)",
        max_length=11,
        unique=True,
        help_text="СНИЛС в формате 11 цифр без разделителей",
    )
    snils_raw_last = models.CharField(
        verbose_name="СНИЛС (последний сырой)",
        max_length=32,
        null=True,
        blank=True,
        help_text="СНИЛС в исходном формате из последней выгрузки",
    )
    tab_norm_current = models.CharField(
        verbose_name="Табельный номер (текущий)",
        max_length=32,
        null=True,
        blank=True,
        db_index=True,
        help_text="Нормализованный табельный номер на текущий момент",
    )
    tab_raw_last = models.CharField(
        verbose_name="Табельный номер (последний сырой)",
        max_length=32,
        null=True,
        blank=True,
        help_text="Табельный номер в исходном формате из последней выгрузки",
    )

    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=128,
        help_text="Фамилия сотрудника",
    )
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=128,
        help_text="Имя сотрудника",
    )
    middle_name = models.CharField(
        verbose_name="Отчество",
        max_length=128,
        null=True,
        blank=True,
        help_text="Отчество сотрудника",
    )
    date_of_birth = models.DateField(
        verbose_name="Дата рождения",
        help_text="Дата рождения сотрудника",
    )
    gender = models.CharField(
        verbose_name="Пол",
        max_length=32,
        null=True,
        blank=True,
        help_text="Пол сотрудника",
    )

    is_fired_current = models.BooleanField(
        verbose_name="Уволен",
        default=False,
        db_index=True,
        help_text="Текущий статус увольнения сотрудника",
    )
    fired_date_current = models.DateField(
        verbose_name="Дата увольнения (текущая)",
        null=True,
        blank=True,
        help_text="Дата увольнения на текущий момент",
    )

    created_at = models.DateTimeField(
        verbose_name="Дата создания",
        default=timezone.now,
        help_text="Дата и время создания записи",
    )
    updated_at = models.DateTimeField(
        verbose_name="Дата обновления",
        auto_now=True,
        help_text="Дата и время последнего обновления записи",
    )

    def __str__(self) -> str:
        middle = f"{self.middle_name[0]}." if self.middle_name else ""
        return f"{self.last_name} {self.first_name[0]}.{middle} ({self.snils_norm})"

    @property
    def current_snapshot(self) -> Optional["EmployeeSnapshot"]:
        return (
            self.snapshots.filter(is_current=True)
            .select_related("org", "post")
            .first()
        )


class EmployeeSnapshot(models.Model):
    """SCD2 снапшот состояния сотрудника (частоизменяемые поля)."""

    class Meta:
        verbose_name = "Снимок состояния сотрудника"
        verbose_name_plural = "Снимки состояний сотрудников"
        ordering = ["employee", "-valid_from"]
        indexes = [
            models.Index(fields=["employee", "is_current"]),
            models.Index(fields=["org", "is_current"]),
            models.Index(fields=["post", "is_current"]),
            models.Index(fields=["valid_from"]),
            models.Index(fields=["valid_to"]),
            models.Index(fields=["is_current"]),
        ]

    employee = models.ForeignKey(
        Employee,
        verbose_name="Сотрудник",
        on_delete=models.PROTECT,
        related_name="snapshots",
        help_text="Ссылка на сотрудника",
    )
    batch = models.ForeignKey(
        ImportBatch,
        verbose_name="Пакет импорта",
        on_delete=models.PROTECT,
        related_name="employee_snapshots",
        help_text="Пакет данных, из которого создан снапшот",
    )

    snils_raw = models.CharField(
        verbose_name="СНИЛС (сырой)",
        max_length=32,
        null=True,
        blank=True,
        help_text="СНИЛС в исходном формате из выгрузки",
    )
    tab_raw = models.CharField(
        verbose_name="Табельный номер (сырой)",
        max_length=32,
        null=True,
        blank=True,
        help_text="Табельный номер в исходном формате из выгрузки",
    )

    org = models.ForeignKey(
        Org,
        verbose_name="Организационная единица",
        on_delete=models.PROTECT,
        related_name="employee_snapshots",
        help_text="Орг.единица, в которой работает сотрудник",
    )
    post = models.ForeignKey(
        Post,
        verbose_name="Должность",
        on_delete=models.PROTECT,
        related_name="employee_snapshots",
        help_text="Должность сотрудника",
    )
    state = models.CharField(
        verbose_name="Состояние",
        max_length=64,
        help_text="Рабочее состояние (активен, в отпуске и т.д.)",
    )
    feature = models.CharField(
        verbose_name="Особенность",
        max_length=128,
        help_text="Особые условия или характеристики",
    )
    start_date = models.DateField(
        verbose_name="Дата приёма",
        help_text="Дата приёма на работу",
    )
    fire_date = models.DateField(
        verbose_name="Дата увольнения",
        help_text="Дата увольнения или планируемого увольнения",
    )
    vacation_start = models.DateField(
        verbose_name="Начало отпуска",
        null=True,
        blank=True,
        help_text="Дата начала отпуска",
    )
    vacation_end = models.DateField(
        verbose_name="Окончание отпуска",
        null=True,
        blank=True,
        help_text="Дата окончания отпуска",
    )
    office_location = models.CharField(
        verbose_name="Место работы",
        max_length=512,
        null=True,
        blank=True,
        help_text="Физическое расположение рабочего места",
    )

    row_hash = models.CharField(
        verbose_name="Хеш строки данных",
        max_length=64,
        db_index=True,
        help_text="Контрольная сумма данных снапшота",
    )
    valid_from = models.DateField(
        verbose_name="Действует с",
        db_index=True,
        help_text="Дата начала действия данного снапшота",
    )
    valid_to = models.DateField(
        verbose_name="Действует до",
        null=True,
        blank=True,
        db_index=True,
        help_text="Дата окончания действия данного снапшота",
    )
    is_current = models.BooleanField(
        verbose_name="Текущий снапшот",
        default=True,
        db_index=True,
        help_text="Флаг актуального (последнего) снапшота",
    )

    def __str__(self) -> str:
        return f"{self.employee} @ {self.org} ({self.valid_from})"


class VacationPeriod(models.Model):
    """История отпусков отдельной таблицей."""

    class Meta:
        verbose_name = "Период отпуска"
        verbose_name_plural = "Периоды отпусков"
        ordering = ["employee", "-start"]
        indexes = [
            models.Index(fields=["employee", "start"]),
            models.Index(fields=["employee", "end"]),
        ]

    employee = models.ForeignKey(
        Employee,
        verbose_name="Сотрудник",
        on_delete=models.PROTECT,
        related_name="vacations",
        help_text="Сотрудник, которому принадлежит отпуск",
    )
    batch = models.ForeignKey(
        ImportBatch,
        verbose_name="Пакет импорта",
        on_delete=models.PROTECT,
        related_name="vacation_periods",
        help_text="Пакет данных, из которого создана запись",
    )
    source_snapshot = models.ForeignKey(
        EmployeeSnapshot,
        verbose_name="Исходный снапшот",
        on_delete=models.PROTECT,
        related_name="vacation_periods",
        help_text="Снапшот сотрудника, содержащий информацию об отпуске",
    )
    start = models.DateField(
        verbose_name="Начало отпуска",
        help_text="Дата начала периода отпуска",
    )
    end = models.DateField(
        verbose_name="Окончание отпуска",
        help_text="Дата окончания периода отпуска",
    )

    def __str__(self) -> str:
        return f"{self.employee} отпуск {self.start} - {self.end}"
