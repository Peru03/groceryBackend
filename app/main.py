from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from .database import Base, engine
from .routers import (
    auth as auth_router,
    products as products_router,
    cart as cart_router,
    orders as orders_router,
    wishlist as wishlist_router,
    promocodes as promocode_router,
    inventory as inventory_router
)

app = FastAPI(
    title="Grocery Backend API",
    description="Production-ready grocery e-commerce API",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)

# Mount static files for uploads
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(auth_router.router)
app.include_router(products_router.router)
app.include_router(cart_router.router)
app.include_router(orders_router.router)
app.include_router(wishlist_router.router)
app.include_router(promocode_router.router)
app.include_router(inventory_router.router)


@app.get("/")
def root():
    return {
        "message": "Grocery Backend API is running",
        "status": "healthy",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# ===== SEED ENDPOINT =====
@app.post("/admin/seed")
def seed_database(secret: str):
    """
    Seed database with initial data.
    Call once with your SECRET_KEY to initialize the database.
    """
    # Security check
    if secret != os.getenv("SECRET_KEY"):
        raise HTTPException(status_code=403, detail="Invalid secret key")
    
    from . import seed, models
    from .database import SessionLocal
    
    db = SessionLocal()
    try:
        # Check if already seeded
        existing_manager = db.query(models.User).filter_by(email="manager@example.com").first()
        if existing_manager:
            return {"message": "Database already seeded", "status": "skipped"}
        
        # Run seed
        seed.seed()
        return {
            "message": "Database seeded successfully",
            "status": "success",
            "accounts": {
                "manager": {"email": "manager@example.com", "password": "managerpass"},
                "customer": {"email": "customer@example.com", "password": "custpass"}
            },
            "products": ["Apple", "Bread", "Milk"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Seeding failed: {str(e)}")
    finally:
        db.close()