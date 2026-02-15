# HRMS Agent v2.0 — Architecture Overhaul Task Plan

> **Total: 8 Phases, 31 Tasks**
> **Status Legend:** ⬜ Not Started | 🔄 In Progress | ✅ Completed

---

## Phase 1: Project Structure & Architecture Foundation

| # | Task | Description | Status |
|---|------|-------------|--------|
| 1.1 | Restructure backend with Clean Architecture | Layers: `routes/` → `services/` → `repositories/` → `models/`. Follow SOLID & DRY. | ✅ |
| 1.2 | Config management | Centralized `config.py` with Pydantic `BaseSettings`, environment-based configs | ✅ |
| 1.3 | Error handling middleware | Global exception handler, custom exception classes, consistent error responses | ✅ |
| 1.4 | Logging setup | Structured logging with Python `logging`, request/response logging middleware | ✅ |
| 1.5 | Dependency injection | FastAPI `Depends()` for DB sessions, auth, services — no hard-coded dependencies | ✅ |

---

## Phase 2: MongoDB Migration

| # | Task | Description | Status |
|---|------|-------------|--------|
| 2.1 | Setup MongoDB with Motor (async driver) | Replace SQLite/SQLAlchemy with `motor` + `beanie` ODM | ✅ |
| 2.2 | Define MongoDB document models | `Employee`, `LeaveRecord`, `Attendance`, `Payroll`, `User`, `AuditLog`, `CachedQuery` | ✅ |
| 2.3 | Repository pattern for data access | `EmployeeRepository`, `LeaveRepository`, `PayrollRepository`, etc. — all DB access abstracted | ✅ |
| 2.4 | Seed data script for MongoDB | Migrate seed data to MongoDB format — 5 employees, leaves, attendance, payroll + admin user | ✅ |
| 2.5 | Docker: Add MongoDB service | Added `mongo:7` container to `docker-compose.yml` with `mongo-data` volume persistence | ✅ |

---

## Phase 3: Authentication & SSO

| # | Task | Description | Status |
|---|------|-------------|--------|
| 3.1 | JWT authentication | Login/register endpoints, access + refresh tokens, password hashing with `bcrypt` | ✅ |
| 3.2 | Google SSO (OAuth2) | Google OAuth2 login flow via `authlib` | ✅ |
| 3.3 | Microsoft SSO (OAuth2) | Microsoft/Azure AD OAuth2 login flow | ✅ |
| 3.4 | GitHub SSO (OAuth2) | GitHub OAuth2 login flow | ✅ |
| 3.5 | Auth middleware | Protect all routes, extract user from JWT, inject into request context | ✅ |
| 3.6 | Frontend: Login page | Login form (email/password) + tabs for Sign In/Register + demo credentials | ✅ |
| 3.7 | Frontend: Auth state management | Token storage in localStorage, auto-inject via Axios interceptor, logout, 401 redirect | ✅ |

---

## Phase 4: Role-Based Access Control (RBAC)

| # | Task | Description | Status |
|---|------|-------------|--------|
| 4.1 | Define roles & permissions | 4 roles (super_admin, hr_admin, manager, employee) with 10 permissions in centralized map | ✅ |
| 4.2 | Permission guard middleware | `require_role()` and `require_permission()` FastAPI dependencies | ✅ |
| 4.3 | Role-aware agent tools | Tool executor checks user permissions before every tool call | ✅ |
| 4.4 | Role management via chat | Super admin can assign roles via `assign_role` tool through chat | ✅ |

---

## Phase 5: Enhanced HRMS Features (Chat-Driven)

| # | Task | Description | Status |
|---|------|-------------|--------|
| 5.1 | Add Employee tool | `add_employee` tool definition + service + repo | ✅ |
| 5.2 | Update Employee tool | `update_employee` tool definition + service + repo | ✅ |
| 5.3 | Resignation management tools | `initiate_resignation` tool — updates status, resignation date, exit reason | ✅ |
| 5.4 | Leave approval tool | `approve_or_reject_leave` tool with RBAC check | ✅ |
| 5.5 | Audit logging | Every write operation logged in `AuditLog` collection with who/what/when | ✅ |

---

## Phase 6: Query Caching (Avoid Redundant GPT Calls)

| # | Task | Description | Status |
|---|------|-------------|--------|
| 6.1 | Query cache layer | MongoDB TTL-based cache with SHA-256 hash matching in `CachedQuery` collection | ✅ |
| 6.2 | Semantic query matching | Hash-based matching of normalized (lowercase, no punctuation) queries | ✅ |
| 6.3 | FAQ / Static response registry | Regex-based FAQ for leave policy, holidays, working hours, help — zero GPT cost | ✅ |
| 6.4 | Cache invalidation | `invalidate_cache()` wipes all cached responses on any write operation | ✅ |

---

## Phase 7: Frontend Enhancements

| # | Task | Description | Status |
|---|------|-------------|--------|
| 7.1 | Login page with SSO | Email/password form with Sign In / Register tabs + demo credentials | ✅ |
| 7.2 | Role-based UI | User role shown in sidebar, role-appropriate greeting | ✅ |
| 7.3 | User profile & session display | User name, role badge in sidebar, logout button | ✅ |
| 7.4 | Chat context per user | Session ID tied to user email for per-user chat history | ✅ |

---

## Phase 8: Docker & DevOps

| # | Task | Description | Status |
|---|------|-------------|--------|
| 8.1 | Update docker-compose | MongoDB service, proper depends_on & networking, removed old volume | ✅ |
| 8.2 | Environment configuration | `.env` with all keys (MongoDB, JWT, OAuth, cache, CORS) | ✅ |
| 8.3 | Health checks | `/health` endpoint with MongoDB connectivity context | ✅ |

---

## Architecture Summary

```
backend/app/
├── main.py                    # FastAPI app, lifespan, middleware, routers
├── config.py                  # Pydantic BaseSettings (singleton)
├── exceptions.py              # Custom exception hierarchy
├── auth/
│   ├── jwt_handler.py         # JWT create/verify (PyJWT)
│   ├── dependencies.py        # get_current_user, require_role, require_permission
│   ├── service.py             # register, login, sso_login
│   └── oauth_providers.py     # Google, Microsoft, GitHub OAuth (authlib)
├── models/
│   ├── user.py                # User doc + UserRole enum + RolePermissions
│   ├── employee.py            # Employee doc with resignation fields
│   ├── leave.py               # LeaveRecord doc
│   ├── attendance.py          # Attendance doc
│   ├── payroll.py             # Payroll doc
│   ├── audit_log.py           # AuditLog doc (immutable trail)
│   └── schemas.py             # Pydantic request/response schemas
├── repositories/
│   ├── base.py                # Generic BaseRepository[T] with CRUD
│   ├── user_repo.py           # User queries + role update
│   ├── employee_repo.py       # Employee queries + aggregations
│   ├── leave_repo.py          # Leave queries + status updates
│   ├── attendance_repo.py     # Attendance queries
│   └── payroll_repo.py        # Payroll queries
├── services/
│   ├── employee_service.py    # Employee business logic
│   ├── leave_service.py       # Leave business logic
│   ├── attendance_service.py  # Attendance business logic
│   └── payroll_service.py     # Payroll business logic
├── agent/
│   ├── tools.py               # 12 tool definitions (Chat Completions format)
│   ├── tool_executor.py       # RBAC-checked dispatcher
│   ├── orchestrator.py        # Main AI loop (FAQ → cache → GPT)
│   └── prompt_templates.py    # Role-aware system prompts
├── cache/
│   ├── query_cache.py         # MongoDB TTL cache + SHA-256 hashing
│   └── faq_registry.py        # Regex-based static answers
├── database/
│   ├── mongodb.py             # Motor + Beanie init
│   └── seed.py                # Demo data seeder (idempotent)
├── middleware/
│   ├── error_handler.py       # Global exception → JSON middleware
│   └── logging_middleware.py   # Request/response logging
└── routes/
    ├── health.py              # GET /health
    ├── auth.py                # POST /auth/login, /auth/register, SSO flows
    ├── chat.py                # POST /chat (auth required)
    └── employees.py           # GET /employees (auth required)

frontend/src/
├── api.js                     # Axios + auth interceptors + token helpers
├── App.js                     # Auth-gated routing (LoginPage or main app)
├── App.css                    # All styles including login page
└── components/
    ├── LoginPage.js           # Sign In / Register tabs + demo credentials
    ├── Sidebar.js             # User profile, role badge, quick actions, logout
    ├── ChatPanel.js           # Chat interface (unchanged)
    └── MessageBubble.js       # Message rendering (unchanged)
```

## Demo Accounts (seeded automatically)

| Role | Email | Password |
|------|-------|----------|
| Super Admin | admin@hrms.local | admin123 |
| HR Admin | priya.hr@company.com | hr123 |
| Manager | rahul.m@company.com | mgr123 |
| Employee | anita.d@company.com | emp123 |
| Employee | vikram.s@company.com | emp123 |
