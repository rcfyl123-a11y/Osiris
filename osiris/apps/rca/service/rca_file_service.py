from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import duckdb
from django.conf import settings
from loguru import logger


FILE_RE = re.compile(
    r"^000_(\d{8})_?(org|post|employee)(?:_(\d{2}\.\d{2}\.\d{4}_\d{2}-\d{2}-\d{2}))?\.xml$",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class ScanResult:
    total_files: int
    days: int
    complete_sets: int
    incomplete_sets: int
    pending_complete: int
    hashed_sets: int
    error_sets: int


class RcaDuckDbService:
    def __init__(self, *, db_path: Path, xml_dir: Path):
        self.db_path = Path(db_path)
        self.xml_dir = Path(xml_dir)

        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_django_settings(cls) -> "RcaDuckDbService":
        return cls(
            db_path=Path(settings.RCA_DUCKDB_PATH),
            xml_dir=Path(settings.RCA_XML_DIR),
        )

    def open_db(self) -> duckdb.DuckDBPyConnection:
        db = duckdb.connect(str(self.db_path))

        db.execute("CREATE SEQUENCE IF NOT EXISTS seq_scanned_files START 1")
        db.execute("CREATE SEQUENCE IF NOT EXISTS seq_daily_file_sets START 1")

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS scanned_files (
                file_id BIGINT PRIMARY KEY,
                file_path VARCHAR NOT NULL,
                file_name VARCHAR NOT NULL,
                file_date DATE NOT NULL,
                file_date_str VARCHAR(8) NOT NULL,
                file_type VARCHAR(10) NOT NULL,

                is_correction BOOLEAN DEFAULT FALSE,
                correction_time TIMESTAMP,

                file_size BIGINT NOT NULL,
                file_mtime TIMESTAMP NOT NULL,
                file_hash VARCHAR(64),

                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_scanned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,

                UNIQUE(file_path)
            )
            """
        )

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_file_sets (
                set_id BIGINT PRIMARY KEY,
                set_date DATE NOT NULL,
                set_date_str VARCHAR(8) NOT NULL,

                org_file_id BIGINT REFERENCES scanned_files(file_id),
                post_file_id BIGINT REFERENCES scanned_files(file_id),
                employee_main_file_id BIGINT REFERENCES scanned_files(file_id),

                set_hash VARCHAR(64),
                org_hash VARCHAR(64),
                post_hash VARCHAR(64),
                employee_hash VARCHAR(64),

                total_files_count INTEGER DEFAULT 0,
                employee_files_count INTEGER DEFAULT 0,
                org_files_count INTEGER DEFAULT 0,
                post_files_count INTEGER DEFAULT 0,

                has_correction BOOLEAN DEFAULT FALSE,
                is_complete BOOLEAN DEFAULT FALSE,

                scan_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processing_status VARCHAR(20) DEFAULT 'discovered',
                processed_timestamp TIMESTAMP,
                error_message VARCHAR,

                UNIQUE(set_date_str)
            )
            """
        )

        db.execute("CREATE INDEX IF NOT EXISTS idx_files_date_type ON scanned_files(file_date, file_type)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_sets_date ON daily_file_sets(set_date)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_sets_status ON daily_file_sets(processing_status)")

        return db

    def extract_file_info(self, filename: str) -> Optional[Tuple[str, str, bool, Optional[datetime]]]:
        match = FILE_RE.match(filename)
        if not match:
            return None
        date_str = match.group(1)
        file_type = match.group(2).lower()
        time_str = match.group(3)

        is_correction = time_str is not None
        correction_time = None
        if time_str:
            try:
                correction_time = datetime.strptime(time_str, "%d.%m.%Y_%H-%M-%S")
            except ValueError:
                logger.warning("Некорректный correction timestamp: {} -> {}", filename, time_str)

        return date_str, file_type, is_correction, correction_time

    @staticmethod
    def _sql_id_changed(old_col: str, new_col: str) -> str:
        return (
            f"(({old_col} IS NULL AND {new_col} IS NOT NULL) "
            f"OR ({old_col} IS NOT NULL AND {new_col} IS NULL) "
            f"OR ({old_col} <> {new_col}))"
        )

    def rebuild_daily_sets(self, db: duckdb.DuckDBPyConnection) -> None:
        db.execute("DROP TABLE IF EXISTS tmp_sets")
        db.execute(
            """
            CREATE TEMP TABLE tmp_sets AS
            WITH ranked AS (
                SELECT
                    file_date_str,
                    file_date,
                    file_type,
                    file_id,
                    is_correction,
                    correction_time,
                    file_mtime,
                    ROW_NUMBER() OVER (
                        PARTITION BY file_date_str, file_type
                        ORDER BY
                            is_correction DESC,
                            correction_time DESC NULLS LAST,
                            file_mtime DESC
                    ) AS rn
                FROM scanned_files
                WHERE is_active = TRUE
            ),
            mains AS (
                SELECT file_date_str, file_date, file_type, file_id
                FROM ranked
                WHERE rn = 1
            ),
            counts AS (
                SELECT
                    file_date_str,
                    MAX(file_date) AS set_date,
                    COUNT(*) AS total_files_count,
                    SUM(CASE WHEN file_type = 'employee' THEN 1 ELSE 0 END) AS employee_files_count,
                    SUM(CASE WHEN file_type = 'org' THEN 1 ELSE 0 END) AS org_files_count,
                    SUM(CASE WHEN file_type = 'post' THEN 1 ELSE 0 END) AS post_files_count,
                    MAX(CASE WHEN is_correction THEN 1 ELSE 0 END) AS has_correction_int
                FROM scanned_files
                WHERE is_active = TRUE
                GROUP BY file_date_str
            ),
            pivot_mains AS (
                SELECT
                    file_date_str,
                    MAX(CASE WHEN file_type='org' THEN file_id END) AS org_file_id,
                    MAX(CASE WHEN file_type='post' THEN file_id END) AS post_file_id,
                    MAX(CASE WHEN file_type='employee' THEN file_id END) AS employee_main_file_id
                FROM mains
                GROUP BY file_date_str
            )
            SELECT
                c.set_date AS set_date,
                c.file_date_str AS set_date_str,
                p.org_file_id,
                p.post_file_id,
                p.employee_main_file_id,
                c.total_files_count,
                c.employee_files_count,
                c.org_files_count,
                c.post_files_count,
                (c.has_correction_int = 1) AS has_correction,
                (p.org_file_id IS NOT NULL AND p.post_file_id IS NOT NULL AND p.employee_main_file_id IS NOT NULL) AS is_complete,
                CASE
                    WHEN (p.org_file_id IS NULL OR p.post_file_id IS NULL OR p.employee_main_file_id IS NULL)
                        THEN ('Неполный комплект: org=' || CAST(p.org_file_id IS NOT NULL AS VARCHAR)
                        || ', post=' || CAST(p.post_file_id IS NOT NULL AS VARCHAR)
                        || ', employee=' || CAST(p.employee_main_file_id IS NOT NULL AS VARCHAR))
                    ELSE NULL
                END AS incomplete_message
            FROM counts c
            LEFT JOIN pivot_mains p USING(file_date_str)
            """
        )

        db.execute(
            """
            INSERT INTO daily_file_sets (
                set_id, set_date, set_date_str,
                org_file_id, post_file_id, employee_main_file_id,
                total_files_count, employee_files_count, org_files_count, post_files_count,
                has_correction, is_complete,
                processing_status, error_message, scan_timestamp
            )
            SELECT
                nextval('seq_daily_file_sets'),
                t.set_date, t.set_date_str,
                t.org_file_id, t.post_file_id, t.employee_main_file_id,
                t.total_files_count, t.employee_files_count, t.org_files_count, t.post_files_count,
                t.has_correction, t.is_complete,
                CASE WHEN t.is_complete THEN 'discovered' ELSE 'error' END,
                CASE WHEN t.is_complete THEN NULL ELSE t.incomplete_message END,
                CURRENT_TIMESTAMP
            FROM tmp_sets t
            LEFT JOIN daily_file_sets s ON s.set_date_str = t.set_date_str
            WHERE s.set_id IS NULL
            """
        )

        changed_expr = " OR ".join(
            [
                self._sql_id_changed("s.org_file_id", "t.org_file_id"),
                self._sql_id_changed("s.post_file_id", "t.post_file_id"),
                self._sql_id_changed("s.employee_main_file_id", "t.employee_main_file_id"),
            ]
        )

        db.execute(
            f"""
            UPDATE daily_file_sets s
            SET
                set_date = t.set_date,
                org_file_id = t.org_file_id,
                post_file_id = t.post_file_id,
                employee_main_file_id = t.employee_main_file_id,

                total_files_count = t.total_files_count,
                employee_files_count = t.employee_files_count,
                org_files_count = t.org_files_count,
                post_files_count = t.post_files_count,

                has_correction = t.has_correction,
                is_complete = t.is_complete,
                scan_timestamp = CURRENT_TIMESTAMP,

                org_hash = CASE WHEN ({changed_expr}) OR (NOT t.is_complete) THEN NULL ELSE s.org_hash END,
                post_hash = CASE WHEN ({changed_expr}) OR (NOT t.is_complete) THEN NULL ELSE s.post_hash END,
                employee_hash = CASE WHEN ({changed_expr}) OR (NOT t.is_complete) THEN NULL ELSE s.employee_hash END,
                set_hash = CASE WHEN ({changed_expr}) OR (NOT t.is_complete) THEN NULL ELSE s.set_hash END,
                processed_timestamp = CASE WHEN ({changed_expr}) OR (NOT t.is_complete) THEN NULL ELSE s.processed_timestamp END,

                processing_status = CASE
                    WHEN NOT t.is_complete THEN 'error'
                    WHEN ({changed_expr}) THEN 'discovered'
                    WHEN s.processing_status = 'error' AND t.is_complete THEN 'discovered'
                    ELSE s.processing_status
                END,

                error_message = CASE
                    WHEN NOT t.is_complete THEN t.incomplete_message
                    WHEN ({changed_expr}) THEN NULL
                    WHEN s.processing_status = 'error' AND t.is_complete THEN NULL
                    ELSE s.error_message
                END
            FROM tmp_sets t
            WHERE s.set_date_str = t.set_date_str
            """
        )

    def scan_and_group(self) -> ScanResult:
        db = self.open_db()

        xml_files = list(self.xml_dir.glob("*.xml"))
        logger.info("Найдено {} XML файлов в {}", len(xml_files), self.xml_dir)

        seen_paths: list[str] = []

        db.execute("BEGIN TRANSACTION")
        try:
            for file_path in xml_files:
                info = self.extract_file_info(file_path.name)
                if not info:
                    continue

                date_str, file_type, is_correction, correction_time = info
                file_date = datetime.strptime(date_str, "%Y%m%d").date()

                stats = file_path.stat()
                file_size = stats.st_size
                file_mtime = datetime.fromtimestamp(stats.st_mtime)
                normalized_path = str(file_path.resolve())
                seen_paths.append(normalized_path)

                existing = db.execute(
                    """
                    SELECT file_id, file_size, file_mtime
                    FROM scanned_files
                    WHERE file_path = ?
                    """,
                    (normalized_path,),
                ).fetchone()

                if existing:
                    file_id, old_size, old_mtime = existing
                    if old_size != file_size or old_mtime != file_mtime:
                        db.execute(
                            """
                            UPDATE scanned_files
                            SET file_name = ?, file_date = ?, file_date_str = ?, file_type = ?,
                                is_correction = ?, correction_time = ?,
                                file_size = ?, file_mtime = ?,
                                file_hash = NULL
                            WHERE file_id = ?
                            """,
                            (
                                file_path.name,
                                file_date,
                                date_str,
                                file_type,
                                is_correction,
                                correction_time,
                                file_size,
                                file_mtime,
                                file_id,
                            ),
                        )
                else:
                    db.execute(
                        """
                        INSERT INTO scanned_files
                        (file_id, file_path, file_name, file_date, file_date_str, file_type,
                         is_correction, correction_time, file_size, file_mtime)
                        VALUES (nextval('seq_scanned_files'), ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            normalized_path,
                            file_path.name,
                            file_date,
                            date_str,
                            file_type,
                            is_correction,
                            correction_time,
                            file_size,
                            file_mtime,
                        ),
                    )

            db.execute("DROP TABLE IF EXISTS tmp_seen_paths")
            db.execute("CREATE TEMP TABLE tmp_seen_paths(file_path VARCHAR)")
            if seen_paths:
                db.executemany("INSERT INTO tmp_seen_paths VALUES (?)", [(p,) for p in seen_paths])
                db.execute(
                    """
                    UPDATE scanned_files sf
                    SET is_active = TRUE, last_scanned = CURRENT_TIMESTAMP
                    WHERE sf.file_path IN (SELECT file_path FROM tmp_seen_paths)
                    """
                )
                db.execute(
                    """
                    UPDATE scanned_files sf
                    SET is_active = FALSE, last_scanned = CURRENT_TIMESTAMP
                    WHERE sf.is_active = TRUE
                      AND sf.file_path NOT IN (SELECT file_path FROM tmp_seen_paths)
                    """
                )

            self.rebuild_daily_sets(db)
            db.execute("COMMIT")
        except Exception:
            db.execute("ROLLBACK")
            db.close()
            raise

        files_stats = db.execute(
            """
            SELECT
                COUNT(*) AS total_files,
                COUNT(DISTINCT file_date) AS total_days
            FROM scanned_files
            WHERE is_active = TRUE
            """
        ).fetchone()

        sets_stats = db.execute(
            """
            SELECT
                COUNT(*) AS total_sets,
                SUM(CASE WHEN is_complete THEN 1 ELSE 0 END) AS complete_sets,
                SUM(CASE WHEN NOT is_complete THEN 1 ELSE 0 END) AS incomplete_sets,
                SUM(CASE WHEN processing_status='discovered' AND is_complete THEN 1 ELSE 0 END) AS pending_complete,
                SUM(CASE WHEN processing_status='hashed' THEN 1 ELSE 0 END) AS hashed_sets,
                SUM(CASE WHEN processing_status='error' THEN 1 ELSE 0 END) AS error_sets
            FROM daily_file_sets
            """
        ).fetchone()

        db.close()
        return ScanResult(
            total_files=int(files_stats[0]),
            days=int(files_stats[1]),
            complete_sets=int(sets_stats[1]),
            incomplete_sets=int(sets_stats[2]),
            pending_complete=int(sets_stats[3]),
            hashed_sets=int(sets_stats[4]),
            error_sets=int(sets_stats[5]),
        )

    @staticmethod
    def calculate_file_hash(file_path: str) -> Optional[str]:
        sha = hashlib.sha256()
        try:
            with open(file_path, "rb") as file_obj:
                for block in iter(lambda: file_obj.read(4096), b""):
                    sha.update(block)
            return sha.hexdigest()
        except Exception as exc:
            logger.error("Ошибка хэширования {}: {}", file_path, exc)
            return None

    def _get_or_compute_hash(self, db: duckdb.DuckDBPyConnection, file_id: int) -> Optional[str]:
        row = db.execute(
            """
            SELECT file_path, file_hash
            FROM scanned_files
            WHERE file_id = ?
            """,
            (file_id,),
        ).fetchone()
        if not row:
            return None
        file_path, file_hash = row
        if file_hash:
            return file_hash
        file_hash = self.calculate_file_hash(file_path)
        if not file_hash:
            return None
        db.execute("UPDATE scanned_files SET file_hash=? WHERE file_id=?", (file_hash, file_id))
        return file_hash

    def hash_pending_sets(self, *, limit: int = 0, order: str = "newest") -> int:
        order_sql = "DESC" if order == "newest" else "ASC"

        db = self.open_db()

        limit_clause = "" if limit == 0 else "LIMIT ?"
        params = () if limit == 0 else (limit,)

        rows = db.execute(
            f"""
            SELECT set_id, set_date_str, org_file_id, post_file_id, employee_main_file_id
            FROM daily_file_sets
            WHERE is_complete = TRUE
              AND processing_status IN ('discovered','error')
            ORDER BY set_date {order_sql}
            {limit_clause}
            """,
            params,
        ).fetchall()

        if not rows:
            db.close()
            return 0

        done = 0
        for set_id, date_str, org_id, post_id, emp_id in rows:
            org_hash = self._get_or_compute_hash(db, int(org_id))
            post_hash = self._get_or_compute_hash(db, int(post_id))
            emp_hash = self._get_or_compute_hash(db, int(emp_id))

            if not all([org_hash, post_hash, emp_hash]):
                db.execute(
                    """
                    UPDATE daily_file_sets
                    SET processing_status='error',
                        error_message='Ошибка вычисления хэшей файлов',
                        processed_timestamp=NULL,
                        set_hash=NULL, org_hash=NULL, post_hash=NULL, employee_hash=NULL
                    WHERE set_id=?
                    """,
                    (set_id,),
                )
                continue

            set_hash = hashlib.sha256(f"{org_hash}:{post_hash}:{emp_hash}".encode()).hexdigest()

            db.execute(
                """
                UPDATE daily_file_sets
                SET org_hash=?, post_hash=?, employee_hash=?,
                    set_hash=?, processing_status='hashed',
                    processed_timestamp=CURRENT_TIMESTAMP,
                    error_message=NULL
                WHERE set_id=?
                """,
                (org_hash, post_hash, emp_hash, set_hash, set_id),
            )
            done += 1

        db.close()
        return done

    def auto_sync(self, *, hash_limit: int = 0, hash_order: str = "newest") -> ScanResult:
        stats = self.scan_and_group()
        hashed = self.hash_pending_sets(limit=hash_limit, order=hash_order)
        logger.info(
            "SCAN: files={}, days={}, complete={}, pending_complete={}, hashed_now={}",
            stats.total_files,
            stats.days,
            stats.complete_sets,
            stats.pending_complete,
            hashed,
        )
        return stats
