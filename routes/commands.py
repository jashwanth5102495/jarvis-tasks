
from fastapi import APIRouter
from jarvis_server.models.command_models import CommandRequest, CommandResponse
from jarvis_server.core.executor import execute_command


router = APIRouter(prefix="", tags=["commands"])


@router.post("/command", response_model=CommandResponse)
def post_command(request: CommandRequest):
    success, message = execute_command(request.command)
    if success:
        return CommandResponse(
            status="success",
            message=message,
            command=request.command
        )
    else:
        return CommandResponse(
            status="failed",
            message=message,
            command=request.command
        )
