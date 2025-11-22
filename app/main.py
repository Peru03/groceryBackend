from fastapi import FastAPI, HTTPException
import os
from .database import SessionLocal, Base, engine
from . import models
from .utils import hash_password_safe  # <-- Import the safe hasher

app = FastAPI()

@app.post("/admin/seed")
def seed_database(secret: str):
    """
    Seed database with initial data.
    Only works if SECRET_KEY matches.
    """
    if secret != os.getenv("SECRET_KEY"):
        raise HTTPException(status_code=403, detail="Invalid secret key")

    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(models.User).filter_by(email="manager@example.com").first():
            return {"message": "Database already seeded", "status": "skipped"}

        # Create manager
        manager = models.User(
            name="Manager",
            email="manager@example.com",
            hashed_password=hash_password_safe("managerpass"),
            role="manager"
        )
        db.add(manager)

        # Create customer
        customer = models.User(
            name="Customer",
            email="customer@example.com",
            hashed_password=hash_password_safe("custpass"),
            role="customer"
        )
        db.add(customer)

        # Seed products if none exist
        if db.query(models.Product).count() == 0:
            products = [
                models.Product(name="Apple", category="Fruits", price=50.0, stock=100),
                models.Product(name="Bread", category="Bakery", price=30.0, stock=50),
                models.Product(name="Milk", category="Dairy", price=45.0, stock=200),
            ]
            db.add_all(products)

        db.commit()

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
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Seeding failed: {str(e)}")
    finally:
        db.close()
