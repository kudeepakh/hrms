"""
FastAPI application — HRMS Agent backend (Clean Architecture).

Lifespan:
    - Connects to MongoDB via Beanie on startup
    - Seeds demo data
    - Closes connection on shutdown
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.database.mongodb import connect_db, close_db
from app.database.seed import seed_database
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.logging_middleware import LoggingMiddleware
from app.routes.health import router as health_router
from app.routes.auth import router as auth_router
from app.routes.chat import router as chat_router
from app.routes.employees import router as employees_router
from app.routes.uploads import router as uploads_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("hrms")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info("Starting HRMS Agent …")
    await connect_db()
    await seed_database()
    logger.info("HRMS Agent ready.")
    yield
    logger.info("Shutting down HRMS Agent …")
    await close_db()


app = FastAPI(
    title="HRMS Agent API",
    description="AI-powered Human Resource Management System with RBAC, SSO, and chat-driven management.",
    version="2.0.0",
    lifespan=lifespan,
)

# ------------------------------------------------------------------
# Middleware (order matters — outermost first)
# ------------------------------------------------------------------
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.JWT_SECRET,
)

# ------------------------------------------------------------------
# Routers
# ------------------------------------------------------------------
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(employees_router)
app.include_router(uploads_router)

