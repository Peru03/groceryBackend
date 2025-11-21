from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from typing import List, Optional
from .. import schemas, crud
from ..database import get_db
from ..auth import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/orders", tags=["orders"])
oauth2 = OAuth2PasswordBearer(tokenUrl="/token")


def get_payload(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None


@router.post("/checkout", response_model=schemas.OrderOut)
def checkout(
    promo_code: str = None,
    token: str = Depends(oauth2),
    db: Session = Depends(get_db)
):
    payload = get_payload(token)
    if not payload or payload.get("role") != "customer":
        raise HTTPException(status_code=403, detail="Customer required")

    user_id = payload.get("user_id")

    try:
        # calculate total and check stock
        cart_items = crud.get_cart_items(db, user_id)
        if not cart_items:
            raise HTTPException(status_code=400, detail="Cart is empty")

        total = 0
        for ci in cart_items:
            product = crud.get_product(db, ci.product_id)
            if product.stock < ci.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for '{product.name}'"
                )
            total += product.price * ci.quantity

        # Apply promo code (IF given)
        discount = 0
        if promo_code:
            promo_result = crud.apply_promocode(db, promo_code, total)

            if promo_result is None:
                raise HTTPException(status_code=400, detail="Invalid or expired promo code")
            if promo_result == "min_amount":
                raise HTTPException(status_code=400, detail="Order does not meet minimum amount")

            discount = promo_result
            total -= discount

        # Create order
        order = crud.create_order(db, user_id, total, cart_items)

        return {
            "id": order.id,
            "total_amount": order.total_amount,
            "discount_applied": discount,
            "created_at": order.created_at,
            "items": [
                {
                    "product_id": oi.product_id,
                    "quantity": oi.quantity,
                    "price_at_purchase": oi.price_at_purchase
                }
                for oi in order.items
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
