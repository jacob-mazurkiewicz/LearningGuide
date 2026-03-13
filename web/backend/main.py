"""
main.py — FastAPI Application
==============================

This is the heart of the web backend. It defines all API routes (endpoints)
and serves the frontend HTML/CSS/JS files.

How FastAPI works:
    - You define Python functions decorated with @app.get(), @app.post(), etc.
    - FastAPI automatically validates incoming data using your Pydantic schemas.
    - FastAPI generates interactive API documentation at /docs (try it!).

API Structure:
    /api/plans           — Learning plan CRUD
    /api/plans/{id}/goals   — Goal CRUD (nested under a plan)
    /api/goals/{id}/subtasks — Subtask CRUD
    /api/subtasks/{id}/tasks — Daily task CRUD
    /api/tasks/{id}      — Update/delete individual tasks
    /api/reorder         — Drag-and-drop reordering
    /api/ai/generate     — AI plan generation
    /api/ai/status       — Check if AI is configured
    /                    — Serves the frontend index.html
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

import models
import schemas
from database import engine, get_db, Base

# ─── Create all database tables (if they don't exist yet) ────────────────────
# This runs when the app starts. SQLAlchemy reads all the models and creates
# the corresponding tables in the SQLite database automatically.
Base.metadata.create_all(bind=engine)

# ─── Initialize the FastAPI application ──────────────────────────────────────
app = FastAPI(
    title="LearningGuide API",
    description="Backend API for the LearningGuide app — plan, track, and achieve your learning goals.",
    version="1.0.0",
)

# ─── CORS Middleware ──────────────────────────────────────────────────────────
# CORS (Cross-Origin Resource Sharing) lets the frontend (running on a different
# port during development) talk to this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Serve frontend static files ─────────────────────────────────────────────
# This makes the frontend files (HTML, CSS, JS) available through FastAPI.
# The frontend lives in ../frontend relative to this file.
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


# =============================================================================
# LEARNING PLANS
# =============================================================================

@app.get("/api/plans", response_model=List[schemas.PlanSummary], tags=["Plans"])
def list_plans(db: Session = Depends(get_db)):
    """Return a summary list of all learning plans (for the sidebar)."""
    return db.query(models.LearningPlan).order_by(models.LearningPlan.updated_at.desc()).all()


@app.post("/api/plans", response_model=schemas.PlanResponse, status_code=status.HTTP_201_CREATED, tags=["Plans"])
def create_plan(plan: schemas.PlanCreate, db: Session = Depends(get_db)):
    """Create a new learning plan."""
    db_plan = models.LearningPlan(**plan.model_dump())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan


@app.get("/api/plans/{plan_id}", response_model=schemas.PlanResponse, tags=["Plans"])
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    """Get a full plan including all goals, subtasks, and daily tasks."""
    plan = db.get(models.LearningPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@app.put("/api/plans/{plan_id}", response_model=schemas.PlanResponse, tags=["Plans"])
def update_plan(plan_id: int, data: schemas.PlanUpdate, db: Session = Depends(get_db)):
    """Update a plan's title or description."""
    plan = db.get(models.LearningPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(plan, field, value)
    plan.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(plan)
    return plan


@app.delete("/api/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Plans"])
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    """Delete a plan and all its goals, subtasks, and tasks."""
    plan = db.get(models.LearningPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    db.delete(plan)
    db.commit()


# =============================================================================
# GOALS
# =============================================================================

@app.get("/api/plans/{plan_id}/goals", response_model=List[schemas.GoalResponse], tags=["Goals"])
def list_goals(plan_id: int, db: Session = Depends(get_db)):
    """List all goals for a plan, ordered by position."""
    plan = db.get(models.LearningPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan.goals


@app.post("/api/plans/{plan_id}/goals", response_model=schemas.GoalResponse, status_code=201, tags=["Goals"])
def create_goal(plan_id: int, goal: schemas.GoalCreate, db: Session = Depends(get_db)):
    """Create a new goal within a plan."""
    plan = db.get(models.LearningPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    # Set position to be after the last goal
    max_pos = max((g.position for g in plan.goals), default=-1)
    db_goal = models.Goal(**goal.model_dump(), plan_id=plan_id, position=max_pos + 1)
    db.add(db_goal)
    plan.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_goal)
    return db_goal


@app.put("/api/goals/{goal_id}", response_model=schemas.GoalResponse, tags=["Goals"])
def update_goal(goal_id: int, data: schemas.GoalUpdate, db: Session = Depends(get_db)):
    """Update a goal."""
    goal = db.get(models.Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(goal, field, value)
    goal.plan.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(goal)
    return goal


@app.delete("/api/goals/{goal_id}", status_code=204, tags=["Goals"])
def delete_goal(goal_id: int, db: Session = Depends(get_db)):
    """Delete a goal and all its subtasks and tasks."""
    goal = db.get(models.Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    goal.plan.updated_at = datetime.utcnow()
    db.delete(goal)
    db.commit()


# =============================================================================
# SUBTASKS
# =============================================================================

@app.get("/api/goals/{goal_id}/subtasks", response_model=List[schemas.SubtaskResponse], tags=["Subtasks"])
def list_subtasks(goal_id: int, db: Session = Depends(get_db)):
    """List all subtasks for a goal."""
    goal = db.get(models.Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal.subtasks


@app.post("/api/goals/{goal_id}/subtasks", response_model=schemas.SubtaskResponse, status_code=201, tags=["Subtasks"])
def create_subtask(goal_id: int, subtask: schemas.SubtaskCreate, db: Session = Depends(get_db)):
    """Create a new subtask within a goal."""
    goal = db.get(models.Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    max_pos = max((s.position for s in goal.subtasks), default=-1)
    db_subtask = models.Subtask(**subtask.model_dump(), goal_id=goal_id, position=max_pos + 1)
    db.add(db_subtask)
    goal.plan.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_subtask)
    return db_subtask


@app.put("/api/subtasks/{subtask_id}", response_model=schemas.SubtaskResponse, tags=["Subtasks"])
def update_subtask(subtask_id: int, data: schemas.SubtaskUpdate, db: Session = Depends(get_db)):
    """Update a subtask."""
    subtask = db.get(models.Subtask, subtask_id)
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(subtask, field, value)
    subtask.goal.plan.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(subtask)
    return subtask


@app.delete("/api/subtasks/{subtask_id}", status_code=204, tags=["Subtasks"])
def delete_subtask(subtask_id: int, db: Session = Depends(get_db)):
    """Delete a subtask and all its daily tasks."""
    subtask = db.get(models.Subtask, subtask_id)
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")
    subtask.goal.plan.updated_at = datetime.utcnow()
    db.delete(subtask)
    db.commit()


# =============================================================================
# DAILY TASKS
# =============================================================================

@app.get("/api/subtasks/{subtask_id}/tasks", response_model=List[schemas.DailyTaskResponse], tags=["Daily Tasks"])
def list_tasks(subtask_id: int, db: Session = Depends(get_db)):
    """List all daily tasks for a subtask."""
    subtask = db.get(models.Subtask, subtask_id)
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")
    return subtask.daily_tasks


@app.post("/api/subtasks/{subtask_id}/tasks", response_model=schemas.DailyTaskResponse, status_code=201, tags=["Daily Tasks"])
def create_task(subtask_id: int, task: schemas.DailyTaskCreate, db: Session = Depends(get_db)):
    """Create a new daily task within a subtask."""
    subtask = db.get(models.Subtask, subtask_id)
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")
    max_pos = max((t.position for t in subtask.daily_tasks), default=-1)
    db_task = models.DailyTask(**task.model_dump(), subtask_id=subtask_id, position=max_pos + 1)
    db.add(db_task)
    subtask.goal.plan.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_task)
    return db_task


@app.put("/api/tasks/{task_id}", response_model=schemas.DailyTaskResponse, tags=["Daily Tasks"])
def update_task(task_id: int, data: schemas.DailyTaskUpdate, db: Session = Depends(get_db)):
    """Update a daily task (title, notes, date, etc.)."""
    task = db.get(models.DailyTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    updates = data.model_dump(exclude_none=True)

    # If completing the task, record when it was completed
    if "completed" in updates:
        if updates["completed"] and not task.completed:
            task.completed_at = datetime.utcnow()
        elif not updates["completed"]:
            task.completed_at = None

    for field, value in updates.items():
        setattr(task, field, value)

    task.subtask.goal.plan.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return task


@app.delete("/api/tasks/{task_id}", status_code=204, tags=["Daily Tasks"])
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a daily task."""
    task = db.get(models.DailyTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.subtask.goal.plan.updated_at = datetime.utcnow()
    db.delete(task)
    db.commit()


# =============================================================================
# DRAG-AND-DROP REORDERING
# =============================================================================

@app.put("/api/plans/{plan_id}/goals/reorder", tags=["Reorder"])
def reorder_goals(plan_id: int, data: schemas.ReorderRequest, db: Session = Depends(get_db)):
    """
    Reorder goals within a plan after drag-and-drop.
    `data.ids` is the new ordered list of goal IDs.
    """
    plan = db.get(models.LearningPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    for position, goal_id in enumerate(data.ids):
        goal = db.get(models.Goal, goal_id)
        if goal and goal.plan_id == plan_id:
            goal.position = position
    plan.updated_at = datetime.utcnow()
    db.commit()
    return {"ok": True}


@app.put("/api/goals/{goal_id}/subtasks/reorder", tags=["Reorder"])
def reorder_subtasks(goal_id: int, data: schemas.ReorderRequest, db: Session = Depends(get_db)):
    """Reorder subtasks within a goal after drag-and-drop."""
    goal = db.get(models.Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    for position, subtask_id in enumerate(data.ids):
        subtask = db.get(models.Subtask, subtask_id)
        if subtask and subtask.goal_id == goal_id:
            subtask.position = position
    goal.plan.updated_at = datetime.utcnow()
    db.commit()
    return {"ok": True}


@app.put("/api/subtasks/{subtask_id}/tasks/reorder", tags=["Reorder"])
def reorder_tasks(subtask_id: int, data: schemas.ReorderRequest, db: Session = Depends(get_db)):
    """Reorder daily tasks within a subtask after drag-and-drop."""
    subtask = db.get(models.Subtask, subtask_id)
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")
    for position, task_id in enumerate(data.ids):
        task = db.get(models.DailyTask, task_id)
        if task and task.subtask_id == subtask_id:
            task.position = position
    subtask.goal.plan.updated_at = datetime.utcnow()
    db.commit()
    return {"ok": True}


# =============================================================================
# AI GENERATION
# =============================================================================

@app.get("/api/ai/status", tags=["AI"])
def ai_status():
    """Check which AI providers are configured."""
    return {
        "groq": bool(os.getenv("GROQ_API_KEY")),
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "ollama": True,  # Ollama is always "available" (we check at generation time)
        "any_configured": bool(
            os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY") or True
        ),
    }


@app.post("/api/ai/generate", response_model=schemas.AIGenerateResponse, tags=["AI"])
def ai_generate(request: schemas.AIGenerateRequest):
    """
    Generate a full learning plan using AI.

    The generated plan is returned as JSON — the frontend shows a preview
    and the user can click "Create Plan" to save it.
    """
    from ai_service import generate_learning_plan
    try:
        result = generate_learning_plan(
            topic=request.topic,
            duration_weeks=request.duration_weeks,
            hours_per_day=request.hours_per_day,
        )
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/api/ai/import", response_model=schemas.PlanResponse, status_code=201, tags=["AI"])
def ai_import_plan(plan_data: schemas.AIGenerateResponse, db: Session = Depends(get_db)):
    """
    Import an AI-generated plan into the database.

    After the user reviews the AI-generated plan, this endpoint saves it.
    """
    # Create the top-level plan
    db_plan = models.LearningPlan(
        title=plan_data.plan_title,
        description=plan_data.plan_description,
    )
    db.add(db_plan)
    db.flush()  # Get the plan ID without committing

    # Create goals, subtasks, and tasks from the nested structure
    for g_pos, goal_data in enumerate(plan_data.goals):
        db_goal = models.Goal(
            plan_id=db_plan.id,
            title=goal_data.get("title", ""),
            description=goal_data.get("description", ""),
            position=g_pos,
        )
        db.add(db_goal)
        db.flush()

        for s_pos, subtask_data in enumerate(goal_data.get("subtasks", [])):
            db_subtask = models.Subtask(
                goal_id=db_goal.id,
                title=subtask_data.get("title", ""),
                description=subtask_data.get("description", ""),
                position=s_pos,
            )
            db.add(db_subtask)
            db.flush()

            for t_pos, task_data in enumerate(subtask_data.get("daily_tasks", [])):
                db_task = models.DailyTask(
                    subtask_id=db_subtask.id,
                    title=task_data.get("title", ""),
                    description=task_data.get("description", ""),
                    estimated_minutes=task_data.get("estimated_minutes", 30),
                    position=t_pos,
                )
                db.add(db_task)

    db.commit()
    db.refresh(db_plan)
    return db_plan


# =============================================================================
# FRONTEND SERVING
# =============================================================================
# Serve static frontend files if the frontend directory exists.
# In production, you could serve these from a CDN instead.

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend():
        """Serve the main frontend HTML file."""
        return FileResponse(str(FRONTEND_DIR / "index.html"))
