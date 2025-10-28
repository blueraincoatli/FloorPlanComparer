from __future__ import annotations

import json
import secrets
import sqlite3
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from app.models.jobs import JobDiffPayload, JobMetadata, JobStatusPayload, StoredFile

CHUNK_SIZE = 1024 * 1024


class JobService:
    """Service responsible for persisting job files and metadata."""

    def __init__(self, storage_root: Path):
        self._root = storage_root
        self._jobs_dir = self._root / "jobs"
        self._meta_dir = self._root / "meta"
        self._jobs_dir.mkdir(parents=True, exist_ok=True)
        self._meta_dir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._meta_dir / "jobs.db"
        self._initialize_database()
        self._migrate_legacy_metadata()

    async def create_job(self, original: UploadFile, revised: UploadFile) -> JobMetadata:
        """Persist uploaded files and create initial metadata."""

        job_id = self._generate_job_id()
        job_dir = self._jobs_dir / job_id
        original_dir = job_dir / "original"
        revised_dir = job_dir / "revised"
        original_dir.mkdir(parents=True, exist_ok=True)
        revised_dir.mkdir(parents=True, exist_ok=True)

        original_file = await self._save_upload(original_dir, original, kind="original")
        revised_file = await self._save_upload(revised_dir, revised, kind="revised")

        now = datetime.now(timezone.utc)
        metadata = JobMetadata(
            job_id=job_id,
            status="queued",
            progress=0.0,
            created_at=now,
            updated_at=now,
            original_files=[original_file],
            revised_files=[revised_file],
        )
        self._write_metadata(metadata)
        return metadata

    def load_job(self, job_id: str) -> JobMetadata:
        """Read job metadata from storage."""

        return self._read_metadata(job_id)

    def get_job_status(self, job_id: str) -> JobStatusPayload:
        """Convert metadata into the public status payload."""

        job = self.load_job(job_id)
        last_error: str | None = None
        for entry in reversed(job.logs):
            if entry.get("level") == "error" or entry.get("status") == "failed":
                last_error = entry.get("error") or entry.get("details") or entry.get("message")
                if last_error:
                    break
        return JobStatusPayload(
            job_id=job.job_id,
            status=job.status,
            progress=job.progress,
            reports=job.reports,
            logs=job.logs,
            last_error=last_error,
        )

    def list_jobs(self, *, limit: int = 20, offset: int = 0) -> tuple[int, list[JobMetadata]]:
        """Return jobs sorted by updated_at descending with pagination."""

        if limit <= 0:
            raise ValueError("limit must be positive")
        if offset < 0:
            raise ValueError("offset cannot be negative")

        with self._connect() as conn:
            total_row = conn.execute("SELECT COUNT(*) AS count FROM jobs").fetchone()
            total = int(total_row["count"]) if total_row else 0
            if total == 0:
                return 0, []

            cursor = conn.execute(
                """
                SELECT job_id, status, progress, created_at, updated_at,
                       original_files, revised_files, converted_files, reports, logs
                FROM jobs
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
            jobs = [self._row_to_metadata(row) for row in cursor.fetchall()]

        return total, jobs

    def get_job_diff(self, job_id: str) -> JobDiffPayload:
        """Load diff payload for a given job."""

        job = self.load_job(job_id)
        diff_file = next((report for report in job.reports if report.kind == "diff"), None)
        if diff_file is None:
            diff_file = next((report for report in job.reports if report.name.endswith("diff.json")), None)
        if diff_file is None:
            raise FileNotFoundError(f"diff report not found for job {job_id}")

        path = Path(diff_file.path)
        if not path.exists():
            raise FileNotFoundError(f"diff file missing for job {job_id}")
        return JobDiffPayload.model_validate_json(path.read_text(encoding="utf-8"))

    def get_report_file(self, job_id: str, kind: str) -> StoredFile:
        """Return a stored report file for the given kind."""

        job = self.load_job(job_id)
        normalized_kind = kind.lower().replace("-", "_")

        for report in job.reports:
            if report.kind and report.kind.lower() == normalized_kind:
                return report

        for report in job.reports:
            name = report.name.lower()
            if name == normalized_kind:
                return report
            if name.startswith(f"{normalized_kind}.") or name.endswith(f".{normalized_kind}"):
                return report

        raise FileNotFoundError(f"report '{kind}' not found for job {job_id}")

    def save_metadata(self, metadata: JobMetadata) -> JobMetadata:
        """Write metadata to disk and return the model."""

        self._write_metadata(metadata)
        return metadata

    def update_metadata(self, job_id: str, **updates) -> JobMetadata:
        """Update selected fields of the stored metadata."""

        job = self.load_job(job_id)
        new_job = job.model_copy(
            update={
                **updates,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        self._write_metadata(new_job)
        return new_job

    def _write_metadata(self, metadata: JobMetadata) -> None:
        payload = self._serialize_metadata(metadata)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO jobs (
                    job_id, status, progress, created_at, updated_at,
                    original_files, revised_files, converted_files, reports, logs
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                    status=excluded.status,
                    progress=excluded.progress,
                    created_at=excluded.created_at,
                    updated_at=excluded.updated_at,
                    original_files=excluded.original_files,
                    revised_files=excluded.revised_files,
                    converted_files=excluded.converted_files,
                    reports=excluded.reports,
                    logs=excluded.logs
                """,
                payload,
            )

    def _read_metadata(self, job_id: str) -> JobMetadata:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT job_id, status, progress, created_at, updated_at,
                       original_files, revised_files, converted_files, reports, logs
                FROM jobs
                WHERE job_id = ?
                """,
                (job_id,),
            ).fetchone()
        if row is None:
            raise FileNotFoundError(f"metadata not found for job {job_id}")
        return self._row_to_metadata(row)

    def _serialize_metadata(self, metadata: JobMetadata) -> tuple[Any, ...]:
        return (
            metadata.job_id,
            metadata.status,
            float(metadata.progress),
            metadata.created_at.isoformat(),
            metadata.updated_at.isoformat(),
            json.dumps([file.model_dump() for file in metadata.original_files], ensure_ascii=False),
            json.dumps([file.model_dump() for file in metadata.revised_files], ensure_ascii=False),
            json.dumps([file.model_dump() for file in metadata.converted_files], ensure_ascii=False),
            json.dumps([file.model_dump() for file in metadata.reports], ensure_ascii=False),
            json.dumps(metadata.logs, ensure_ascii=False),
        )

    def _row_to_metadata(self, row: sqlite3.Row) -> JobMetadata:
        def _parse_files(value: str) -> list[StoredFile]:
            data = json.loads(value)
            return [StoredFile.model_validate(item) for item in data]

        return JobMetadata(
            job_id=row["job_id"],
            status=row["status"],
            progress=float(row["progress"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            original_files=_parse_files(row["original_files"]),
            revised_files=_parse_files(row["revised_files"]),
            converted_files=_parse_files(row["converted_files"]),
            reports=_parse_files(row["reports"]),
            logs=json.loads(row["logs"] or "[]"),
        )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_database(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    progress REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    original_files TEXT NOT NULL,
                    revised_files TEXT NOT NULL,
                    converted_files TEXT NOT NULL,
                    reports TEXT NOT NULL,
                    logs TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_updated_at ON jobs(updated_at)")

    def _migrate_legacy_metadata(self) -> None:
        legacy_files = sorted(self._meta_dir.glob("*.json"))
        if not legacy_files:
            return
        for path in legacy_files:
            job_id = path.stem
            with self._connect() as conn:
                exists = conn.execute("SELECT 1 FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
            if exists:
                continue
            try:
                legacy_metadata = JobMetadata.model_validate_json(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            self._write_metadata(legacy_metadata)

    async def _save_upload(self, target_dir: Path, upload: UploadFile, *, kind: str | None = None) -> StoredFile:
        filename = self._safe_filename(upload.filename)
        target_path = target_dir / filename

        hasher = sha256()
        size = 0

        await upload.seek(0)
        with target_path.open("wb") as handle:
            while True:
                chunk = await upload.read(CHUNK_SIZE)
                if not chunk:
                    break
                handle.write(chunk)
                hasher.update(chunk)
                size += len(chunk)
        await upload.seek(0)

        return StoredFile(
            name=filename,
            path=str(target_path.resolve()),
            size=size,
            checksum=hasher.hexdigest(),
            content_type=upload.content_type,
            kind=kind,
        )

    @staticmethod
    def _safe_filename(filename: str | None) -> str:
        if not filename:
            return "uploaded.dwg"
        return Path(filename).name

    @staticmethod
    def _generate_job_id() -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        suffix = secrets.token_hex(4)
        return f"{timestamp}-{suffix}"
