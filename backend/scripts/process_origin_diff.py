from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from starlette.datastructures import Headers

from app.core.settings import get_settings
from app.models import JobDiffPayload
from app.services import JobService
from app.tasks.jobs import convert_job_task, extract_job_task, match_job_task


async def _create_job(service: JobService, original_path: Path, revised_path: Path) -> str:
    def _load_upload(path: Path) -> UploadFile:
        buffer = BytesIO(path.read_bytes())
        buffer.seek(0)
        return UploadFile(filename=path.name, file=buffer, headers=Headers({"content-type": "application/dwg"}))

    original_upload = _load_upload(original_path)
    revised_upload = _load_upload(revised_path)
    metadata = await service.create_job(original_upload, revised_upload)
    return metadata.job_id


async def main() -> None:
    settings = get_settings()
    project_root = Path(__file__).resolve().parents[2]
    origin_dir = project_root / "originFile"
    dwg_files = sorted(origin_dir.glob("*.dwg"))
    if len(dwg_files) < 2:
        raise RuntimeError(f"Expected at least 2 DWG files in {origin_dir}, found {len(dwg_files)}")

    original_path, revised_path = dwg_files[:2]

    service = JobService(Path(settings.storage_dir))
    job_id = await _create_job(service, original_path, revised_path)

    payload = convert_job_task.run(job_id)
    payload = extract_job_task.run(payload)
    payload = match_job_task.run(payload)

    job = service.load_job(job_id)
    diff_file = next((report for report in job.reports if report.kind == "diff"), None)
    if diff_file is None:
        raise RuntimeError(f"Diff report not generated for job {job_id}")

    diff_path = Path(diff_file.path)
    diff_payload = JobDiffPayload.model_validate_json(diff_path.read_text(encoding="utf-8"))

    print("job_id:", job_id)
    print("diff_path:", diff_path)
    print("summary:", diff_payload.summary.model_dump())


if __name__ == "__main__":
    asyncio.run(main())
