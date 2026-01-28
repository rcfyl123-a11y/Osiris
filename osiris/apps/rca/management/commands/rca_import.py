from __future__ import annotations

from django.core.management.base import BaseCommand
from loguru import logger

from osiris.apps.rca.service.rca_import_service import RcaImportService


class Command(BaseCommand):
    # rca_import --until-empty
    help = "Import hashed RCA sets from DuckDB into Django models (ORG/POST/EMPLOYEE + history)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="How many hashed days to import (ignored with --until-empty)",
        )
        parser.add_argument(
            "--batch-size", type=int, default=200, help="Batch size for --until-empty loop"
        )
        parser.add_argument("--order", type=str, default="oldest", choices=["newest", "oldest"])
        parser.add_argument(
            "--until-empty",
            action="store_true",
            help="Keep importing until no hashed sets remain",
        )
        parser.add_argument(
            "--no-mark-processed", action="store_true", help="Do not mark DuckDB set as processed"
        )

    def handle(self, *args, **opts):
        svc = RcaImportService()

        order = str(opts["order"])
        if order != "oldest":
            self.stdout.write(
                self.style.WARNING(
                    "Внимание: для корректной истории (SCD2) рекомендуется импортировать "
                    "от старых к новым: --order oldest"
                )
            )

        mark_processed = not bool(opts["no_mark_processed"])

        if opts["until_empty"]:
            batch_size = int(opts["batch_size"])
            total_days = 0
            while True:
                stats = svc.import_hashed(
                    limit=batch_size, order=order, mark_processed=mark_processed
                )
                if not stats:
                    break
                total_days += len(stats)
                self.stdout.write(
                    self.style.SUCCESS(f"Imported batch: {len(stats)} days (total={total_days})")
                )
            self.stdout.write(self.style.SUCCESS(f"Done. Imported total days: {total_days}"))
            return

        limit = int(opts["limit"])
        logger.info(
            "Import hashed sets: limit={}, order={}, mark_processed={}",
            limit,
            order,
            mark_processed,
        )
        stats = svc.import_hashed(limit=limit, order=order, mark_processed=mark_processed)

        if not stats:
            self.stdout.write(self.style.WARNING("No hashed sets to import."))
            return

        total_batches = sum(s.created_batches for s in stats)
        total_org = sum(s.org_versions_created for s in stats)
        total_post = sum(s.post_versions_created for s in stats)
        total_employees = sum(s.employees_created for s in stats)
        total_snaps = sum(s.employee_snapshots_created for s in stats)
        total_vac = sum(s.vacation_periods_created for s in stats)

        self.stdout.write(
            self.style.SUCCESS(
                "Imported days: %s | batches+%s | org_versions+%s | post_versions+%s | "
                "employees+%s | employee_snaps+%s | vacations+%s"
                % (
                    len(stats),
                    total_batches,
                    total_org,
                    total_post,
                    total_employees,
                    total_snaps,
                    total_vac,
                )
            )
        )
