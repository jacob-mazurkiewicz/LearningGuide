"""
app.py — LearningGuide Desktop App
====================================
Built with Flet — a Python framework that lets you create beautiful
desktop (and mobile/web) apps entirely in Python.

Flet uses Flutter's rendering engine, so it looks modern and native
on any platform (macOS, Windows, Linux).

How to run:
    python app.py               # Desktop window
    flet run --web app.py       # In the browser at http://localhost:8550

The desktop app connects to the FastAPI backend (web app) to store and
retrieve data. This means:
1. Start the web backend first: cd ../web/backend && uvicorn main:app --reload
2. Then run: python app.py

Alternatively, the desktop app can be extended to include its own
database connection (see web/backend/database.py and models.py).

Key Flet concepts:
- Page: The top-level container for your app
- Controls: UI elements (ft.Text, ft.ElevatedButton, ft.Column, etc.)
- ft.app(target): Starts the Flet app
- page.add(): Add controls to the page
- page.update(): Refresh the display after making changes
"""

import flet as ft
import httpx
import threading
from typing import Optional

# URL of the FastAPI backend
API_BASE = "http://localhost:8000/api"


# =============================================================================
# API HELPER
# =============================================================================

def api_get(path: str) -> Optional[dict | list]:
    """Make a GET request to the API. Returns None on error."""
    try:
        res = httpx.get(f"{API_BASE}{path}", timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return None


def api_post(path: str, body: dict) -> Optional[dict]:
    """Make a POST request to the API."""
    try:
        res = httpx.post(f"{API_BASE}{path}", json=body, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return None


def api_put(path: str, body: dict) -> Optional[dict]:
    """Make a PUT request to the API."""
    try:
        res = httpx.put(f"{API_BASE}{path}", json=body, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return None


def api_delete(path: str) -> bool:
    """Make a DELETE request to the API. Returns True on success."""
    try:
        res = httpx.delete(f"{API_BASE}{path}", timeout=10)
        return res.status_code == 204
    except Exception:
        return False


# =============================================================================
# MAIN APP
# =============================================================================

def main(page: ft.Page):
    """
    This function is the entry point for the Flet app.
    Flet calls this function with the Page object.
    """
    # ── Page configuration ────────────────────────────────────────────────
    page.title = "LearningGuide 📚"
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.window.width = 1100
    page.window.height = 750
    page.window.min_width = 700
    page.window.min_height = 500
    page.padding = 0

    # Color theme
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE)

    # ── State ─────────────────────────────────────────────────────────────
    state = {
        "plans": [],
        "current_plan": None,
        "current_plan_id": None,
    }

    # ── UI References (components we need to update later) ───────────────
    plan_list_view = ft.ListView(spacing=2, padding=ft.padding.symmetric(vertical=8))
    main_content = ft.Column(expand=True)
    status_bar = ft.Text("", size=12, color=ft.Colors.GREY_600)

    # ── Error / connection banner ─────────────────────────────────────────
    connection_error = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.ORANGE),
            ft.Text(
                "Cannot connect to backend. Start the web server first:\n"
                "cd web/backend && uvicorn main:app --reload",
                size=13,
                color=ft.Colors.ORANGE_900,
            ),
        ]),
        bgcolor=ft.Colors.ORANGE_50,
        border=ft.border.all(1, ft.Colors.ORANGE_200),
        border_radius=8,
        padding=12,
        margin=ft.margin.all(16),
        visible=False,
    )

    # =========================================================================
    # SIDEBAR — Plan list
    # =========================================================================

    def load_plans():
        plans = api_get("/plans")
        if plans is None:
            connection_error.visible = True
            page.update()
            return

        connection_error.visible = False
        state["plans"] = plans
        render_plan_list()
        page.update()

    def render_plan_list():
        plan_list_view.controls.clear()
        for plan in state["plans"]:
            is_active = state["current_plan_id"] == plan["id"]
            plan_tile = ft.Container(
                content=ft.Row([
                    ft.Icon(
                        ft.Icons.MENU_BOOK,
                        size=16,
                        color=ft.Colors.WHITE if is_active else ft.Colors.BLUE_700,
                    ),
                    ft.Text(
                        plan["title"],
                        size=13,
                        weight=ft.FontWeight.W_500,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        expand=True,
                        color=ft.Colors.WHITE if is_active else None,
                    ),
                ]),
                bgcolor=ft.Colors.BLUE_700 if is_active else None,
                border_radius=6,
                padding=ft.padding.symmetric(horizontal=10, vertical=8),
                ink=True,
                on_click=lambda e, pid=plan["id"]: select_plan(pid),
            )
            plan_list_view.controls.append(plan_tile)

    def select_plan(plan_id: int):
        state["current_plan_id"] = plan_id
        plan_data = api_get(f"/plans/{plan_id}")
        if plan_data:
            state["current_plan"] = plan_data
            render_plan_view()
            render_plan_list()
            page.update()

    # =========================================================================
    # PLAN VIEW
    # =========================================================================

    def render_plan_view():
        plan = state["current_plan"]
        if not plan:
            return

        # Calculate progress
        all_tasks = [
            task
            for goal in plan["goals"]
            for subtask in goal["subtasks"]
            for task in subtask["daily_tasks"]
        ]
        total = len(all_tasks)
        done = sum(1 for t in all_tasks if t["completed"])
        pct = round(done / total * 100) if total > 0 else 0

        # Build the goals view
        goals_view = ft.Column(
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        if not plan["goals"]:
            goals_view.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.TRACK_CHANGES, size=48, color=ft.Colors.GREY_400),
                        ft.Text("No goals yet", size=18, color=ft.Colors.GREY_500),
                        ft.Text("Click 'Add Goal' to get started", size=13, color=ft.Colors.GREY_400),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    expand=True,
                )
            )
        else:
            for goal in plan["goals"]:
                goals_view.controls.append(create_goal_card(goal))

        main_content.controls = [
            # Plan header
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Column([
                            ft.Text(plan["title"], size=22, weight=ft.FontWeight.BOLD),
                            ft.Text(plan.get("description") or "", size=13, color=ft.Colors.GREY_600),
                        ], expand=True),
                        ft.Row([
                            ft.ElevatedButton(
                                "Add Goal",
                                icon=ft.Icons.ADD,
                                on_click=lambda _: open_add_goal_dialog(),
                            ),
                            ft.OutlinedButton(
                                "Edit",
                                icon=ft.Icons.EDIT_OUTLINED,
                                on_click=lambda _: open_edit_plan_dialog(),
                            ),
                            ft.OutlinedButton(
                                "Delete",
                                icon=ft.Icons.DELETE_OUTLINE,
                                style=ft.ButtonStyle(color=ft.Colors.RED),
                                on_click=lambda _: confirm_delete_plan(),
                            ),
                        ]),
                    ]),
                    # Progress bar
                    ft.Row([
                        ft.ProgressBar(
                            value=pct / 100,
                            expand=True,
                            color=ft.Colors.GREEN,
                            bgcolor=ft.Colors.GREY_200,
                        ),
                        ft.Text(f"{done}/{total} ({pct}%)", size=12, color=ft.Colors.GREY_600),
                    ]),
                ], spacing=8),
                padding=ft.padding.all(20),
                border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_200)),
            ),
            # Goals area
            ft.Container(
                content=goals_view,
                expand=True,
                padding=ft.padding.all(20),
            ),
            connection_error,
        ]

    def create_goal_card(goal: dict) -> ft.Container:
        """Create a card UI component for a goal."""
        all_tasks = [t for s in goal["subtasks"] for t in s["daily_tasks"]]
        total = len(all_tasks)
        done = sum(1 for t in all_tasks if t["completed"])
        pct = round(done / total * 100) if total > 0 else 0

        subtasks_col = ft.Column(spacing=8)
        for subtask in goal["subtasks"]:
            subtasks_col.controls.append(create_subtask_item(subtask))

        return ft.Container(
            content=ft.Column([
                # Goal header
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.TRACK_CHANGES, color=ft.Colors.BLUE_700, size=18),
                        ft.Column([
                            ft.Text(goal["title"], size=15, weight=ft.FontWeight.W_600, expand=True),
                            ft.Text(goal.get("description") or "", size=12, color=ft.Colors.GREY_600),
                        ], expand=True, spacing=2),
                        ft.Row([
                            ft.Text(f"{pct}%", size=12, color=ft.Colors.GREEN_700),
                            ft.IconButton(
                                ft.Icons.ADD_CIRCLE_OUTLINE,
                                tooltip="Add Subtask",
                                icon_size=18,
                                on_click=lambda _, gid=goal["id"]: open_add_subtask_dialog(gid),
                            ),
                            ft.IconButton(
                                ft.Icons.EDIT_OUTLINED,
                                tooltip="Edit Goal",
                                icon_size=18,
                                on_click=lambda _, g=goal: open_edit_goal_dialog(g),
                            ),
                            ft.IconButton(
                                ft.Icons.DELETE_OUTLINE,
                                tooltip="Delete Goal",
                                icon_size=18,
                                icon_color=ft.Colors.RED_400,
                                on_click=lambda _, gid=goal["id"]: confirm_delete_goal(gid),
                            ),
                        ], spacing=0),
                    ], spacing=8),
                    bgcolor=ft.Colors.BLUE_50,
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                    border_radius=ft.border_radius.only(top_left=8, top_right=8),
                ),
                ft.ProgressBar(value=pct / 100, color=ft.Colors.GREEN, bgcolor=ft.Colors.GREY_200, height=4),
                # Subtasks
                ft.Container(
                    content=subtasks_col,
                    padding=ft.padding.all(12),
                ),
            ], spacing=0),
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=8,
            margin=ft.margin.only(bottom=8),
        )

    def create_subtask_item(subtask: dict) -> ft.Container:
        """Create a UI component for a subtask."""
        tasks = subtask["daily_tasks"]
        done = sum(1 for t in tasks if t["completed"])

        task_items = ft.Column(spacing=4, visible=True)
        if not tasks:
            task_items.controls.append(ft.Text("No tasks yet", size=12, italic=True, color=ft.Colors.GREY_400))
        for task in tasks:
            task_items.controls.append(create_task_row(task))

        # Expand/collapse state for this subtask
        expand_icon = ft.Icon(ft.Icons.EXPAND_MORE, size=18)
        is_expanded = {"value": True}

        def toggle_expand(_):
            is_expanded["value"] = not is_expanded["value"]
            task_items.visible = is_expanded["value"]
            expand_icon.name = ft.Icons.EXPAND_MORE if is_expanded["value"] else ft.Icons.CHEVRON_RIGHT
            page.update()

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.GestureDetector(
                        content=expand_icon,
                        on_tap=toggle_expand,
                    ),
                    ft.Icon(ft.Icons.LAYERS_OUTLINED, size=15, color=ft.Colors.BLUE_400),
                    ft.Text(subtask["title"], size=13, weight=ft.FontWeight.W_500, expand=True),
                    ft.Text(f"{done}/{len(tasks)}", size=12, color=ft.Colors.GREY_500),
                    ft.IconButton(
                        ft.Icons.ADD,
                        tooltip="Add Task",
                        icon_size=16,
                        on_click=lambda _, sid=subtask["id"]: open_add_task_dialog(sid),
                    ),
                    ft.IconButton(
                        ft.Icons.EDIT_OUTLINED,
                        tooltip="Edit Subtask",
                        icon_size=16,
                        on_click=lambda _, s=subtask: open_edit_subtask_dialog(s),
                    ),
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE,
                        tooltip="Delete",
                        icon_size=16,
                        icon_color=ft.Colors.RED_300,
                        on_click=lambda _, sid=subtask["id"]: confirm_delete_subtask(sid),
                    ),
                ], spacing=4),
                ft.Container(
                    content=task_items,
                    padding=ft.padding.only(left=24),
                ),
            ], spacing=4),
            padding=ft.padding.symmetric(vertical=4, horizontal=8),
            border=ft.border.all(1, ft.Colors.GREY_100),
            border_radius=6,
            bgcolor=ft.Colors.GREY_50,
        )

    def create_task_row(task: dict) -> ft.Row:
        """Create a row UI for a single daily task with a checkbox."""
        checkbox = ft.Checkbox(
            value=task["completed"],
            label=task["title"],
            label_style=ft.TextStyle(
                decoration=ft.TextDecoration.LINE_THROUGH if task["completed"] else None,
                color=ft.Colors.GREY_500 if task["completed"] else None,
                size=13,
            ),
            on_change=lambda e, tid=task["id"]: toggle_task(tid, e.control.value),
        )
        time_badge = ft.Container(
            content=ft.Text(
                f"{task['estimated_minutes']}m",
                size=11,
                color=ft.Colors.GREY_500,
            ),
            bgcolor=ft.Colors.GREY_100,
            border_radius=4,
            padding=ft.padding.symmetric(horizontal=4, vertical=1),
        )
        return ft.Row([
            checkbox,
            time_badge,
            ft.IconButton(
                ft.Icons.EDIT_OUTLINED,
                tooltip="Edit task",
                icon_size=14,
                on_click=lambda _, t=task: open_edit_task_dialog(t),
            ),
        ], spacing=4)

    def toggle_task(task_id: int, completed: bool):
        result = api_put(f"/tasks/{task_id}", {"completed": completed})
        if result:
            select_plan(state["current_plan_id"])

    # =========================================================================
    # DIALOGS — Create/Edit forms
    # =========================================================================

    def open_create_plan_dialog(_=None):
        title_field = ft.TextField(label="Plan Title", autofocus=True)
        desc_field = ft.TextField(label="Description", multiline=True, max_lines=3)

        def save(_):
            if not title_field.value.strip():
                title_field.error_text = "Required"
                page.update()
                return
            result = api_post("/plans", {
                "title": title_field.value.strip(),
                "description": desc_field.value.strip() or None,
            })
            if result:
                page.close(dialog)
                load_plans()
                select_plan(result["id"])

        dialog = ft.AlertDialog(
            title=ft.Text("New Learning Plan"),
            content=ft.Column([title_field, desc_field], spacing=12, width=400, tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: page.close(dialog)),
                ft.ElevatedButton("Create", on_click=save),
            ],
        )
        page.open(dialog)

    def open_edit_plan_dialog():
        plan = state["current_plan"]
        title_field = ft.TextField(label="Plan Title", value=plan["title"], autofocus=True)
        desc_field = ft.TextField(label="Description", value=plan.get("description") or "", multiline=True)

        def save(_):
            if not title_field.value.strip():
                return
            api_put(f"/plans/{plan['id']}", {
                "title": title_field.value.strip(),
                "description": desc_field.value.strip() or None,
            })
            page.close(dialog)
            select_plan(plan["id"])
            load_plans()

        dialog = ft.AlertDialog(
            title=ft.Text("Edit Plan"),
            content=ft.Column([title_field, desc_field], spacing=12, width=400, tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: page.close(dialog)),
                ft.ElevatedButton("Save", on_click=save),
            ],
        )
        page.open(dialog)

    def confirm_delete_plan():
        plan = state["current_plan"]

        def do_delete(_):
            api_delete(f"/plans/{plan['id']}")
            page.close(dialog)
            state["current_plan"] = None
            state["current_plan_id"] = None
            main_content.controls = [render_welcome()]
            load_plans()
            page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Delete Plan?"),
            content=ft.Text(f'Delete "{plan["title"]}" and all its contents?'),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: page.close(dialog)),
                ft.ElevatedButton("Delete", style=ft.ButtonStyle(color=ft.Colors.RED), on_click=do_delete),
            ],
        )
        page.open(dialog)

    def open_add_goal_dialog():
        title_field = ft.TextField(label="Goal Title", autofocus=True)
        desc_field = ft.TextField(label="Description", multiline=True)

        def save(_):
            if not title_field.value.strip():
                return
            api_post(f"/plans/{state['current_plan_id']}/goals", {
                "title": title_field.value.strip(),
                "description": desc_field.value.strip() or None,
            })
            page.close(dialog)
            select_plan(state["current_plan_id"])

        dialog = ft.AlertDialog(
            title=ft.Text("New Goal"),
            content=ft.Column([title_field, desc_field], spacing=12, width=380, tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: page.close(dialog)),
                ft.ElevatedButton("Add Goal", on_click=save),
            ],
        )
        page.open(dialog)

    def open_edit_goal_dialog(goal: dict):
        title_field = ft.TextField(label="Goal Title", value=goal["title"], autofocus=True)
        desc_field = ft.TextField(label="Description", value=goal.get("description") or "", multiline=True)

        def save(_):
            if not title_field.value.strip():
                return
            api_put(f"/goals/{goal['id']}", {
                "title": title_field.value.strip(),
                "description": desc_field.value.strip() or None,
            })
            page.close(dialog)
            select_plan(state["current_plan_id"])

        dialog = ft.AlertDialog(
            title=ft.Text("Edit Goal"),
            content=ft.Column([title_field, desc_field], spacing=12, width=380, tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: page.close(dialog)),
                ft.ElevatedButton("Save", on_click=save),
            ],
        )
        page.open(dialog)

    def confirm_delete_goal(goal_id: int):
        def do_delete(_):
            api_delete(f"/goals/{goal_id}")
            page.close(dialog)
            select_plan(state["current_plan_id"])

        dialog = ft.AlertDialog(
            title=ft.Text("Delete Goal?"),
            content=ft.Text("This will also delete all subtasks and daily tasks."),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: page.close(dialog)),
                ft.ElevatedButton("Delete", style=ft.ButtonStyle(color=ft.Colors.RED), on_click=do_delete),
            ],
        )
        page.open(dialog)

    def open_add_subtask_dialog(goal_id: int):
        title_field = ft.TextField(label="Subtask Title", autofocus=True)
        desc_field = ft.TextField(label="Description", multiline=True)

        def save(_):
            if not title_field.value.strip():
                return
            api_post(f"/goals/{goal_id}/subtasks", {
                "title": title_field.value.strip(),
                "description": desc_field.value.strip() or None,
            })
            page.close(dialog)
            select_plan(state["current_plan_id"])

        dialog = ft.AlertDialog(
            title=ft.Text("New Subtask"),
            content=ft.Column([title_field, desc_field], spacing=12, width=380, tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: page.close(dialog)),
                ft.ElevatedButton("Add Subtask", on_click=save),
            ],
        )
        page.open(dialog)

    def open_edit_subtask_dialog(subtask: dict):
        title_field = ft.TextField(label="Subtask Title", value=subtask["title"], autofocus=True)
        desc_field = ft.TextField(label="Description", value=subtask.get("description") or "", multiline=True)

        def save(_):
            if not title_field.value.strip():
                return
            api_put(f"/subtasks/{subtask['id']}", {
                "title": title_field.value.strip(),
                "description": desc_field.value.strip() or None,
            })
            page.close(dialog)
            select_plan(state["current_plan_id"])

        dialog = ft.AlertDialog(
            title=ft.Text("Edit Subtask"),
            content=ft.Column([title_field, desc_field], spacing=12, width=380, tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: page.close(dialog)),
                ft.ElevatedButton("Save", on_click=save),
            ],
        )
        page.open(dialog)

    def confirm_delete_subtask(subtask_id: int):
        def do_delete(_):
            api_delete(f"/subtasks/{subtask_id}")
            page.close(dialog)
            select_plan(state["current_plan_id"])

        dialog = ft.AlertDialog(
            title=ft.Text("Delete Subtask?"),
            content=ft.Text("This will also delete all daily tasks."),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: page.close(dialog)),
                ft.ElevatedButton("Delete", style=ft.ButtonStyle(color=ft.Colors.RED), on_click=do_delete),
            ],
        )
        page.open(dialog)

    def open_add_task_dialog(subtask_id: int):
        title_field = ft.TextField(label="Task Title", autofocus=True)
        minutes_field = ft.TextField(label="Estimated Minutes", value="30", keyboard_type=ft.KeyboardType.NUMBER)

        def save(_):
            if not title_field.value.strip():
                return
            api_post(f"/subtasks/{subtask_id}/tasks", {
                "title": title_field.value.strip(),
                "estimated_minutes": int(minutes_field.value or 30),
            })
            page.close(dialog)
            select_plan(state["current_plan_id"])

        dialog = ft.AlertDialog(
            title=ft.Text("New Daily Task"),
            content=ft.Column([title_field, minutes_field], spacing=12, width=380, tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: page.close(dialog)),
                ft.ElevatedButton("Add Task", on_click=save),
            ],
        )
        page.open(dialog)

    def open_edit_task_dialog(task: dict):
        title_field = ft.TextField(label="Task Title", value=task["title"], autofocus=True)
        minutes_field = ft.TextField(
            label="Estimated Minutes",
            value=str(task["estimated_minutes"]),
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        notes_field = ft.TextField(
            label="Progress Notes",
            value=task.get("notes") or "",
            multiline=True,
            hint_text="How did it go? What did you learn?",
        )

        def save(_):
            if not title_field.value.strip():
                return
            api_put(f"/tasks/{task['id']}", {
                "title": title_field.value.strip(),
                "estimated_minutes": int(minutes_field.value or 30),
                "notes": notes_field.value.strip() or None,
            })
            page.close(dialog)
            select_plan(state["current_plan_id"])

        dialog = ft.AlertDialog(
            title=ft.Text("Edit Task"),
            content=ft.Column([title_field, minutes_field, notes_field], spacing=12, width=400, tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: page.close(dialog)),
                ft.ElevatedButton("Save", on_click=save),
            ],
        )
        page.open(dialog)

    # =========================================================================
    # WELCOME SCREEN
    # =========================================================================

    def render_welcome() -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Text("📚", size=64),
                ft.Text("Welcome to LearningGuide", size=28, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Plan your learning journey with goals, subtasks, and daily tasks.",
                    size=15,
                    color=ft.Colors.GREY_600,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Row([
                    ft.ElevatedButton(
                        "Create a Plan",
                        icon=ft.Icons.ADD,
                        on_click=open_create_plan_dialog,
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Text(
                    "Note: Requires the web backend to be running.\n"
                    "Run: cd web/backend && uvicorn main:app --reload",
                    size=12,
                    color=ft.Colors.GREY_500,
                    text_align=ft.TextAlign.CENTER,
                    italic=True,
                ),
            ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=16,
            ),
            alignment=ft.alignment.center,
            expand=True,
        )

    # =========================================================================
    # PAGE LAYOUT ASSEMBLY
    # =========================================================================

    # Initialize main content with welcome screen
    main_content.controls = [render_welcome(), connection_error]

    # Top app bar
    app_bar = ft.AppBar(
        leading=ft.Icon(ft.Icons.MENU_BOOK, color=ft.Colors.WHITE),
        leading_width=48,
        title=ft.Text("LearningGuide", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.BLUE_700,
        actions=[
            ft.IconButton(
                ft.Icons.ADD,
                tooltip="New Plan",
                icon_color=ft.Colors.WHITE,
                on_click=open_create_plan_dialog,
            ),
            ft.IconButton(
                ft.Icons.BRIGHTNESS_6,
                tooltip="Toggle Dark Mode",
                icon_color=ft.Colors.WHITE,
                on_click=lambda _: toggle_theme(),
            ),
        ],
    )
    page.appbar = app_bar

    def toggle_theme():
        page.theme_mode = (
            ft.ThemeMode.DARK
            if page.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        page.update()

    # Sidebar
    sidebar = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Text("MY PLANS", size=11, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_500),
                    ft.IconButton(
                        ft.Icons.ADD,
                        tooltip="New Plan",
                        icon_size=18,
                        on_click=open_create_plan_dialog,
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.symmetric(horizontal=8),
            ),
            ft.Divider(height=1),
            plan_list_view,
        ], spacing=4),
        width=220,
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
        border=ft.border.only(right=ft.BorderSide(1, ft.Colors.GREY_200)),
        padding=ft.padding.symmetric(vertical=12),
    )

    # Full page layout
    page.add(
        ft.Row([
            sidebar,
            ft.VerticalDivider(width=1),
            ft.Container(content=main_content, expand=True),
        ], expand=True, spacing=0)
    )

    # Load initial data
    load_plans()


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    ft.app(target=main)
