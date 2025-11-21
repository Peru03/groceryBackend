from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from .. import schemas, crud
from ..database import get_db
from ..auth import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/cart", tags=["cart"])
oauth2 = OAuth2PasswordBearer(tokenUrl="/token")


def get_payload(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None


@router.post("/", response_model=schemas.CartItemOut)
def add_to_cart(item: schemas.CartItemCreate, token: str = Depends(oauth2), db: Session = Depends(get_db)):
    payload = get_payload(token)
    if not payload or payload.get("role") != "customer":
        raise HTTPException(status_code=403, detail="Customer required")
    return crud.add_to_cart(db, payload.get("user_id"), item.product_id, item.quantity)


@router.get("/", response_model=List[schemas.CartItemOut])
def get_cart(token: str = Depends(oauth2), db: Session = Depends(get_db)):
    payload = get_payload(token)
    if not payload or payload.get("role") != "customer":
        raise HTTPException(status_code=403, detail="Customer required")
    return crud.get_cart_items(db, payload.get("user_id"))


@router.delete("/{cart_item_id}")
def remove_cart(cart_item_id: int, token: str = Depends(oauth2), db: Session = Depends(get_db)):
    payload = get_payload(token)
    if not payload or payload.get("role") != "customer":
        raise HTTPException(status_code=403, detail="Customer required")
    ok = crud.remove_cart_item(db, cart_item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return {"detail": "removed"}
