import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager
from database.db import engine, SessionLocal
from models.models import User
from services.auth_service import hash_password
from routes.auth_routes import router as auth_router
from routes.route_routes import router as route_router
from routes.simulation_routes import router as sim_router, admin_router
from utils.config import settings
from utils.observability import RequestLoggingMiddleware, configure_logging

configure_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tables are managed by Alembic. An initial admin is opt-in through environment variables.
    db = SessionLocal()
    try:
        if settings.INITIAL_ADMIN_EMAIL and settings.INITIAL_ADMIN_PASSWORD and not db.query(User).filter(User.email == settings.INITIAL_ADMIN_EMAIL).first():
            admin = User(
                email=settings.INITIAL_ADMIN_EMAIL,
                username="admin",
                full_name="Admin User",
                hashed_password=hash_password(settings.INITIAL_ADMIN_PASSWORD),
                role="admin",
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()
    yield

app = FastAPI(
    title="QuantumRoute AI API",
    description="Quantum-Assisted Intelligent Route Optimization System",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(auth_router, prefix="/api")
app.include_router(route_router, prefix="/api")
app.include_router(sim_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(request: Request, exc: SQLAlchemyError):
    logging.getLogger("quantumroute.error").exception("database_error", exc_info=exc)
    return JSONResponse(status_code=503, content={"detail": "Database service unavailable"})


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception):
    logging.getLogger("quantumroute.error").exception("unexpected_error", exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

@app.get("/api/health")
def health():
    database_status = "unavailable"
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database_status = "healthy"
    except Exception:
        pass
    try:
        from qiskit_aer import AerSimulator
        quantum_backend = AerSimulator().name
    except Exception:
        quantum_backend = None
    return {
        "status": "healthy" if database_status == "healthy" else "degraded",
        "service": "QuantumRoute AI",
        "version": "2.0.0",
        "database": database_status,
        "quantum_backend": quantum_backend,
    }
