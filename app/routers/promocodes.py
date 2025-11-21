from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from jose import jwt

from ..database import get_db
from ..auth import SECRET_KEY, ALGORITHM
from .. import crud, schemas, models   # VERY IMPORTANT

router = APIRouter(prefix="/promocodes", tags=["Promo Codes"])
oauth2 = OAuth2PasswordBearer(tokenUrl="/token")


# Helper to decode token (same as products router)
def get_payload(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None


# ============================
#  Create Promo Code
# ============================

@router.post("/create")
def create_promocode(
    data: schemas.PromoCodeCreate,
    token: str = Depends(oauth2),
    db: Session = Depends(get_db)
):
    payload = get_payload(token)
    if not payload or payload.get("role") != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")

    return crud.create_promocode(db, data)

# ============================
#  Apply Promo Code
# ============================

@router.get("/apply/{code}")
def apply_promocode(
    code: str,
    cart_total: float,
    db: Session = Depends(get_db)
):
    result = crud.apply_promocode(db, code, cart_total)

    if result is None:
        raise HTTPException(status_code=400, detail="Invalid or expired promo code")

    if result == "min_amount":
        raise HTTPException(status_code=400, detail="Order below minimum amount")

    return {"discount": result}


# ============================
#  Update Promo Code
# ============================

@router.put("/update/{promo_id}")
def update_promo(
    promo_id: int,
    data: schemas.PromoUpdate,
    token: str = Depends(oauth2),
    db: Session = Depends(get_db)
):
    # Validate manager role
    payload = get_payload(token)
    if not payload or payload.get("role") != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")

    #  Import from models via "models.PromoCode"
    PromoCode = models.PromoCode

    promo = db.query(PromoCode).filter(PromoCode.id == promo_id).first()

    if not promo:
        raise HTTPException(status_code=404, detail="Promo code not found")

    # If code is updated, check uniqueness
    if data.code:
        existing = db.query(PromoCode).filter(
            PromoCode.code == data.code,
            PromoCode.id != promo_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Code already exists")
        promo.code = data.code

    if data.discount_percent is not None:
        if not (1 <= data.discount_percent <= 90):
            raise HTTPException(status_code=400, detail="Discount must be between 1 and 90")
        promo.discount_percent = data.discount_percent

    if data.expires_at:
        promo.expires_at = data.expires_at

    if data.min_order_amount is not None:
        if data.min_order_amount < 0:
            raise HTTPException(status_code=400, detail="min_order_amount cannot be negative")
        promo.min_order_amount = data.min_order_amount

    if data.active is not None:
        promo.active = data.active

    db.commit()
    db.refresh(promo)

    return {
        "message": "Promo code updated",
        "promo": {
            "id": promo.id,
            "code": promo.code,
            "discount_percent": promo.discount_percent,
            "expires_at": promo.expires_at,
            "min_order_amount": promo.min_order_amount,
            "active": promo.active
        }
    }
