from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import crud
from ..auth import SECRET_KEY, ALGORITHM
from fastapi.security import OAuth2PasswordBearer
from jose import jwt


router = APIRouter(prefix="/inventory", tags=["Inventory"])
oauth2 = OAuth2PasswordBearer(tokenUrl="/token")


@router.get("/low-stock")
def low_stock_products(
    threshold: int = 5,
    token: str = Depends(oauth2),
    db: Session = Depends(get_db)
):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    # Manager check
    if payload.get("role") != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")

    items = crud.low_stock_products(db, threshold)
    return items
