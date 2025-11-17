from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from . import database, models, schemas, crud, auth
from .database import Base, engine
from .auth import verify_password, create_access_token
from jose import JWTError, jwt

# create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Grocery Backend")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# helper to get DB
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# authenticate user and produce token
@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, form_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token_data = {"user_id": user.id, "role": user.role}
    access_token = create_access_token(data=token_data)
    return {"access_token": access_token, "token_type": "bearer"}

# helper dependency to get current user
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    from jose import JWTError, jwt
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        user_id: int = payload.get("user_id")
        role: str = payload.get("role")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token")
    user = crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def require_manager(user: models.User = Depends(get_current_user)):
    if user.role != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    return user

def require_customer(user: models.User = Depends(get_current_user)):
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Customer access required")
    return user

# Register
@app.post("/register", response_model=schemas.UserOut)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = crud.create_user(db, user_in)
    return user

# Product endpoints (manager)
@app.post("/products", response_model=schemas.ProductOut, dependencies=[Depends(require_manager)])
def create_product(product_in: schemas.ProductCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.create_product(db, product_in)

@app.put("/products/{product_id}", response_model=schemas.ProductOut, dependencies=[Depends(require_manager)])
def update_product(product_id:int, product_in: schemas.ProductCreate, db: Session = Depends(get_db)):
    return crud.update_product(db, product_id, product_in.dict())

@app.delete("/products/{product_id}", dependencies=[Depends(require_manager)])
def delete_product(product_id:int, db: Session = Depends(get_db)):
    crud.delete_product(db, product_id)
    return {"detail":"deleted"}

# Browse products (customers + unauthenticated)
@app.get("/products", response_model=List[schemas.ProductOut])
def list_products(category: Optional[str]=None, popular: Optional[str]=None, limit: int=50, db: Session = Depends(get_db)):
    # popular: "most" or "least" or None
    if popular:
        complex = crud.list_products(db, category=category, order_by_popular=popular, limit=limit)
        # complex returns list of dicts {product, times_sold}, but response_model expects ProductOut.
        return [c["product"] for c in complex]
    prods = crud.list_products(db, category=category, order_by_popular=None, limit=limit)
    return prods

@app.get("/products/{product_id}", response_model=schemas.ProductOut)
def get_product(product_id:int, db: Session = Depends(get_db)):
    p = crud.get_product(db, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return p

# Cart operations (customer)
@app.post("/cart", response_model=schemas.CartItemOut)
def add_cart(item: schemas.CartItemCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    # only customers allowed
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Only customers can manage cart")
    return crud.add_to_cart(db, user.id, item.product_id, item.quantity)

@app.get("/cart", response_model=List[schemas.CartItemOut])
def get_cart(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Only customers can view cart")
    return crud.get_cart_items(db, user.id)

@app.delete("/cart/{cart_item_id}")
def remove_cart(cart_item_id:int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Only customers can modify cart")
    ok = crud.remove_from_cart(db, cart_item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return {"detail":"removed"}

# Wishlist
@app.post("/wishlist", response_model=schemas.WishlistItemOut)
def add_wishlist(product_id:int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return crud.add_to_wishlist(db, user.id, product_id)

@app.get("/wishlist", response_model=List[schemas.WishlistItemOut])
def get_wishlist(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return crud.get_wishlist(db, user.id)

# Checkout
@app.post("/checkout", response_model=schemas.OrderOut)
def checkout(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Only customers can checkout")
    try:
        order = crud.checkout(db, user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    # Build response
    items = []
    for oi in order.items:
        items.append({
            "product_id": oi.product_id,
            "quantity": oi.quantity,
            "price_at_purchase": oi.price_at_purchase
        })
    return {
        "id": order.id,
        "total_amount": order.total_amount,
        "created_at": order.created_at,
        "items": items
    }

# Sales report (manager)
@app.get("/manager/sales-report", dependencies=[Depends(require_manager)])
def sales_report(sort: Optional[str] = "most", category: Optional[str] = None, limit: int = 50, db: Session = Depends(get_db)):
    rows = crud.sales_report(db, sort=sort, category=category, limit=limit)
    return [{"product_id": r.product_id, "name": r.name, "category": r.category, "times_sold": int(r.times_sold)} for r in rows]

# Low stock endpoint (manager)
@app.get("/manager/low-stock", dependencies=[Depends(require_manager)])
def low_stock(threshold: int = 5, db: Session = Depends(get_db)):
    prods = db.query(models.Product).filter(models.Product.stock <= threshold).all()
    return prods
