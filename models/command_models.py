
from pydantic import BaseModel, Field
from typing import Optional


class CommandRequest(BaseModel):
    command: str = Field(..., description="The command to execute")
    source: Optional[str] = Field("unknown", description="Source of the command")


class CommandResponse(BaseModel):
    status: str = Field(..., description="Status of command execution")
    message: Optional[str] = Field(None, description="Response message")
    command: str = Field(..., description="The executed command")


class HealthResponse(BaseModel):
    status: str = "online"
