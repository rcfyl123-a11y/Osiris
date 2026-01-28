from __future__ import annotations

from django.core.management.base import BaseCommand
from loguru import logger

from osiris.apps.rca.service.rca_file_service import RcaDuckDbService


class Command(BaseCommand):
    help = "Scan RCA XML folder -> update DuckDB registry -> hash pending sets."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0, help="0 = hash all pending sets")
        parser.add_argument("--order", type=str, default="newest", choices=["newest", "oldest"])
        parser.add_argument("--no-hash", action="store_true", help="Only scan+group, do not hash")

    def handle(self, *args, **opts):
        svc = RcaDuckDbService.from_django_settings()

        logger.info("RCA_XML_DIR={}", svc.xml_dir)
        logger.info("RCA_DUCKDB_PATH={}", svc.db_path)

        stats = svc.scan_and_group()
        self.stdout.write(
            self.style.SUCCESS(
                "Scanned: files=%s, days=%s, complete=%s, pending_complete=%s, error=%s"
                % (
                    stats.total_files,
                    stats.days,
                    stats.complete_sets,
                    stats.pending_complete,
                    stats.error_sets,
                )
            )
        )

        if opts["no_hash"]:
            return

        done = svc.hash_pending_sets(limit=opts["limit"], order=opts["order"])
        self.stdout.write(self.style.SUCCESS(f"Hashed sets: {done}"))
