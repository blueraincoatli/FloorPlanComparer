from fastapi import APIRouter

from app.models.responses import Envelope, HealthData

router = APIRouter()


@router.get("", response_model=Envelope[HealthData], summary="健康检查")
async def health_check() -> Envelope[HealthData]:
    """返回服务健康状态。"""

    return Envelope(data=HealthData(status="ok"))
