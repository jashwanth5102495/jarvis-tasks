
from fastapi import APIRouter
from jarvis_server.models.command_models import HealthResponse


router = APIRouter(prefix="", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def get_health():
    return HealthResponse(status="online")
