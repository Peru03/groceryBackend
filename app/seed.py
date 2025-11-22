from sqlalchemy.orm import Session
from .database import engine, SessionLocal, Base
from . import models
from passlib.context import CryptContext

# Create password context directly here to avoid any import issues
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password_safe(password: str) -> str:
    """Hash password with bcrypt, ensuring it's under 72 bytes"""
    # Truncate to 72 bytes if needed
    safe_password = password[:72] if len(password) > 72 else password
    return pwd_context.hash(safe_password)

def seed():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        # Create manager if doesn't exist
        if not db.query(models.User).filter_by(email="manager@example.com").first():
            m = models.User(
                name="Manager",
                email="manager@example.com",
                hashed_password=hash_password_safe("managerpass"),
                role="manager"
            )
            db.add(m)
            print(" Manager account created")
        
        # Create customer if doesn't exist
        if not db.query(models.User).filter_by(email="customer@example.com").first():
            c = models.User(
                name="Customer",
                email="customer@example.com",
                hashed_password=hash_password_safe("custpass"),
                role="customer"
            )
            db.add(c)
            print(" Customer account created")
        
        # Create products if none exist
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