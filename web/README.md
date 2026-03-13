# 🌐 Web App

The web version of LearningGuide runs entirely in your browser and is powered by a Python backend.

## How to Run

```bash
# 1. Install Python dependencies
cd web/backend
pip install -r requirements.txt

# 2. (Optional) Configure AI
cp .env.example .env
# Edit .env and add your GROQ_API_KEY or OPENAI_API_KEY

# 3. Start the server
uvicorn main:app --reload

# 4. Open your browser
# → http://localhost:8000
```

The `--reload` flag makes the server automatically restart whenever you edit a Python file.
To see frontend changes (HTML/CSS/JS), just refresh your browser.

## Folder Structure

```
web/
├── backend/           # Python API server
│   ├── main.py        # All API routes — start reading here
│   ├── models.py      # Database table definitions
│   ├── schemas.py     # Data validation shapes
│   ├── database.py    # Database connection
│   ├── ai_service.py  # AI plan generation
│   └── tests/         # Automated tests
└── frontend/          # Browser-side files
    ├── index.html     # The single HTML page
    ├── style.css      # Custom styles
    └── app.js         # All frontend logic
```

## Architecture Diagram

```
Browser (HTML + CSS + JS)
       ↕ HTTP requests (fetch)
FastAPI Server (Python)
       ↕ SQL queries
SQLite Database (file: learningguide.db)
       ↕ optional
AI Provider (Groq / OpenAI / Ollama)
```

## Running Tests

```bash
cd web/backend
pytest tests/ -v         # Run all tests
pytest tests/ -v -k plan # Run only plan-related tests
```

## API Documentation

When the server is running, visit **http://localhost:8000/docs** for interactive API docs.
You can try out every endpoint directly from your browser — no Postman needed!

## Key Learning Topics

| File | Concepts |
|------|---------|
| `backend/main.py` | HTTP methods, REST APIs, FastAPI routes, dependency injection |
| `backend/models.py` | Database design, ORM, foreign keys, relationships |
| `backend/schemas.py` | Data validation, Pydantic, request/response design |
| `frontend/app.js` | DOM manipulation, async/await, fetch API, event-driven programming |
| `frontend/index.html` | HTML structure, Bootstrap components, modals, forms |
