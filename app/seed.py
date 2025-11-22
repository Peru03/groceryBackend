from sqlalchemy.orm import Session
from .database import engine, SessionLocal, Base
from . import models
from .auth import hash_password

def seed():
    """Seed initial users and products (byte-safe passwords)"""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        # Manager user
        if not db.query(models.User).filter_by(email="manager@example.com").first():
            manager = models.User(
                name="Manager",
                email="manager@example.com",
                hashed_password=hash_password("managerpass"),
                role="manager"
            )
            db.add(manager)
            print(" Manager account created")

        # Customer user
        if not db.query(models.User).filter_by(email="customer@example.com").first():
            customer = models.User(
                name="Customer",
                email="customer@example.com",
                hashed_password=hash_password("custpass"),
                role="customer"
            )
            db.add(customer)
            print(" Customer account created")

        # Products
        if db.query(models.Product).count() == 0:
            products = [
                models.Product(name="Apple", category="Fruits", price=50.0, stock=100),
                models.Product(name="Bread", category="Bakery", price=30.0, stock=50),
                models.Product(name="Milk", category="Dairy", price=45.0, stock=200),
                models.Product(name="Banana", category="Fruits", price=40.0, stock=150),
                models.Product(name="Chicken Breast", category="Meat", price=250.0, stock=40),
                models.Product(name="Rice", category="Grains", price=120.0, stock=200),
            ]
            db.add_all(products)
            print(" Products created")

        db.commit()
        print(" Database seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f" Seeding error: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
