# HRMS Agent — AI-Powered HR Management System

An agentic HRMS assistant built with **FastAPI + OpenAI + React**, fully containerized with **Docker**.

---

## Features

| Feature              | Description                                           |
|----------------------|-------------------------------------------------------|
| Employee Lookup      | Search by name or employee code                       |
| Leave Management     | View, apply, and track leave requests                 |
| Attendance Tracking  | Check daily attendance records                        |
| Payroll Details      | View monthly salary breakdowns                        |
| Company Statistics   | Department headcount, average salary, and more        |
| Chat Interface       | Natural language queries via React chat UI            |
| Tool Calling         | Agent selects and executes the right HRMS tool        |
| Session Memory       | Remembers conversation context within a session       |

---

## Architecture

```
┌────────────┐         ┌──────────────┐         ┌──────────┐
│   React UI │ ──────> │  FastAPI     │ ──────> │  OpenAI  │
│  (port 3000)│ <────── │  Backend     │ <────── │  API     │
└────────────┘         │  (port 8000) │         └──────────┘
                       │              │
                       │  SQLite DB   │
                       │  HRMS Tools  │
                       └──────────────┘
```

---

## Quick Start (Docker)

### 1. Set your API key
Edit `backend/.env`:
```
OPENAI_API_KEY=sk-your-key-here
```

### 2. Build and run
```bash
docker-compose up --build
```

### 3. Open the app
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Health check: http://localhost:8000/health

---

## Quick Start (Without Docker)

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1    # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm start
```

---

## Sample Queries

Try these in the chat:
- "Show me all employees"
- "What is the attendance for EMP001 on 2026-02-14?"
- "Apply casual leave for EMP003 from 2026-03-10 to 2026-03-12 for personal work"
- "Show payroll for EMP005 for January 2026"
- "How many employees are in Engineering?"
- "Give me company HR statistics"

---

## Available HRMS Tools

| Tool                         | Purpose                                  |
|------------------------------|------------------------------------------|
| `lookup_employee`            | Find employee by code or name            |
| `list_employees_by_department` | List all employees in a department     |
| `get_leave_records`          | View leave history for an employee       |
| `apply_leave`                | Submit a new leave request               |
| `get_attendance`             | Check attendance records                 |
| `get_payroll`                | View salary slip for a month             |
| `get_company_stats`          | Overall HR statistics                    |

---

## Project Structure

```
Project/
├── docker-compose.yml
├── .gitignore
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env
│   ├── .env.example
│   └── app/
│       ├── __init__.py
│       ├── main.py           # FastAPI app + routes
│       ├── agent.py          # LLM agent with tool calling
│       ├── tools.py          # HRMS tool definitions + implementations
│       ├── models.py         # Pydantic + SQLAlchemy models
│       ├── database.py       # DB engine + session
│       └── seed_data.py      # Demo data seeder
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    ├── public/
    │   └── index.html
    └── src/
        ├── index.js
        ├── App.js
        ├── App.css
        ├── api.js
        └── components/
            ├── ChatPanel.js
            ├── Sidebar.js
            └── MessageBubble.js
```

---

## Tech Stack

- **Backend:** Python 3.12, FastAPI, OpenAI SDK, SQLAlchemy, SQLite
- **Frontend:** React 18, Axios, React Markdown, React Icons
- **Containerization:** Docker, Docker Compose, Nginx
- **AI:** OpenAI GPT with function/tool calling

---

## License
For educational use as part of the Agentic AI Developer Course.
