from sqlalchemy.orm import Session
from .database import SessionLocal, Base, engine
from . import models
from .auth import hash_password

def seed():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        if not db.query(models.User).filter_by(email="manager@example.com").first():
            manager = models.User(
                name="Manager",
                email="manager@example.com",
                hashed_password=hash_password("managerpass"),
                role="manager"
            )
            db.add(manager)

        if not db.query(models.User).filter_by(email="customer@example.com").first():
            customer = models.User(
                name="Customer",
                email="customer@example.com",
                hashed_password=hash_password("custpass"),
                role="customer"
            )
            db.add(customer)

        # Products
        if db.query(models.Product).count() == 0:
            products = [
                models.Product(name="Apple", category="Fruits", price=50.0, stock=100),
                models.Product(name="Bread", category="Bakery", price=30.0, stock=50),
                models.Product(name="Milk", category="Dairy", price=45.0, stock=200),
            ]
            db.add_all(products)

        db.commit()
        print("Database seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"Seeding error: {str(e)}")
        raise
    finally:
        db.close()
