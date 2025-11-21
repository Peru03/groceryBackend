import os
from fastapi import APIRouter, Depends, HTTPException , File, UploadFile, Form
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from .. import schemas, crud
from ..database import get_db
from ..auth import SECRET_KEY, ALGORITHM


router = APIRouter(prefix="/products", tags=["products"])
oauth2 = OAuth2PasswordBearer(tokenUrl="/token")


def get_payload(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None
    


#  PRODUCT


@router.post("/", response_model=schemas.ProductOut)
def create_product(
    name: str = Form(...),
    category: str = Form(None),
    price: float = Form(...),
    stock: int = Form(...),
    image: UploadFile = File(None),
    token: str = Depends(oauth2),
    db: Session = Depends(get_db)
):

    payload = get_payload(token)
    if not payload or payload.get("role") != "manager":
        raise HTTPException(status_code=403, detail="Manager required")

    # ---------- CREATE UPLOAD FOLDER IF NOT EXISTS ----------
    UPLOAD_DIR = "uploads"
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # ---------- SAVE IMAGE IF PROVIDED ----------
    image_url = None
    if image is not None:
        file_location = os.path.join(UPLOAD_DIR, image.filename)
        with open(file_location, "wb") as f:
            f.write(image.file.read())
        image_url = file_location
        
        # Convert Windows path → URL path
        image_url = file_location.replace("\\", "/")

    product_data = {
        "name": name,
        "category": category,
        "price": price,
        "stock": stock,
        "image_url": image_url,
    }

    return crud.create_product(db, schemas.ProductCreate(**product_data))


# @router.post("/", response_model=schemas.ProductOut)
# def create_product(product_in: schemas.ProductCreate, token: str = Depends(oauth2), db: Session = Depends(get_db)):
#     payload = get_payload(token)
#     if not payload or payload.get("role") != "manager":
#         raise HTTPException(status_code=403, detail="Manager required")
#     return crud.create_product(db, product_in)


@router.get("/", response_model=List[schemas.ProductOut])
def list_products(category: Optional[str] = None, popular: Optional[str] = None, limit: int = 50, db: Session = Depends(get_db)):
    prods = crud.list_products(db, category=category, popular=popular, limit=limit)
    if isinstance(prods, list) and prods and isinstance(prods[0], dict) and "product" in prods[0]:
        return [p["product"] for p in prods]
    return prods


@router.get("/{product_id}", response_model=schemas.ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = crud.get_product(db, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return p


@router.put("/{product_id}", response_model=schemas.ProductOut)
def update_product(product_id: int, product_in: schemas.ProductCreate, token: str = Depends(oauth2), db: Session = Depends(get_db)):
    payload = get_payload(token)
    if not payload or payload.get("role") != "manager":
        raise HTTPException(status_code=403, detail="Manager required")
    p = crud.update_product(db, product_id, product_in.model_dump())
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return p


@router.delete("/{product_id}")
def delete_product(product_id: int, token: str = Depends(oauth2), db: Session = Depends(get_db)):
    payload = get_payload(token)
    if not payload or payload.get("role") != "manager":
        raise HTTPException(status_code=403, detail="Manager required")
    ok = crud.delete_product(db, product_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"detail": "deleted"}
