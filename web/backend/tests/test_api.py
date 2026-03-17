"""
test_api.py — API Endpoint Tests
==================================

These tests verify that every API endpoint behaves correctly.
Each test function starts with "test_" — pytest discovers them automatically.

Test naming convention: test_<what>_<expected result>
  e.g., test_create_plan_success, test_get_plan_not_found

Run tests with:
    cd web/backend
    pytest tests/ -v          # verbose output
    pytest tests/ -v -k plan  # only tests with "plan" in the name
"""

import pytest


# =============================================================================
# LEARNING PLAN TESTS
# =============================================================================

class TestPlans:
    """Tests for the /api/plans endpoints."""

    def test_list_plans_empty(self, client):
        """A fresh database should return an empty list of plans."""
        response = client.get("/api/plans")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_plan_success(self, client):
        """Creating a plan with valid data should return 201 and the plan."""
        response = client.post("/api/plans", json={
            "title": "Learn FastAPI",
            "description": "Master Python web APIs",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Learn FastAPI"
        assert data["description"] == "Master Python web APIs"
        assert "id" in data
        assert "created_at" in data

    def test_create_plan_minimal(self, client):
        """Creating a plan with only a title (no description) should work."""
        response = client.post("/api/plans", json={"title": "Quick Plan"})
        assert response.status_code == 201
        assert response.json()["title"] == "Quick Plan"
        assert response.json()["description"] is None

    def test_create_plan_missing_title(self, client):
        """Creating a plan without a title should fail with 422."""
        response = client.post("/api/plans", json={"description": "No title"})
        assert response.status_code == 422

    def test_create_plan_empty_title(self, client):
        """Creating a plan with an empty string title should fail."""
        response = client.post("/api/plans", json={"title": ""})
        assert response.status_code == 422

    def test_get_plan_success(self, client, sample_plan):
        """Getting a plan by ID should return the full plan with empty goals."""
        response = client.get(f"/api/plans/{sample_plan['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_plan["id"]
        assert data["title"] == sample_plan["title"]
        assert data["goals"] == []  # No goals yet

    def test_get_plan_not_found(self, client):
        """Getting a nonexistent plan should return 404."""
        response = client.get("/api/plans/99999")
        assert response.status_code == 404

    def test_update_plan_title(self, client, sample_plan):
        """Updating a plan's title should work."""
        response = client.put(f"/api/plans/{sample_plan['id']}", json={
            "title": "Updated Title",
        })
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    def test_update_plan_partial(self, client, sample_plan):
        """Updating only description should leave title unchanged."""
        response = client.put(f"/api/plans/{sample_plan['id']}", json={
            "description": "New description",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == sample_plan["title"]
        assert data["description"] == "New description"

    def test_delete_plan_success(self, client, sample_plan):
        """Deleting a plan should return 204 and make the plan unreachable."""
        response = client.delete(f"/api/plans/{sample_plan['id']}")
        assert response.status_code == 204

        # Verify it's gone
        response = client.get(f"/api/plans/{sample_plan['id']}")
        assert response.status_code == 404

    def test_list_plans_shows_created(self, client, sample_plan):
        """After creating a plan, it should appear in the list."""
        response = client.get("/api/plans")
        assert response.status_code == 200
        ids = [p["id"] for p in response.json()]
        assert sample_plan["id"] in ids


# =============================================================================
# GOAL TESTS
# =============================================================================

class TestGoals:
    """Tests for the /api/plans/{id}/goals and /api/goals/{id} endpoints."""

    def test_create_goal_success(self, client, sample_plan):
        """Creating a goal within a plan should succeed."""
        response = client.post(f"/api/plans/{sample_plan['id']}/goals", json={
            "title": "Python Fundamentals",
            "description": "Learn basic Python concepts",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Python Fundamentals"
        assert data["plan_id"] == sample_plan["id"]
        assert data["position"] == 0  # First goal gets position 0

    def test_create_second_goal_position(self, client, sample_plan):
        """Second goal should get position 1."""
        client.post(f"/api/plans/{sample_plan['id']}/goals", json={"title": "Goal 1"})
        response = client.post(f"/api/plans/{sample_plan['id']}/goals", json={"title": "Goal 2"})
        assert response.status_code == 201
        assert response.json()["position"] == 1

    def test_create_goal_bad_plan(self, client):
        """Creating a goal in a nonexistent plan should return 404."""
        response = client.post("/api/plans/99999/goals", json={"title": "Orphan Goal"})
        assert response.status_code == 404

    def test_get_goals_for_plan(self, client, sample_plan, sample_goal):
        """Listing goals for a plan should include the created goal."""
        response = client.get(f"/api/plans/{sample_plan['id']}/goals")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["id"] == sample_goal["id"]

    def test_get_plan_includes_goals(self, client, sample_plan, sample_goal):
        """Getting the full plan should include nested goals."""
        response = client.get(f"/api/plans/{sample_plan['id']}")
        assert response.status_code == 200
        goals = response.json()["goals"]
        assert len(goals) == 1
        assert goals[0]["title"] == sample_goal["title"]

    def test_update_goal(self, client, sample_goal):
        """Updating a goal should work."""
        response = client.put(f"/api/goals/{sample_goal['id']}", json={
            "title": "Updated Goal Title",
        })
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Goal Title"

    def test_delete_goal(self, client, sample_goal, sample_plan):
        """Deleting a goal should remove it from the plan."""
        response = client.delete(f"/api/goals/{sample_goal['id']}")
        assert response.status_code == 204

        # Plan should have no goals now
        response = client.get(f"/api/plans/{sample_plan['id']}")
        assert response.json()["goals"] == []

    def test_reorder_goals(self, client, sample_plan):
        """Reordering goals should update their positions."""
        g1 = client.post(f"/api/plans/{sample_plan['id']}/goals", json={"title": "Goal A"}).json()
        g2 = client.post(f"/api/plans/{sample_plan['id']}/goals", json={"title": "Goal B"}).json()
        g3 = client.post(f"/api/plans/{sample_plan['id']}/goals", json={"title": "Goal C"}).json()

        # Reorder: C, A, B
        response = client.put(
            f"/api/plans/{sample_plan['id']}/goals/reorder",
            json={"ids": [g3["id"], g1["id"], g2["id"]]},
        )
        assert response.status_code == 200

        # Fetch and verify order
        goals = client.get(f"/api/plans/{sample_plan['id']}/goals").json()
        assert goals[0]["id"] == g3["id"]
        assert goals[1]["id"] == g1["id"]
        assert goals[2]["id"] == g2["id"]


# =============================================================================
# SUBTASK TESTS
# =============================================================================

class TestSubtasks:
    """Tests for subtask endpoints."""

    def test_create_subtask(self, client, sample_goal):
        """Creating a subtask within a goal should succeed."""
        response = client.post(f"/api/goals/{sample_goal['id']}/subtasks", json={
            "title": "Learn variables",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["goal_id"] == sample_goal["id"]
        assert data["title"] == "Learn variables"

    def test_create_subtask_bad_goal(self, client):
        """Creating a subtask in a nonexistent goal should return 404."""
        response = client.post("/api/goals/99999/subtasks", json={"title": "Orphan"})
        assert response.status_code == 404

    def test_get_plan_includes_subtasks(self, client, sample_plan, sample_goal, sample_subtask):
        """Getting the full plan should include nested subtasks."""
        response = client.get(f"/api/plans/{sample_plan['id']}")
        goals = response.json()["goals"]
        subtasks = goals[0]["subtasks"]
        assert len(subtasks) == 1
        assert subtasks[0]["id"] == sample_subtask["id"]

    def test_update_subtask(self, client, sample_subtask):
        """Updating a subtask should reflect changes."""
        response = client.put(f"/api/subtasks/{sample_subtask['id']}", json={
            "title": "New Subtask Title",
        })
        assert response.status_code == 200
        assert response.json()["title"] == "New Subtask Title"

    def test_delete_subtask(self, client, sample_subtask, sample_goal):
        """Deleting a subtask should remove it from the goal."""
        response = client.delete(f"/api/subtasks/{sample_subtask['id']}")
        assert response.status_code == 204

        subtasks = client.get(f"/api/goals/{sample_goal['id']}/subtasks").json()
        assert subtasks == []


# =============================================================================
# DAILY TASK TESTS
# =============================================================================

class TestDailyTasks:
    """Tests for daily task endpoints."""

    def test_create_task(self, client, sample_subtask):
        """Creating a daily task should succeed."""
        response = client.post(f"/api/subtasks/{sample_subtask['id']}/tasks", json={
            "title": "Watch tutorial video",
            "estimated_minutes": 30,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Watch tutorial video"
        assert data["completed"] is False
        assert data["estimated_minutes"] == 30

    def test_create_task_with_date(self, client, sample_subtask):
        """Creating a task with a scheduled date should work."""
        response = client.post(f"/api/subtasks/{sample_subtask['id']}/tasks", json={
            "title": "Dated task",
            "scheduled_date": "2025-01-15",
        })
        assert response.status_code == 201
        assert response.json()["scheduled_date"] == "2025-01-15"

    def test_complete_task(self, client, sample_task):
        """Marking a task as complete should set completed=True and completed_at."""
        response = client.put(f"/api/tasks/{sample_task['id']}", json={"completed": True})
        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is True
        assert data["completed_at"] is not None

    def test_uncomplete_task(self, client, sample_task):
        """Un-marking a completed task should clear completed_at."""
        # First complete it
        client.put(f"/api/tasks/{sample_task['id']}", json={"completed": True})
        # Then uncomplete
        response = client.put(f"/api/tasks/{sample_task['id']}", json={"completed": False})
        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is False
        assert data["completed_at"] is None

    def test_add_notes_to_task(self, client, sample_task):
        """Adding notes to a task should work."""
        response = client.put(f"/api/tasks/{sample_task['id']}", json={
            "notes": "I struggled with list comprehensions but got it eventually.",
        })
        assert response.status_code == 200
        assert "struggled with list comprehensions" in response.json()["notes"]

    def test_delete_task(self, client, sample_task, sample_subtask):
        """Deleting a task should remove it."""
        response = client.delete(f"/api/tasks/{sample_task['id']}")
        assert response.status_code == 204

        tasks = client.get(f"/api/subtasks/{sample_subtask['id']}/tasks").json()
        assert tasks == []

    def test_task_position_increments(self, client, sample_subtask):
        """Each new task should get the next position number."""
        t1 = client.post(f"/api/subtasks/{sample_subtask['id']}/tasks", json={"title": "T1"}).json()
        t2 = client.post(f"/api/subtasks/{sample_subtask['id']}/tasks", json={"title": "T2"}).json()
        t3 = client.post(f"/api/subtasks/{sample_subtask['id']}/tasks", json={"title": "T3"}).json()
        assert t1["position"] == 0
        assert t2["position"] == 1
        assert t3["position"] == 2

    def test_reorder_tasks(self, client, sample_subtask):
        """Reordering tasks should update positions correctly."""
        t1 = client.post(f"/api/subtasks/{sample_subtask['id']}/tasks", json={"title": "T1"}).json()
        t2 = client.post(f"/api/subtasks/{sample_subtask['id']}/tasks", json={"title": "T2"}).json()
        t3 = client.post(f"/api/subtasks/{sample_subtask['id']}/tasks", json={"title": "T3"}).json()

        response = client.put(
            f"/api/subtasks/{sample_subtask['id']}/tasks/reorder",
            json={"ids": [t3["id"], t2["id"], t1["id"]]},
        )
        assert response.status_code == 200

        tasks = client.get(f"/api/subtasks/{sample_subtask['id']}/tasks").json()
        assert tasks[0]["id"] == t3["id"]
        assert tasks[1]["id"] == t2["id"]
        assert tasks[2]["id"] == t1["id"]


# =============================================================================
# CASCADING DELETE TESTS
# =============================================================================

class TestCascadingDeletes:
    """Verify that deleting a parent deletes all children."""

    def test_delete_plan_deletes_goals(self, client, sample_plan, sample_goal):
        """Deleting a plan should also delete its goals."""
        client.delete(f"/api/plans/{sample_plan['id']}")
        # The goal should be gone too (cascaded delete)
        response = client.get(f"/api/goals/{sample_goal['id']}/subtasks")
        assert response.status_code == 404

    def test_delete_goal_deletes_subtasks(self, client, sample_goal, sample_subtask):
        """Deleting a goal should also delete its subtasks."""
        client.delete(f"/api/goals/{sample_goal['id']}")
        response = client.get(f"/api/subtasks/{sample_subtask['id']}/tasks")
        assert response.status_code == 404


# =============================================================================
# AI STATUS TEST
# =============================================================================

class TestAI:
    """Tests for AI-related endpoints."""

    def test_ai_status(self, client):
        """The AI status endpoint should always return a response."""
        response = client.get("/api/ai/status")
        assert response.status_code == 200
        data = response.json()
        assert "groq" in data
        assert "openai" in data
        assert "ollama" in data
