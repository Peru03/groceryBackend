from .database import SessionLocal, engine
from . import models, crud, schemas, auth
from sqlalchemy.orm import Session

def seed():
    db: Session = SessionLocal()
    # create a manager and a customer
    from .models import User
    if not db.query(models.User).filter_by(email="manager@example.com").first():
        manager = schemas.UserCreate(email="manager@example.com", password="managerpass", role="manager")
        crud.create_user(db, manager)
    if not db.query(models.User).filter_by(email="customer@example.com").first():
        customer = schemas.UserCreate(email="customer@example.com", password="custpass", role="customer")
        crud.create_user(db, customer)

    # create some products
    if db.query(models.Product).count() == 0:
        products = [
            {"name":"Apple", "category":"Fruits", "price":50.0, "stock":100, "image_url":""},
            {"name":"Bread", "category":"Bakery", "price":30.0, "stock":50, "image_url":""},
            {"name":"Milk", "category":"Dairy", "price":45.0, "stock":200, "image_url":""}
        ]
        for p in products:
            crud.create_product(db, schemas.ProductCreate(**p))
    db.close()

if __name__ == "__main__":
    seed()
