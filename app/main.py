from fastapi import FastAPI
from .database import Base, engine
from .routers import auth as auth_router, products as products_router, cart as cart_router, orders as orders_router ,wishlist as wishlist_router,promocodes as promocode_router ,inventory as inventory_router
from . import models

app = FastAPI(title="Grocery Backend")

# create tables
Base.metadata.create_all(bind=engine)

# include routers with prefixes
app.include_router(auth_router.router)
app.include_router(products_router.router)
app.include_router(cart_router.router)
app.include_router(orders_router.router)
app.include_router(wishlist_router.router)
app.include_router(promocode_router.router)
app.include_router(inventory_router.router)



@app.get("/")
def root():
    return {"message": "Grocery backend running"}
