from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Goal(BaseModel):
    goal: str
    category: str
    requirements: List[str] = Field(default_factory=list)
    priority: str = "normal"
    confidence: float = 0.0
    intent_summary: str = ""


class Plan(BaseModel):
    steps: List[str] = Field(default_factory=list)


class Skill(BaseModel):
    name: str
    installed: bool = False
    description: str


class MemoryRecord(BaseModel):
    task: str
    goal: Goal
    plan: Plan
    timestamp: datetime = Field(default_factory=datetime.now)
    suggested_skills: List[Skill] = Field(default_factory=list)


class Task(BaseModel):
    user_input: str
    goal: Optional[Goal] = None
    plan: Optional[Plan] = None
    suggested_skills: List[Skill] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)


class Preference(BaseModel):
    key: str
    value: str
    timestamp: datetime = Field(default_factory=datetime.now)
