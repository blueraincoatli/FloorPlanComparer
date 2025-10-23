from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class StoredFile(BaseModel):
    """Information about a persisted file."""

    name: str = Field(description="Original filename without path")
    path: str = Field(description="Absolute path to the file on disk")
    size: int = Field(ge=0, description="File size in bytes")
    checksum: str = Field(description="SHA256 checksum")
    content_type: str | None = Field(default=None, description="Optional MIME type")
    kind: str | None = Field(default=None, description="Logical category of the file (e.g. original, diff)")


class JobMetadata(BaseModel):
    """Metadata describing a comparison job."""

    job_id: str = Field(description="Unique job identifier")
    status: Literal["queued", "processing", "completed", "failed"] = Field(description="Current job status")
    progress: float = Field(ge=0.0, le=1.0, default=0.0, description="Job progress between 0 and 1")
    created_at: datetime = Field(description="UTC timestamp when the job was created")
    updated_at: datetime = Field(description="UTC timestamp of the latest update")
    original_files: list[StoredFile] = Field(default_factory=list, description="Uploaded original files")
    revised_files: list[StoredFile] = Field(default_factory=list, description="Uploaded revised files")
    converted_files: list[StoredFile] = Field(default_factory=list, description="Converted DXF files")
    reports: list[StoredFile] = Field(default_factory=list, description="Generated artefact files")
    logs: list[dict[str, Any]] = Field(default_factory=list, description="Processing log entries")


class JobCreatedPayload(BaseModel):
    """Response payload returned after creating a job."""

    job_id: str = Field(description="Unique job identifier")
    status: Literal["queued"] = Field(description="Initial job status")


class JobStatusPayload(BaseModel):
    """Response payload returned when querying job status."""

    job_id: str = Field(description="Unique job identifier")
    status: Literal["queued", "processing", "completed", "failed"] = Field(description="Current job status")
    progress: float = Field(ge=0.0, le=1.0, description="Job progress between 0 and 1")
    reports: list[StoredFile] = Field(default_factory=list, description="Downloadable report files")


class JobSummary(BaseModel):
    """Summary information for job listings."""

    job_id: str = Field(description="Unique job identifier")
    status: Literal["queued", "processing", "completed", "failed"] = Field(description="Current job status")
    progress: float = Field(ge=0.0, le=1.0, description="Job progress between 0 and 1")
    created_at: datetime = Field(description="Job creation timestamp (UTC)")
    updated_at: datetime = Field(description="Last update timestamp (UTC)")


class JobListPayload(BaseModel):
    """Payload returned when listing jobs."""

    total: int = Field(ge=0, description="Total number of jobs available")
    limit: int = Field(ge=1, description="Requested page size")
    offset: int = Field(ge=0, description="Requested offset")
    jobs: list[JobSummary] = Field(default_factory=list, description="Jobs sorted by last update time")


class DiffPolygon(BaseModel):
    """Polygon geometry representing a diff entity."""

    points: list[tuple[float, float]] = Field(description="Ordered list of (x, y) vertices")


class DiffEntity(BaseModel):
    """Single geometry entity difference."""

    entity_id: str = Field(description="Unique identifier for the entity")
    entity_type: str = Field(description="Entity category, e.g. wall, door")
    change_type: Literal["added", "removed", "modified"] = Field(description="Type of change detected")
    label: str | None = Field(default=None, description="Friendly label for the entity")
    polygon: DiffPolygon = Field(description="Polygon describing the entity footprint")


class DiffSummary(BaseModel):
    """Aggregated diff statistics."""

    added: int = Field(ge=0, description="Number of added entities")
    removed: int = Field(ge=0, description="Number of removed entities")
    modified: int = Field(ge=0, description="Number of modified entities")


class JobDiffPayload(BaseModel):
    """Full diff payload for a job."""

    job_id: str = Field(description="Job identifier")
    summary: DiffSummary = Field(description="Summary statistics")
    entities: list[DiffEntity] = Field(default_factory=list, description="List of entity-level differences")
