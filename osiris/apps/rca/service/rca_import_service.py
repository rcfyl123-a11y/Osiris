from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

import duckdb
from django.conf import settings
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from loguru import logger

from osiris.apps.rca.models import (
    Employee,
    EmployeeSnapshot,
    ImportBatch,
    Org,
    OrgVersion,
    Post,
    PostVersion,
    VacationPeriod,
)
from osiris.apps.rca.service.rca_file_service import RcaDuckDbService
from osiris.apps.rca.service.rca_norm import (
    is_fired,
    norm_snils,
    norm_tab_id,
    to_iso,
)
from osiris.apps.rca.service.rca_xml_parser import parse_employee, parse_org, parse_post


@dataclass(frozen=True)
class ImportStats:
    day: str
    created_batches: int
    org_versions_created: int
    post_versions_created: int
    employees_created: int
    employee_snapshots_created: int
    vacation_periods_created: int


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def row_hash_org(code: str, name: str, full_name: str, parent_code: str | None, is_top: bool) -> str:
    base = "|".join([code, name, full_name, parent_code or "", "1" if is_top else "0"])
    return sha256_hex(base)


def row_hash_post(code: str, name: str) -> str:
    return sha256_hex("|".join([code, name]))


def row_hash_employee(
    snils_norm: str,
    tab_norm: str,
    org_code: str,
    post_code: str,
    state: str,
    feature: str,
    start_date: date,
    fire_date: date,
    vacation_start: date | None,
    vacation_end: date | None,
    office_location: str | None,
) -> str:
    base = "|".join(
        [
            snils_norm,
            tab_norm,
            org_code,
            post_code,
            state,
            feature,
            start_date.isoformat(),
            fire_date.isoformat(),
            to_iso(vacation_start),
            to_iso(vacation_end),
            office_location or "",
        ]
    )
    return sha256_hex(base)


def created_at_from_set_date(set_date: date) -> datetime:
    created_at = datetime.combine(set_date, time.min)
    if settings.USE_TZ:
        return timezone.make_aware(created_at, timezone.get_current_timezone())
    return created_at


class RcaImportService:
    """Импортирует hashed-комплекты из DuckDB в Django."""

    def __init__(self) -> None:
        self.duck = RcaDuckDbService.from_django_settings()

    def _open_duckdb(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(str(settings.RCA_DUCKDB_PATH))

    def list_hashed_sets(self, *, limit: int = 10, order: str = "newest") -> list[tuple]:
        order_sql = "DESC" if order == "newest" else "ASC"
        db = self._open_duckdb()
        rows = db.execute(
            f"""
            SELECT set_id, set_date, set_date_str, set_hash, org_hash, post_hash, employee_hash,
                   org_file_id, post_file_id, employee_main_file_id
            FROM daily_file_sets
            WHERE processing_status = 'hashed'
              AND is_complete = TRUE
            ORDER BY set_date {order_sql}
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        db.close()
        return rows

    def _duck_file_path(self, db: duckdb.DuckDBPyConnection, file_id: int) -> str:
        row = db.execute("SELECT file_path FROM scanned_files WHERE file_id = ?", (file_id,)).fetchone()
        if not row:
            raise RuntimeError(f"Не найден file_id={file_id} в scanned_files")
        return row[0]

    def _mark_duck_processed(self, set_id: int) -> None:
        db = self._open_duckdb()
        db.execute(
            """
            UPDATE daily_file_sets
            SET processing_status='processed',
                error_message=NULL
            WHERE set_id=?
            """,
            (set_id,),
        )
        db.close()

    def _mark_duck_error(self, set_id: int, msg: str) -> None:
        db = self._open_duckdb()
        db.execute(
            """
            UPDATE daily_file_sets
            SET processing_status='error',
                error_message=?
            WHERE set_id=?
            """,
            (msg, set_id),
        )
        db.close()

    @transaction.atomic
    def import_one_set(
        self,
        *,
        set_id: int,
        set_date: date,
        set_date_str: str,
        set_hash: str,
        org_hash: str,
        post_hash: str,
        employee_hash: str,
        org_file_id: int,
        post_file_id: int,
        emp_file_id: int,
    ) -> ImportStats:
        max_date = ImportBatch.objects.aggregate(m=Max("set_date"))["m"]
        if max_date and set_date < max_date:
            raise RuntimeError(
                f"Импорт вне хронологии: пытаемся импортировать {set_date}, "
                f"но уже импортированы дни до {max_date}. Используй --order oldest или сбрось данные."
            )

        existing = ImportBatch.objects.filter(set_date=set_date).first()
        if existing:
            if existing.set_hash == set_hash:
                logger.info("[{}] Уже импортировано (set_hash совпадает).", set_date_str)
                return ImportStats(
                    day=set_date_str,
                    created_batches=0,
                    org_versions_created=0,
                    post_versions_created=0,
                    employees_created=0,
                    employee_snapshots_created=0,
                    vacation_periods_created=0,
                )
            existing.set_hash = set_hash
            existing.org_hash = org_hash
            existing.post_hash = post_hash
            existing.employee_hash = employee_hash
            existing.save(update_fields=["set_hash", "org_hash", "post_hash", "employee_hash", "imported_at"])
            batch = existing
            created_batches = 0
        else:
            batch = ImportBatch.objects.create(
                set_date=set_date,
                set_hash=set_hash,
                org_hash=org_hash,
                post_hash=post_hash,
                employee_hash=employee_hash,
                source="duckdb",
            )
            created_batches = 1

        duck_db = self._open_duckdb()
        org_path = self._duck_file_path(duck_db, org_file_id)
        post_path = self._duck_file_path(duck_db, post_file_id)
        emp_path = self._duck_file_path(duck_db, emp_file_id)
        duck_db.close()

        org_versions_created = 0
        created_at = created_at_from_set_date(set_date)
        org_rows = list(parse_org(org_path))
        org_codes = {row.code for row in org_rows}
        orgs_by_code = Org.objects.in_bulk(org_codes, field_name="code")
        missing_org_codes = org_codes - orgs_by_code.keys()
        if missing_org_codes:
            Org.objects.bulk_create(
                [Org(code=code, created_at=created_at) for code in missing_org_codes],
                ignore_conflicts=True,
            )
            orgs_by_code = Org.objects.in_bulk(org_codes, field_name="code")
        org_current_versions = {
            version.org_id: version
            for version in OrgVersion.objects.filter(
                org_id__in=[org.id for org in orgs_by_code.values()],
                is_current=True,
            )
        }
        for row in org_rows:
            org = orgs_by_code[row.code]
            row_hash = row_hash_org(row.code, row.name, row.full_name, row.parent_code, row.is_top)

            current = org_current_versions.get(org.id)
            if current and current.row_hash == row_hash:
                continue

            if current:
                current.is_current = False
                current.valid_to = set_date - timedelta(days=1)
                current.save(update_fields=["is_current", "valid_to"])

            current = OrgVersion.objects.create(
                org=org,
                name=row.name,
                full_name=row.full_name,
                parent_code=row.parent_code,
                is_top=row.is_top,
                row_hash=row_hash,
                valid_from=set_date,
                valid_to=None,
                is_current=True,
            )
            org_current_versions[org.id] = current
            org_versions_created += 1

        post_versions_created = 0
        post_rows = list(parse_post(post_path))
        post_codes = {row.code for row in post_rows}
        posts_by_code = Post.objects.in_bulk(post_codes, field_name="code")
        missing_post_codes = post_codes - posts_by_code.keys()
        if missing_post_codes:
            Post.objects.bulk_create(
                [Post(code=code, created_at=created_at) for code in missing_post_codes],
                ignore_conflicts=True,
            )
            posts_by_code = Post.objects.in_bulk(post_codes, field_name="code")
        post_current_versions = {
            version.post_id: version
            for version in PostVersion.objects.filter(
                post_id__in=[post.id for post in posts_by_code.values()],
                is_current=True,
            )
        }
        for row in post_rows:
            post = posts_by_code[row.code]
            row_hash = row_hash_post(row.code, row.name)
            current = post_current_versions.get(post.id)
            if current and current.row_hash == row_hash:
                continue
            if current:
                current.is_current = False
                current.valid_to = set_date - timedelta(days=1)
                current.save(update_fields=["is_current", "valid_to"])
            current = PostVersion.objects.create(
                post=post,
                name=row.name,
                row_hash=row_hash,
                valid_from=set_date,
                valid_to=None,
                is_current=True,
            )
            post_current_versions[post.id] = current
            post_versions_created += 1

        employees_created = 0
        employee_snapshots_created = 0
        vacation_periods_created = 0

        org_cache: dict[str, Org] = dict(orgs_by_code)
        post_cache: dict[str, Post] = dict(posts_by_code)

        def get_org(code: str) -> Org:
            if code in org_cache:
                return org_cache[code]
            org, _ = Org.objects.get_or_create(code=code, defaults={"created_at": created_at})
            org_cache[code] = org
            return org

        def get_post(code: str) -> Post:
            if code in post_cache:
                return post_cache[code]
            post, _ = Post.objects.get_or_create(code=code, defaults={"created_at": created_at})
            post_cache[code] = post
            return post

        for row in parse_employee(emp_path):
            snils_raw, snils_norm = norm_snils(row.snils_raw)
            tab_raw, tab_norm = norm_tab_id(row.tab_raw)
            if not snils_norm:
                logger.warning(
                    "[{}] Пропуск сотрудника: SNILS не 11 цифр: raw={!r}", set_date_str, row.snils_raw
                )
                continue
            if not tab_norm:
                logger.warning(
                    "[{}] Пропуск сотрудника: пустой tab_id: raw={!r}", set_date_str, row.tab_raw
                )
                continue

            employee, created = Employee.objects.get_or_create(
                snils_norm=snils_norm,
                defaults={
                    "snils_raw_last": snils_raw,
                    "tab_norm_current": tab_norm,
                    "tab_raw_last": tab_raw,
                    "last_name": row.last_name,
                    "first_name": row.first_name,
                    "middle_name": row.middle_name,
                    "date_of_birth": row.date_of_birth,
                    "gender": row.gender,
                },
            )
            if created:
                employees_created += 1
            else:
                update_fields = []
                if snils_raw and employee.snils_raw_last != snils_raw:
                    employee.snils_raw_last = snils_raw
                    update_fields.append("snils_raw_last")
                if tab_norm and employee.tab_norm_current != tab_norm:
                    employee.tab_norm_current = tab_norm
                    update_fields.append("tab_norm_current")
                if tab_raw and employee.tab_raw_last != tab_raw:
                    employee.tab_raw_last = tab_raw
                    update_fields.append("tab_raw_last")
                if employee.last_name != row.last_name:
                    employee.last_name = row.last_name
                    update_fields.append("last_name")
                if employee.first_name != row.first_name:
                    employee.first_name = row.first_name
                    update_fields.append("first_name")
                if employee.middle_name != row.middle_name:
                    employee.middle_name = row.middle_name
                    update_fields.append("middle_name")
                if employee.date_of_birth != row.date_of_birth:
                    employee.date_of_birth = row.date_of_birth
                    update_fields.append("date_of_birth")
                if employee.gender != row.gender:
                    employee.gender = row.gender
                    update_fields.append("gender")
                if update_fields:
                    employee.save(update_fields=update_fields)

            org = get_org(row.org_code)
            post = get_post(row.post_code)

            row_hash = row_hash_employee(
                snils_norm=snils_norm,
                tab_norm=tab_norm,
                org_code=row.org_code,
                post_code=row.post_code,
                state=row.state,
                feature=row.feature,
                start_date=row.start_date,
                fire_date=row.fire_date,
                vacation_start=row.vacation_start,
                vacation_end=row.vacation_end,
                office_location=row.office_location,
            )

            current = EmployeeSnapshot.objects.filter(employee=employee, is_current=True).first()
            if current and current.row_hash == row_hash:
                fired = is_fired(row.fire_date)
                if employee.is_fired_current != fired or employee.fired_date_current != (
                    row.fire_date if fired else None
                ):
                    employee.is_fired_current = fired
                    employee.fired_date_current = row.fire_date if fired else None
                    employee.save(update_fields=["is_fired_current", "fired_date_current"])
                continue

            if current:
                current.is_current = False
                current.valid_to = set_date - timedelta(days=1)
                current.save(update_fields=["is_current", "valid_to"])

            snap = EmployeeSnapshot.objects.create(
                employee=employee,
                batch=batch,
                snils_raw=snils_raw,
                tab_raw=tab_raw,
                org=org,
                post=post,
                state=row.state,
                feature=row.feature,
                start_date=row.start_date,
                fire_date=row.fire_date,
                vacation_start=row.vacation_start,
                vacation_end=row.vacation_end,
                office_location=row.office_location,
                row_hash=row_hash,
                valid_from=set_date,
                valid_to=None,
                is_current=True,
            )
            employee_snapshots_created += 1

            fired = is_fired(row.fire_date)
            employee.is_fired_current = fired
            employee.fired_date_current = row.fire_date if fired else None
            employee.save(update_fields=["is_fired_current", "fired_date_current"])

            if row.vacation_start and row.vacation_end:
                exists = VacationPeriod.objects.filter(
                    employee=employee,
                    start=row.vacation_start,
                    end=row.vacation_end,
                ).exists()
                if not exists:
                    VacationPeriod.objects.create(
                        employee=employee,
                        batch=batch,
                        source_snapshot=snap,
                        start=row.vacation_start,
                        end=row.vacation_end,
                    )
                    vacation_periods_created += 1

        return ImportStats(
            day=set_date_str,
            created_batches=created_batches,
            org_versions_created=org_versions_created,
            post_versions_created=post_versions_created,
            employees_created=employees_created,
            employee_snapshots_created=employee_snapshots_created,
            vacation_periods_created=vacation_periods_created,
        )

    def import_hashed(
        self, *, limit: int = 10, order: str = "newest", mark_processed: bool = True
    ) -> list[ImportStats]:
        rows = self.list_hashed_sets(limit=limit, order=order)
        if not rows:
            return []

        results: list[ImportStats] = []
        for (
            set_id,
            set_date,
            set_date_str,
            set_hash,
            org_hash,
            post_hash,
            emp_hash,
            org_file_id,
            post_file_id,
            emp_file_id,
        ) in rows:
            try:
                stats = self.import_one_set(
                    set_id=int(set_id),
                    set_date=set_date,
                    set_date_str=str(set_date_str),
                    set_hash=str(set_hash),
                    org_hash=str(org_hash),
                    post_hash=str(post_hash),
                    employee_hash=str(emp_hash),
                    org_file_id=int(org_file_id),
                    post_file_id=int(post_file_id),
                    emp_file_id=int(emp_file_id),
                )
                results.append(stats)
                logger.info(
                    "[{}] imported: batch+{}, org_versions+{}, post_versions+{}, employees+{}, emp_snaps+{}, "
                    "vacations+{}",
                    stats.day,
                    stats.created_batches,
                    stats.org_versions_created,
                    stats.post_versions_created,
                    stats.employees_created,
                    stats.employee_snapshots_created,
                    stats.vacation_periods_created,
                )
                if mark_processed:
                    self._mark_duck_processed(int(set_id))
            except Exception as exc:
                logger.exception("[{}] Ошибка импорта: {}", set_date_str, exc)
                self._mark_duck_error(int(set_id), f"django import error: {exc}")
        return results
