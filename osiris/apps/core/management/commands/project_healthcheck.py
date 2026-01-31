import platform
import time

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django import get_version as get_django_version

from osiris.apps.chat.models import ChatRoom
from osiris.apps.core.models import SecurityEvent
from osiris.apps.polls.models import Poll
from osiris.apps.rca.models import Org


class Command(BaseCommand):
    help = "Run baseline project health checks (schema and ORM timings)."

    def handle(self, *args, **options):
        self.stdout.write("Project healthcheck")
        self.stdout.write(
            f"Runtime: Python {platform.python_version()} | Django {get_django_version()}"
        )
        self.stdout.write(f"DEBUG: {settings.DEBUG}")
        self.stdout.write(f"Database vendor: {connection.vendor}")

        existing_tables = set(connection.introspection.table_names())
        required_apps = ["core", "polls", "chat", "rca"]
        missing_tables = {}
        for app_label in required_apps:
            app_config = apps.get_app_config(app_label)
            for model in app_config.get_models():
                table_name = model._meta.db_table
                if table_name not in existing_tables:
                    missing_tables.setdefault(app_label, []).append(table_name)

        if missing_tables:
            self.stdout.write(self.style.ERROR("Missing tables detected:"))
            for app_label, tables in missing_tables.items():
                missing_list = ", ".join(sorted(tables))
                self.stdout.write(self.style.ERROR(f"- {app_label}: {missing_list}"))
        else:
            self.stdout.write(self.style.SUCCESS("All core app tables present."))

        self.stdout.write("\nORM timings:")

        def run_query(label, query):
            start = time.perf_counter()
            result = query()
            elapsed = (time.perf_counter() - start) * 1000
            self.stdout.write(f"- {label}: {elapsed:.2f} ms")
            return result

        if "core" not in missing_tables:
            try:
                run_query(
                    "core.SecurityEvent latest",
                    lambda: SecurityEvent.objects.order_by("-created_at").first(),
                )
            except Exception as exc:  # pragma: no cover - safety for runtime database issues
                self.stdout.write(self.style.WARNING(f"core query failed: {exc}"))

        if "polls" not in missing_tables:
            try:
                run_query(
                    "polls.Poll published count",
                    lambda: Poll.objects.filter(status=Poll.Status.PUBLISHED).count(),
                )
            except Exception as exc:  # pragma: no cover - safety for runtime database issues
                self.stdout.write(self.style.WARNING(f"polls query failed: {exc}"))

        if "chat" not in missing_tables:
            try:
                run_query(
                    "chat.ChatRoom active count",
                    lambda: ChatRoom.objects.filter(is_archived=False).count(),
                )
            except Exception as exc:  # pragma: no cover - safety for runtime database issues
                self.stdout.write(self.style.WARNING(f"chat query failed: {exc}"))

        if "rca" not in missing_tables:
            try:
                run_query(
                    "rca.Org total",
                    lambda: Org.objects.count(),
                )
            except Exception as exc:  # pragma: no cover - safety for runtime database issues
                self.stdout.write(self.style.WARNING(f"rca query failed: {exc}"))
