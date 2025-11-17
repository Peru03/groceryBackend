from sqlalchemy.orm import Session
from . import models, schemas, auth
from typing import List, Optional
from sqlalchemy import func, desc, asc

# Users
def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed = auth.hash_password(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).get(user_id)

# Products
def create_product(db: Session, product: schemas.ProductCreate) -> models.Product:
    db_p = models.Product(**product.dict())
    db.add(db_p)
    db.commit()
    db.refresh(db_p)
    return db_p

def get_product(db: Session, product_id: int):
    return db.query(models.Product).get(product_id)

def list_products(db: Session, category: Optional[str]=None, order_by_popular: Optional[str]=None, limit=100):
    q = db.query(models.Product)
    if category:
        q = q.filter(models.Product.category == category)
    # order_by_popular: "most" or "least"
    if order_by_popular:
        # join with order_items aggregate
        sold_counts = db.query(
            models.OrderItem.product_id,
            func.sum(models.OrderItem.quantity).label("times_sold")
        ).group_by(models.OrderItem.product_id).subquery()

        q = q.outerjoin(sold_counts, models.Product.id == sold_counts.c.product_id).add_columns(
            models.Product, func.coalesce(sold_counts.c.times_sold, 0).label("times_sold")
        )
        if order_by_popular == "most":
            q = q.order_by(desc("times_sold"))
        else:
            q = q.order_by(asc("times_sold"))
        rows = q.limit(limit).all()
        # rows are tuples (Product, times_sold)
        return [{"product": r[1], "times_sold": int(r[2])} for r in rows]
    else:
        return q.limit(limit).all()

def update_product(db: Session, product_id: int, fields: dict):
    p = get_product(db, product_id)
    for k,v in fields.items():
        setattr(p, k, v)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

def delete_product(db: Session, product_id: int):
    p = get_product(db, product_id)
    db.delete(p)
    db.commit()
    return True

# Cart
def add_to_cart(db: Session, user_id: int, product_id: int, quantity: int = 1):
    existing = db.query(models.CartItem).filter_by(user_id=user_id, product_id=product_id).first()
    if existing:
        existing.quantity += quantity
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing
    ci = models.CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
    db.add(ci)
    db.commit()
    db.refresh(ci)
    return ci

def remove_from_cart(db: Session, cart_item_id: int):
    item = db.query(models.CartItem).get(cart_item_id)
    if item:
        db.delete(item)
        db.commit()
        return True
    return False

def get_cart_items(db: Session, user_id: int):
    return db.query(models.CartItem).filter(models.CartItem.user_id == user_id).all()

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

def get_wishlist(db: Session, user_id:int):
    return db.query(models.WishlistItem).filter_by(user_id=user_id).all()

# Checkout: create Order from Cart
def checkout(db: Session, user_id: int):
    cart_items = get_cart_items(db, user_id)
    if not cart_items:
        return None
    total = 0.0
    # ensure stock and reduce stock
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
        # reduce stock
        product.stock -= ci.quantity
        db.add(product)
        # remove cart item
        db.delete(ci)
    db.commit()
    db.refresh(order)
    return order

# Sales report
def sales_report(db: Session, sort: str = "most", category: Optional[str]=None, limit: int=50):
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
    rows = q.limit(limit).all()
    return rows
