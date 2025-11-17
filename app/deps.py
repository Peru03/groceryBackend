from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import crud, models
from jose import jwt, JWTError
from .schemas import TokenData
from .auth import SECRET_KEY, ALGORITHM

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(lambda: None), db: Session = Depends(get_db)):
    # We'll use FastAPI's OAuth2PasswordBearer in main with dependency injection.
    raise NotImplementedError("Use get_current_active_user from main's auth wrapper")
