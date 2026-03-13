# 🐍 Web Backend — FastAPI + SQLite

The backend is a Python application built with **FastAPI**. It handles:
1. Storing and retrieving data (learning plans, goals, subtasks, tasks)
2. AI plan generation
3. Serving the frontend HTML/CSS/JS files

## Files

| File | Purpose |
|------|---------|
| `main.py` | The API server — all routes live here |
| `models.py` | SQLAlchemy database models (the tables) |
| `schemas.py` | Pydantic schemas (validates incoming/outgoing data) |
| `database.py` | Database connection setup |
| `ai_service.py` | AI generation logic |
| `requirements.txt` | Python package dependencies |
| `.env.example` | Template for environment variables |
| `tests/` | Automated tests |

## Key Concepts Explained

### FastAPI Routes
A "route" is a URL + HTTP method that your API handles. For example:

```python
@app.get("/api/plans")        # Handle GET /api/plans
def list_plans(db = Depends(get_db)):
    return db.query(LearningPlan).all()
```

HTTP methods:
- `GET` — Retrieve data (no side effects)
- `POST` — Create new data
- `PUT` — Update existing data
- `DELETE` — Remove data

### SQLAlchemy ORM
Instead of writing SQL like:
```sql
SELECT * FROM learning_plans WHERE id = 1;
```

We write Python:
```python
plan = db.get(LearningPlan, 1)
```

SQLAlchemy translates Python → SQL automatically.

### Pydantic Validation
FastAPI uses Pydantic to validate data. If you send:
```json
{"title": ""}
```
To an endpoint that requires `min_length=1`, FastAPI automatically returns a 422 error
with a clear message explaining what's wrong.

### Dependency Injection
FastAPI's `Depends()` lets you share setup code across routes.
The `get_db` function opens a database session and automatically closes it after
each request — even if an error occurs.

## Database Schema

```
learning_plans
  └── id, title, description, created_at, updated_at

goals
  └── id, plan_id (FK), title, description, position, start_date, end_date

subtasks
  └── id, goal_id (FK), title, description, position, start_date, end_date

daily_tasks
  └── id, subtask_id (FK), title, description, position,
      scheduled_date, estimated_minutes, completed, completed_at, notes
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/plans` | List all plans |
| POST | `/api/plans` | Create a plan |
| GET | `/api/plans/{id}` | Get full plan (nested) |
| PUT | `/api/plans/{id}` | Update a plan |
| DELETE | `/api/plans/{id}` | Delete a plan |
| POST | `/api/plans/{id}/goals` | Create a goal |
| PUT | `/api/goals/{id}` | Update a goal |
| DELETE | `/api/goals/{id}` | Delete a goal |
| POST | `/api/goals/{id}/subtasks` | Create a subtask |
| PUT | `/api/subtasks/{id}` | Update a subtask |
| DELETE | `/api/subtasks/{id}` | Delete a subtask |
| POST | `/api/subtasks/{id}/tasks` | Create a daily task |
| PUT | `/api/tasks/{id}` | Update a task (incl. complete it) |
| DELETE | `/api/tasks/{id}` | Delete a task |
| PUT | `/api/plans/{id}/goals/reorder` | Reorder goals |
| PUT | `/api/goals/{id}/subtasks/reorder` | Reorder subtasks |
| PUT | `/api/subtasks/{id}/tasks/reorder` | Reorder tasks |
| GET | `/api/ai/status` | Check AI configuration |
| POST | `/api/ai/generate` | Generate plan with AI |
| POST | `/api/ai/import` | Save AI-generated plan |

## Running Tests

```bash
cd web/backend
pytest tests/ -v              # All tests, verbose
pytest tests/ -v -k "goal"    # Only goal-related tests
pytest tests/ --tb=short      # Short traceback on failure
```

Tests use an **in-memory SQLite database** — they don't affect your real data.
