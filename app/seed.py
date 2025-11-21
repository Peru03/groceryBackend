from sqlalchemy.orm import Session
from .database import engine, SessionLocal, Base
from . import models
from .auth import hash_password

def seed():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        if not db.query(models.User).filter_by(email="manager@example.com").first():
            m = models.User(name="Manager", email="manager@example.com", hashed_password=hash_password("managerpass"), role="manager")
            db.add(m)
        if not db.query(models.User).filter_by(email="customer@example.com").first():
            c = models.User(name="Customer", email="customer@example.com", hashed_password=hash_password("custpass"), role="customer")
            db.add(c)
        if db.query(models.Product).count() == 0:
            p1 = models.Product(name="Apple", category="Fruits", price=50.0, stock=100)
            p2 = models.Product(name="Bread", category="Bakery", price=30.0, stock=50)
            p3 = models.Product(name="Milk", category="Dairy", price=45.0, stock=200)
            db.add_all([p1,p2,p3])
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
