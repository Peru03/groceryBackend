# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

settings = get_settings()

# ---------- Engine ----------
# - future=True uses SQLAlchemy 2.0 style
# - echo=False: disable verbose SQL logging in production (enable in dev via env)
# - pool_pre_ping=True helps with dropped/long-lived connections (useful in containers)
# - pool_size/max_overflow tuned for modest production usage; adjust to your infra
engine = create_engine(
    settings.DATABASE_URL,
    future=True,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# ---------- Session factory ----------
# - expire_on_commit=False keeps objects usable after commit (convenient for services)
# - autoflush=False / autocommit=False are typical defaults for explicit control
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

# ---------- FastAPI dependency ----------
def get_db():
    """
    Use this dependency in your routers:

        def endpoint(db: Session = Depends(get_db)):
            ...

    It yields a DB session and ensures it's closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
