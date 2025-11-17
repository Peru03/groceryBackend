from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# User schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: Optional[str] = "customer"

class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        orm_mode = True

# Auth
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None

# Product
class ProductBase(BaseModel):
    name: str
    category: Optional[str] = None
    price: float
    stock: int
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductOut(ProductBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

# Cart
class CartItemCreate(BaseModel):
    product_id: int
    quantity: int

class CartItemOut(BaseModel):
    id: int
    product: ProductOut
    quantity: int

    class Config:
        orm_mode = True

# Wishlist
class WishlistItemOut(BaseModel):
    id: int
    product: ProductOut

    class Config:
        orm_mode = True

# Order
class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

class OrderOut(BaseModel):
    id: int
    total_amount: float
    created_at: datetime
    items: List[dict]

    class Config:
        orm_mode = True

# Sales report item
class SalesReportItem(BaseModel):
    product_id: int
    name: str
    category: Optional[str]
    times_sold: int
