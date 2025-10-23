from __future__ import annotations

import json
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.settings import get_settings
from app.main import app


@pytest.fixture
def storage_root(tmp_path, monkeypatch):
    root = tmp_path / "storage"
    monkeypatch.setenv("FLOORPLAN_STORAGE_DIR", str(root))
    monkeypatch.setenv("FLOORPLAN_CELERY_TASK_ALWAYS_EAGER", "true")
    get_settings.cache_clear()
    yield root
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_create_job_persists_files_and_metadata(storage_root):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/jobs",
            files={
                "original_dwg": ("original.dwg", b"original-bytes", "application/dwg"),
                "revised_dwg": ("revised.dwg", b"revised-bytes", "application/dwg"),
            },
        )

    assert response.status_code == 202
    payload = response.json()
    job_id = payload["data"]["job_id"]
    assert payload["data"]["status"] == "queued"

    meta_path = storage_root / "meta" / f"{job_id}.json"
    assert meta_path.exists()

    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    assert metadata["status"] == "completed"
    assert metadata["progress"] == 1.0
    assert metadata["original_files"][0]["name"] == "original.dwg"
    assert metadata["logs"]
    assert metadata["logs"][0]["step"] == "enqueue"
    steps = {entry["step"] for entry in metadata["logs"]}
    assert {"convert", "extract", "match"}.issubset(steps)
    assert metadata["reports"], "expected at least one generated report"
    report_path = Path(metadata["reports"][0]["path"])
    assert report_path.exists()

    stored_path = Path(metadata["original_files"][0]["path"])
    assert stored_path.exists()
    assert stored_path.read_bytes() == b"original-bytes"


@pytest.mark.asyncio
async def test_get_job_status_returns_envelope(storage_root):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/api/jobs",
            files={
                "original_dwg": ("plan_a.dwg", b"a", "application/dwg"),
                "revised_dwg": ("plan_b.dwg", b"b", "application/dwg"),
            },
        )
        job_id = create_resp.json()["data"]["job_id"]

        status_resp = await client.get(f"/api/jobs/{job_id}")
        missing_resp = await client.get("/api/jobs/unknown-job")

    assert status_resp.status_code == 200
    status_payload = status_resp.json()
    assert status_payload["data"]["job_id"] == job_id
    assert status_payload["data"]["status"] == "completed"
    assert status_payload["data"]["progress"] == 1.0

    assert missing_resp.status_code == 404


@pytest.mark.asyncio
async def test_list_jobs_returns_paginated_data(storage_root):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        created_ids: list[str] = []
        for suffix in ("a", "b", "c"):
            resp = await client.post(
                "/api/jobs",
                files={
                    "original_dwg": (f"orig_{suffix}.dwg", f"orig-{suffix}".encode(), "application/dwg"),
                    "revised_dwg": (f"rev_{suffix}.dwg", f"rev-{suffix}".encode(), "application/dwg"),
                },
            )
            assert resp.status_code == 202
            created_ids.append(resp.json()["data"]["job_id"])

        list_resp = await client.get("/api/jobs", params={"limit": 2, "offset": 0})
        assert list_resp.status_code == 200
        payload = list_resp.json()["data"]
        assert payload["total"] >= len(created_ids)
        assert payload["limit"] == 2
        assert payload["offset"] == 0
        returned_ids = [item["job_id"] for item in payload["jobs"]]
        assert len(returned_ids) == 2

        # request next page
        next_resp = await client.get("/api/jobs", params={"limit": 2, "offset": 2})
        assert next_resp.status_code == 200
        next_payload = next_resp.json()["data"]
        assert next_payload["offset"] == 2
        assert next_payload["limit"] == 2
        # all created IDs should appear across both pages
        paged_ids = set(returned_ids + [item["job_id"] for item in next_payload["jobs"]])
        for job_id in created_ids:
            assert job_id in paged_ids


@pytest.mark.asyncio
async def test_get_job_diff_returns_payload(storage_root):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/jobs",
            files={
                "original_dwg": ("example_a.dwg", b"foo", "application/dwg"),
                "revised_dwg": ("example_b.dwg", b"bar", "application/dwg"),
            },
        )
        job_id = resp.json()["data"]["job_id"]

        diff_resp = await client.get(f"/api/jobs/{job_id}/diff")

    assert diff_resp.status_code == 200
    diff_payload = diff_resp.json()["data"]
    assert diff_payload["job_id"] == job_id
    assert diff_payload["summary"]["added"] >= 0
    assert len(diff_payload["entities"]) > 0
    first_entity = diff_payload["entities"][0]
    assert "polygon" in first_entity
