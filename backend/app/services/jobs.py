from __future__ import annotations

import secrets
from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from fastapi import UploadFile
from filelock import FileLock

from app.models.jobs import JobMetadata, JobStatusPayload, StoredFile

CHUNK_SIZE = 1024 * 1024


class JobService:
    """Service responsible for persisting job files and metadata."""

    def __init__(self, storage_root: Path):
        self._root = storage_root
        self._jobs_dir = self._root / "jobs"
        self._meta_dir = self._root / "meta"
        self._jobs_dir.mkdir(parents=True, exist_ok=True)
        self._meta_dir.mkdir(parents=True, exist_ok=True)

    async def create_job(self, original: UploadFile, revised: UploadFile) -> JobMetadata:
        """Persist uploaded files and create initial metadata."""

        job_id = self._generate_job_id()
        job_dir = self._jobs_dir / job_id
        original_dir = job_dir / "original"
        revised_dir = job_dir / "revised"
        original_dir.mkdir(parents=True, exist_ok=True)
        revised_dir.mkdir(parents=True, exist_ok=True)

        original_file = await self._save_upload(original_dir, original)
        revised_file = await self._save_upload(revised_dir, revised)

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

        meta_path = self._meta_path(job_id)
        if not meta_path.exists():
            raise FileNotFoundError(f"metadata not found for job {job_id}")
        with self._metadata_lock(job_id):
            return self._read_metadata(meta_path)

    def get_job_status(self, job_id: str) -> JobStatusPayload:
        """Convert metadata into the public status payload."""

        job = self.load_job(job_id)
        return JobStatusPayload(
            job_id=job.job_id,
            status=job.status,
            progress=job.progress,
            reports=job.reports,
        )

    def list_jobs(self, *, limit: int = 20, offset: int = 0) -> tuple[int, list[JobMetadata]]:
        """Return jobs sorted by updated_at descending with pagination."""

        if limit <= 0:
            raise ValueError("limit must be positive")
        if offset < 0:
            raise ValueError("offset cannot be negative")

        meta_paths = [path for path in self._meta_dir.glob("*.json") if path.is_file()]
        if not meta_paths:
            return 0, []

        jobs: list[JobMetadata] = []
        for path in meta_paths:
            job_id = path.stem
            with self._metadata_lock(job_id):
                jobs.append(self._read_metadata(path))

        jobs.sort(key=lambda job: job.updated_at, reverse=True)
        total = len(jobs)
        start = min(offset, total)
        end = min(start + limit, total)
        return total, jobs[start:end]

    def save_metadata(self, metadata: JobMetadata) -> JobMetadata:
        """Write metadata to disk and return the model."""

        self._write_metadata(metadata)
        return metadata

    def update_metadata(self, job_id: str, **updates) -> JobMetadata:
        """Update selected fields of the stored metadata."""

        meta_path = self._meta_path(job_id)
        if not meta_path.exists():
            raise FileNotFoundError(f"metadata not found for job {job_id}")
        with self._metadata_lock(job_id):
            job = self._read_metadata(meta_path)
            new_job = job.model_copy(
                update={
                    **updates,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            self._write_metadata_unlocked(meta_path, new_job)
            return new_job

    def _write_metadata(self, metadata: JobMetadata) -> None:
        meta_path = self._meta_path(metadata.job_id)
        with self._metadata_lock(metadata.job_id):
            self._write_metadata_unlocked(meta_path, metadata)

    def _read_metadata(self, meta_path: Path) -> JobMetadata:
        return JobMetadata.model_validate_json(meta_path.read_text(encoding="utf-8"))

    def _write_metadata_unlocked(self, meta_path: Path, metadata: JobMetadata) -> None:
        temp_path = meta_path.with_suffix(meta_path.suffix + ".tmp")
        temp_path.write_text(
            metadata.model_dump_json(indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        temp_path.replace(meta_path)

    @contextmanager
    def _metadata_lock(self, job_id: str):
        lock_path = self._meta_dir / f"{job_id}.lock"
        lock = FileLock(str(lock_path))
        with lock:
            yield

    async def _save_upload(self, target_dir: Path, upload: UploadFile) -> StoredFile:
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
        )

    def _meta_path(self, job_id: str) -> Path:
        return self._meta_dir / f"{job_id}.json"

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
