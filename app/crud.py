from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from . import models, schemas, auth
from datetime import datetime
from fastapi import HTTPException

# Users
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    """Create a new user with hashed password"""
    # Ensure password is a string and within safe length
    password = str(user.password)
    
    # Extra safety: truncate at character level before hashing
    if len(password) > 72:
        password = password[:72]
    
    hashed = auth.hash_password(password)
    
    db_user = models.User(
        name=user.name,
        email=user.email,
        hashed_password=hashed,
        role=user.role if hasattr(user, "role") else "customer"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Products
def create_product(db: Session, product: schemas.ProductCreate):
    db_p = models.Product(**product.model_dump())
    db.add(db_p)
    db.commit()
    db.refresh(db_p)
    return db_p

def get_product(db: Session, product_id: int):
    return db.query(models.Product).get(product_id)

def list_products(db: Session, category: str = None, popular: str = None, limit: int = 100):
    q = db.query(models.Product)
    if category:
        q = q.filter(models.Product.category == category)
    if popular:
        sold_counts = db.query(models.OrderItem.product_id, func.sum(models.OrderItem.quantity).label("times_sold")).group_by(models.OrderItem.product_id).subquery()
        q = q.outerjoin(sold_counts, models.Product.id == sold_counts.c.product_id).add_columns(models.Product, func.coalesce(sold_counts.c.times_sold, 0).label("times_sold"))
        if popular == "most":
            q = q.order_by(desc("times_sold"))
        else:
            q = q.order_by(asc("times_sold"))
        rows = q.limit(limit).all()
        return [{"product": r[1], "times_sold": int(r[2])} for r in rows]
    return q.limit(limit).all()

def update_product(db: Session, product_id: int, fields: dict):
    p = get_product(db, product_id)
    if not p:
        return None
    for k,v in fields.items():
        setattr(p, k, v)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

def delete_product(db: Session, product_id: int):
    p = get_product(db, product_id)
    if not p:
        return False
    db.delete(p)
    db.commit()
    return True


# Cart

def add_to_cart(db: Session, user_id: int, product_id: int, quantity: int = 1):
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = db.query(models.CartItem).filter_by(user_id=user_id, product_id=product_id).first()

    # If item already in cart
    if existing:
        if product.stock < existing.quantity + quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Only {product.stock} items available in stock"
            )
        existing.quantity += quantity
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    # New cart item
    if quantity > product.stock:
        raise HTTPException(
            status_code=400,
            detail=f"Only {product.stock} items available in stock"
        )

    ci = models.CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
    db.add(ci)
    db.commit()
    db.refresh(ci)
    return ci



def get_cart_items(db: Session, user_id: int):
    return db.query(models.CartItem).filter(models.CartItem.user_id == user_id).all()

def remove_cart_item(db: Session, cart_item_id: int):
    item = db.query(models.CartItem).get(cart_item_id)
    if item:
        db.delete(item)
        db.commit()
        return True
    return False



# Wishlist
def add_to_wishlist(db: Session, user_id: int, product_id: int):
    exists = db.query(models.WishlistItem).filter_by(user_id=user_id, product_id=product_id).first()
    if exists:
        return exists
    w = models.WishlistItem(user_id=user_id, product_id=product_id)
    db.add(w)
    db.commit()
    db.refresh(w)
    return w

def get_wishlist(db: Session, user_id: int):
    return db.query(models.WishlistItem).filter_by(user_id=user_id).all()

# Checkout
def checkout(db: Session, user_id: int):
    cart_items = get_cart_items(db, user_id)
    if not cart_items:
        return None
    total = 0.0
    for ci in cart_items:
        product = get_product(db, ci.product_id)
        if product.stock < ci.quantity:
            raise Exception(f"Insufficient stock for {product.name}")
        total += product.price * ci.quantity

    order = models.Order(user_id=user_id, total_amount=total)
    db.add(order)
    db.commit()
    db.refresh(order)

    for ci in cart_items:
        product = get_product(db, ci.product_id)
        oi = models.OrderItem(order_id=order.id, product_id=product.id, quantity=ci.quantity, price_at_purchase=product.price)
        db.add(oi)
        product.stock -= ci.quantity
        db.add(product)
        db.delete(ci)
    db.commit()
    db.refresh(order)
    return order

def create_order(db: Session, user_id: int, total: float, cart_items):
    order = models.Order(user_id=user_id, total_amount=total)
    db.add(order)
    db.commit()
    db.refresh(order)

    for ci in cart_items:
        product = get_product(db, ci.product_id)
        oi = models.OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=ci.quantity,
            price_at_purchase=product.price
        )
        db.add(oi)
        product.stock -= ci.quantity
        db.add(product)
        db.delete(ci)

    db.commit()
    db.refresh(order)
    return order


# Sales report
def sales_report(db: Session, sort: str = "most", category: str = None, limit: int = 50):
    q = db.query(
        models.Product.id.label("product_id"),
        models.Product.name,
        models.Product.category,
        func.coalesce(func.sum(models.OrderItem.quantity), 0).label("times_sold")
    ).outerjoin(models.OrderItem, models.Product.id == models.OrderItem.product_id).group_by(models.Product.id)
    if category:
        q = q.filter(models.Product.category == category)
    if sort == "most":
        q = q.order_by(desc("times_sold"))
    else:
        q = q.order_by(asc("times_sold"))
    return q.limit(limit).all()

# Promo code

def create_promocode(db: Session, data: schemas.PromoCodeCreate):
    promo = models.PromoCode(**data.model_dump())
    db.add(promo)
    db.commit()
    db.refresh(promo)
    return promo

def apply_promocode(db: Session, code: str, cart_total: float):
    promo = db.query(models.PromoCode).filter(
        models.PromoCode.code == code,
        models.PromoCode.active == True,
        models.PromoCode.expires_at > datetime.utcnow()
    ).first()

    if not promo:
        return None

    if cart_total < promo.min_order_amount:
        return "min_amount"

    discount_amount = cart_total * (promo.discount_percent / 100)
    return discount_amount


# LOW STOCK 
def low_stock_products(db: Session, threshold: int = 5):
    return db.query(models.Product).filter(models.Product.stock <= threshold).all()
