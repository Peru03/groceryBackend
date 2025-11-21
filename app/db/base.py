# app/db/base.py

"""
Import all SQLAlchemy models here so Alembic can autogenerate migrations.

Example:
    from app.models.user import User
    from app.models.product import Product
    from app.models.order import Order
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import all models below (add more as your project grows)
# ---------------------------------------------------------
from app.models.user import User
from app.models.product import Product
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.wishlist import WishlistItem
from app.models.category import Category

# (If you don't have some of these models, remove those imports.)
