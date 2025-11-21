from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from typing import List
from .. import schemas, crud, models
from ..database import get_db
from ..auth import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/wishlist", tags=["wishlist"])
oauth2 = OAuth2PasswordBearer(tokenUrl="/token")


def get_payload(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None


# -----------------------------
# Add to wishlist
# -----------------------------
@router.post("/", response_model=schemas.WishlistItemOut)
def add_to_wishlist(
    item: schemas.WishlistItemCreate,
    token: str = Depends(oauth2),
    db: Session = Depends(get_db)
):
    payload = get_payload(token)
    if not payload or payload.get("role") != "customer":
        raise HTTPException(status_code=403, detail="Customer required")

    wishlist_item = crud.add_to_wishlist(db, payload.get("user_id"), item.product_id)
    return wishlist_item


# -----------------------------
# Get wishlist
# -----------------------------
@router.get("/", response_model=List[schemas.WishlistItemOut])
def get_wishlist(
    token: str = Depends(oauth2),
    db: Session = Depends(get_db)
):
    payload = get_payload(token)
    if not payload or payload.get("role") != "customer":
        raise HTTPException(status_code=403, detail="Customer required")

    return crud.get_wishlist(db, payload.get("user_id"))


# -----------------------------
# Remove wishlist item
# -----------------------------
@router.delete("/{wishlist_item_id}")
def remove_wishlist_item(
    wishlist_item_id: int,
    token: str = Depends(oauth2),
    db: Session = Depends(get_db)
):
    payload = get_payload(token)
    if not payload or payload.get("role") != "customer":
        raise HTTPException(status_code=403, detail="Customer required")

    item = db.query(models.WishlistItem).get(wishlist_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")

    # ensure user can only delete their own item
    if item.user_id != payload.get("user_id"):
        raise HTTPException(status_code=403, detail="Not allowed")

    db.delete(item)
    db.commit()
    return {"detail": "removed"}
