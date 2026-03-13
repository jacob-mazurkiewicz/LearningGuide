# 📚 LearningGuide

**LearningGuide** is an app that helps you plan, track, and accomplish learning goals — whether you're learning a coding language, exploring a math concept, or building a personal project.

You create a hierarchy of:
- **Overall Goals** — e.g. *"Learn Python"* or *"Build a Data Dashboard"*
- **Subtasks** — the major milestones that make up the goal
- **Daily Tasks** — concrete, bite-sized actions you schedule day-by-day

Drag items around to build a rough timeline, check off tasks as you complete them, and watch your progress bars grow. You can also let an **AI model** generate the entire plan for you!

---

## 🗂️ Repository Structure

```
LearningGuide/
├── web/          # 🌐 Web App  (FastAPI backend + HTML/CSS/JS frontend)
├── desktop/      # 🖥️  Desktop App (Python + Flet — runs natively or as a web app)
└── docs/         # 📄 Additional documentation and guides
```

> Both apps share the same concept and data model, but the **web app** is the primary version and runs in your browser. The **desktop app** is a standalone Python application that wraps the same features in a native window.

---

## 🚀 Quick Start

### Web App (Recommended)

```bash
cd web/backend
pip install -r requirements.txt
cp .env.example .env          # optional: add AI API keys here
uvicorn main:app --reload     # starts server on http://localhost:8000
```

Then open **http://localhost:8000** in your browser.

### Desktop App

```bash
cd desktop
pip install -r requirements.txt
python app.py
```

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📋 Manual Planning | Create goals, subtasks, and daily tasks by hand |
| 🤖 AI Generation | Let an AI model build the full plan from a single sentence |
| 🗂️ Drag & Drop | Reorder any item to reshape your timeline |
| ✅ Progress Tracking | Check off daily tasks; watch progress bars fill up |
| 📝 Notes | Add free-form notes to any task |
| 💾 Persistent Storage | Everything is saved in a local SQLite database |

---

## 🤖 AI Integration

The AI feature is **optional** — the app works fully without it.

Supported providers (all have **free tiers**):

| Provider | How to get a key | Speed |
|----------|-----------------|-------|
| [Groq](https://console.groq.com) | Sign up → API Keys | ⚡ Very fast |
| [OpenAI](https://platform.openai.com) | Sign up → API Keys | Fast |
| [Ollama](https://ollama.com) | Install locally, no key needed | Medium (local) |

Set the key in `web/backend/.env` (see `.env.example`).

---

## 📖 Documentation

- [Getting Started Guide](docs/getting-started.md)
- [Web Backend README](web/backend/README.md)
- [Web Frontend README](web/frontend/README.md)
- [Desktop App README](desktop/README.md)

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Web Backend | Python + FastAPI | Fast, modern, easy to learn |
| Database | SQLite + SQLAlchemy | Zero-config, file-based, great ORM |
| Web Frontend | HTML5 + CSS3 + Vanilla JS | No build step — just open and edit |
| Desktop App | Python + Flet | Pure Python, beautiful Material UI |
| AI | Groq / OpenAI / Ollama | Free tiers, simple API |

---

## 📁 Learning Notes

This project is designed to be **read and understood** as you iterate on it. Every file has comments explaining *what* is happening and *why*. Start with the [Getting Started Guide](docs/getting-started.md) and work your way through.
