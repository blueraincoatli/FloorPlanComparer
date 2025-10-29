from fastapi import APIRouter

from app.api.routes import health, jobs, enhanced, converter

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(enhanced.router, prefix="/enhanced", tags=["enhanced"])
api_router.include_router(converter.router, prefix="/enhanced", tags=["converter"])