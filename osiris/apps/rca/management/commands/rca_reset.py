from __future__ import annotations

import duckdb
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
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


class Command(BaseCommand):
    help = (
        "DANGEROUS: wipe RCA Django tables (snapshots/versions/batches/employee/org/post). "
        "Optionally reset DuckDB statuses back to 'hashed' for re-import."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Required. Without it the command will refuse to run.",
        )
        parser.add_argument(
            "--duck-reset",
            choices=["no", "hashed", "discovered"],
            default="hashed",
            help=(
                "Reset DuckDB daily_file_sets statuses after wipe. "
                "hashed = processed->hashed (if set_hash exists), "
                "discovered = processed->discovered (forces re-hash), "
                "no = do nothing."
            ),
        )

    @transaction.atomic
    def _wipe_django(self) -> dict[str, int]:
        """
        Delete in strict order to satisfy PROTECT FKs:
        VacationPeriod -> EmployeeSnapshot -> (Org/Post versions) -> ImportBatch -> Employee -> Org/Post
        """
        counts: dict[str, int] = {}

        counts["VacationPeriod"] = VacationPeriod.objects.count()
        VacationPeriod.objects.all().delete()

        counts["EmployeeSnapshot"] = EmployeeSnapshot.objects.count()
        EmployeeSnapshot.objects.all().delete()

        counts["OrgVersion"] = OrgVersion.objects.count()
        OrgVersion.objects.all().delete()

        counts["PostVersion"] = PostVersion.objects.count()
        PostVersion.objects.all().delete()

        counts["ImportBatch"] = ImportBatch.objects.count()
        ImportBatch.objects.all().delete()

        counts["Employee"] = Employee.objects.count()
        Employee.objects.all().delete()

        counts["Org"] = Org.objects.count()
        Org.objects.all().delete()

        counts["Post"] = Post.objects.count()
        Post.objects.all().delete()

        return counts

    def _reset_duckdb(self, mode: str) -> int:
        if mode == "no":
            return 0

        db_path = getattr(settings, "RCA_DUCKDB_PATH", None)
        if not db_path:
            raise RuntimeError("settings.RCA_DUCKDB_PATH is not set")

        db = duckdb.connect(str(db_path))
        try:
            if mode == "hashed":
                db.execute(
                    """
                    UPDATE daily_file_sets
                    SET
                        processing_status = CASE
                            WHEN is_complete = TRUE AND set_hash IS NOT NULL THEN 'hashed'
                            ELSE 'discovered'
                        END,
                        error_message = NULL
                    WHERE processing_status = 'processed'
                    """
                ).fetchone()
            elif mode == "discovered":
                db.execute(
                    """
                    UPDATE daily_file_sets
                    SET processing_status = 'discovered',
                        set_hash = NULL,
                        org_hash = NULL,
                        post_hash = NULL,
                        employee_hash = NULL,
                        processed_timestamp = NULL,
                        error_message = NULL
                    WHERE processing_status = 'processed'
                    """
                ).fetchone()
            else:
                return 0

            rowcount = db.execute(
                """
                SELECT COUNT(*) FROM daily_file_sets
                WHERE processing_status IN ('hashed','discovered') AND is_complete = TRUE
                """
            ).fetchone()[0]
            return int(rowcount)
        finally:
            db.close()

    def handle(self, *args, **opts):
        if not opts["yes"]:
            self.stderr.write(
                self.style.ERROR("Refusing to run. This command deletes RCA data. Re-run with --yes")
            )
            return

        duck_mode = opts["duck_reset"]

        self.stdout.write(self.style.WARNING("WIPING RCA Django tables..."))
        with transaction.atomic():
            counts = self._wipe_django()

        for key, value in counts.items():
            self.stdout.write(f"Deleted {key}: {value}")

        if duck_mode != "no":
            self.stdout.write(self.style.WARNING(f"Resetting DuckDB statuses: {duck_mode}"))
            count = self._reset_duckdb(duck_mode)
            self.stdout.write(
                self.style.SUCCESS(f"DuckDB reset done. Complete sets now pending import-ish: {count}")
            )

        self.stdout.write(self.style.SUCCESS("RCA reset finished."))
