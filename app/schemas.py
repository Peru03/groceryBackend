from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class ORMModel(BaseModel):
    model_config = {"from_attributes": True}


# User
class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserOut(UserBase, ORMModel):
    id: int
    role: str
    created_at: datetime


# Auth tokens
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


class ProductOut(ProductBase, ORMModel):
    id: int
    created_at: datetime


# Cart
class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = 1


class CartItemOut(ORMModel):
    id: int
    product: ProductOut
    quantity: int


# Wishlist
class WishlistItemOut(ORMModel):
    id: int
    product: ProductOut
    
class WishlistItemCreate(BaseModel):
    product_id: int




# Order
class OrderItemOut(BaseModel):
    product_id: int
    quantity: int
    price_at_purchase: float


class OrderOut(ORMModel):
    id: int
    total_amount: float
    created_at: datetime
    items: List[OrderItemOut]


# PromoCode
class PromoCodeCreate(BaseModel):
    code: str
    discount_percent: int
    expires_at: datetime
    min_order_amount: float = 0


class PromoCodeOut(BaseModel):
    id: int
    code: str
    discount_percent: int
    expires_at: datetime
    min_order_amount: float
    active: bool

    class Config:
        from_attributes = True


class PromoUpdate(BaseModel):
    code: Optional[str]
    discount_percent: Optional[int]
    expires_at: Optional[datetime]
    min_order_amount: Optional[float]
    active: Optional[bool]