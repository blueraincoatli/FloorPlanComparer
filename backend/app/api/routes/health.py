from fastapi import APIRouter

from app.models.responses import Envelope, HealthData

router = APIRouter()


@router.get("", response_model=Envelope[HealthData], summary="Health check")
async def health_check() -> Envelope[HealthData]:
    """Return the API health status."""

    return Envelope(data=HealthData(status="ok"))
