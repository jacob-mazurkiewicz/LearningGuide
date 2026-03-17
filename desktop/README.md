# 🖥️ Desktop App — Python + Flet

The desktop app is built with **Flet**, a Python framework that creates beautiful
native desktop applications using Flutter's rendering engine.

## Prerequisites

The desktop app connects to the web backend for data storage. You need to:
1. Start the web backend first (see `web/README.md`)
2. Then run the desktop app

## How to Run

```bash
# Terminal 1: Start the web backend
cd web/backend
uvicorn main:app --reload

# Terminal 2: Start the desktop app
cd desktop
pip install -r requirements.txt
python app.py
```

## Alternative: Run as a Web App

Flet apps can also run in the browser:

```bash
cd desktop
flet run --web app.py
# Opens at http://localhost:8550
```

## Files

| File | Purpose |
|------|---------|
| `app.py` | The entire desktop app — layout, components, API calls |
| `requirements.txt` | Python dependencies (flet, httpx) |

## Flet Concepts

### Controls
Everything visible in a Flet app is a "control":

```python
# Text
ft.Text("Hello, World!", size=20, weight=ft.FontWeight.BOLD)

# Button
ft.ElevatedButton("Click me", on_click=my_function)

# Layout containers
ft.Row([control1, control2])      # Side by side
ft.Column([control1, control2])   # Stacked
ft.Container(content=control, padding=12, bgcolor=ft.Colors.BLUE_50)
```

### Page and Updates
The `page` object is the app window. You call `page.update()` to refresh after changes:

```python
def main(page: ft.Page):
    counter = ft.Text("0")
    page.add(counter)

    def increment(_):
        counter.value = str(int(counter.value) + 1)
        page.update()  # Must call this to see changes!

    page.add(ft.ElevatedButton("Click", on_click=increment))
```

### Dialogs
Flet uses `ft.AlertDialog` for popup dialogs:

```python
dialog = ft.AlertDialog(
    title=ft.Text("Confirm?"),
    content=ft.Text("Are you sure?"),
    actions=[
        ft.TextButton("No", on_click=lambda _: page.close(dialog)),
        ft.ElevatedButton("Yes", on_click=do_action),
    ]
)
page.open(dialog)
```

## Architecture Note

The desktop app doesn't have its own database — it talks to the FastAPI web backend
via HTTP (using the `httpx` library). This means:

- The same data is shared between the web and desktop apps
- All business logic lives in the backend
- The desktop app is purely a "view" layer

If you wanted a standalone desktop app (without the web backend), you could:
1. Copy `database.py` and `models.py` from the web backend
2. Create SQLAlchemy sessions directly in `app.py`
3. Remove the `httpx` HTTP calls and replace with direct DB queries

## Learning Topics

| Concept | Where to see it |
|---------|----------------|
| Flet layouts (Row, Column, Container) | `create_goal_card()` function |
| Flet controls (Text, Button, Checkbox) | `create_task_row()` function |
| Dialog popups | `open_add_goal_dialog()` function |
| State management | `state` dict in `main()` |
| HTTP client (httpx) | `api_get/post/put/delete` functions |
