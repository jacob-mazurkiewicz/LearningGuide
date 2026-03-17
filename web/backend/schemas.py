"""
schemas.py — Request and Response Data Shapes
=============================================

Pydantic schemas define the shape of data that comes INTO the API
(request bodies) and goes OUT of the API (response bodies).

Why use schemas separate from database models?
- The database model defines what's stored in the DB.
- The schema defines what the user sends and receives via the API.
- This separation lets you control what data is exposed and validated.

Key Pydantic concepts:
- BaseModel: The base class for all schemas.
- Optional[X]: The field might be None.
- Field(...): Define extra constraints or defaults.
- model_config = ConfigDict(from_attributes=True): Allows Pydantic to
  read data directly from SQLAlchemy model instances.
"""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# DailyTask schemas
# ---------------------------------------------------------------------------

class DailyTaskCreate(BaseModel):
    """Data required to CREATE a daily task."""
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = None
    scheduled_date: Optional[date] = None
    estimated_minutes: int = Field(default=30, ge=1, le=1440)  # 1 min to 24 hours
    notes: Optional[str] = None


class DailyTaskUpdate(BaseModel):
    """Data for UPDATING a daily task — all fields are optional."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    scheduled_date: Optional[date] = None
    estimated_minutes: Optional[int] = Field(None, ge=1, le=1440)
    completed: Optional[bool] = None
    notes: Optional[str] = None
    position: Optional[int] = None


class DailyTaskResponse(BaseModel):
    """Data returned when reading a daily task."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    subtask_id: int
    title: str
    description: Optional[str]
    position: int
    scheduled_date: Optional[date]
    estimated_minutes: int
    completed: bool
    completed_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime


# ---------------------------------------------------------------------------
# Subtask schemas
# ---------------------------------------------------------------------------

class SubtaskCreate(BaseModel):
    """Data required to CREATE a subtask."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class SubtaskUpdate(BaseModel):
    """Data for UPDATING a subtask."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    position: Optional[int] = None


class SubtaskResponse(BaseModel):
    """Data returned when reading a subtask (includes its daily tasks)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    goal_id: int
    title: str
    description: Optional[str]
    position: int
    start_date: Optional[date]
    end_date: Optional[date]
    created_at: datetime
    daily_tasks: List[DailyTaskResponse] = []

    @property
    def progress_percent(self) -> int:
        """How many daily tasks are completed (0–100)."""
        if not self.daily_tasks:
            return 0
        done = sum(1 for t in self.daily_tasks if t.completed)
        return int(done / len(self.daily_tasks) * 100)


# ---------------------------------------------------------------------------
# Goal schemas
# ---------------------------------------------------------------------------

class GoalCreate(BaseModel):
    """Data required to CREATE a goal."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class GoalUpdate(BaseModel):
    """Data for UPDATING a goal."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    position: Optional[int] = None


class GoalResponse(BaseModel):
    """Data returned when reading a goal (includes its subtasks)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_id: int
    title: str
    description: Optional[str]
    position: int
    start_date: Optional[date]
    end_date: Optional[date]
    created_at: datetime
    subtasks: List[SubtaskResponse] = []


# ---------------------------------------------------------------------------
# LearningPlan schemas
# ---------------------------------------------------------------------------

class PlanCreate(BaseModel):
    """Data required to CREATE a learning plan."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class PlanUpdate(BaseModel):
    """Data for UPDATING a learning plan."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None


class PlanSummary(BaseModel):
    """Lightweight plan data used in the sidebar list."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]


class PlanResponse(BaseModel):
    """Full plan data including all goals, subtasks, and tasks."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    goals: List[GoalResponse] = []


# ---------------------------------------------------------------------------
# Reordering schema
# ---------------------------------------------------------------------------

class ReorderRequest(BaseModel):
    """
    Sent when the user drags and drops to reorder items.

    `ids` is the new ordered list of item IDs.
    For example, if goals were [3, 1, 2] after dragging,
    we send ids=[3, 1, 2] and the backend updates their positions.
    """
    ids: List[int] = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# AI Generation schemas
# ---------------------------------------------------------------------------

class AIGenerateRequest(BaseModel):
    """Sent to the AI generation endpoint."""
    topic: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="What do you want to learn or build?",
        examples=["Learn Python in 8 weeks", "Build a personal finance tracker app"],
    )
    duration_weeks: int = Field(
        default=4,
        ge=1,
        le=52,
        description="How many weeks do you want the plan to span?",
    )
    hours_per_day: float = Field(
        default=1.0,
        ge=0.25,
        le=8.0,
        description="How many hours per day can you dedicate?",
    )


class AIGenerateResponse(BaseModel):
    """The AI-generated plan structure, ready to be imported."""
    plan_title: str
    plan_description: str
    goals: List[dict]   # Each dict has: title, description, subtasks (list of dicts)
