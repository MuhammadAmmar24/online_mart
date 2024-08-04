from fastapi import HTTPException
from sqlmodel import Session, select, asc

from inventory_service.app.models.inventory_model import Product, ProductUpdate


# Add a new Product
def add_product(product_data, session: Session) -> Product:
    try:
        session.add(product_data)
        session.commit()
        session.refresh(product_data)
        return product_data
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    

# Get all Products
def get_all_products(session: Session) -> list[Product]:
    all_products = session.exec(select(Product).order_by(asc(Product.id)))
    if all_products is None:
        raise HTTPException(status_code=404, detail="No Product Found")
    return all_products


# Get Product by id
def get_product_by_id(id: int, session: Session) -> Product:
    product = session.exec(select(Product).where(Product.id == id)).one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail=f"No Product found with the id : {id}")
    return product

# Delete Product by id
def delete_product_by_id(id: int, session: Session) -> dict:

    # 1. Get the Product 
    product = get_product_by_id(id,session)

    # 2. Delete the Product
    session.delete(product)
    session.commit()

    return {"message": "Product Deleted Successfully"}

# Update Product by id
def update_product(id: int, to_update_product_data: ProductUpdate, session: Session) -> Product:

    # 1. Get the Product 
    product = get_product_by_id(id,session)
    
    # 2. Upload the Product
    hero_data = to_update_product_data.model_dump(exclude_unset=True)
    product.sqlmodel_update(hero_data)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product

# Check if product exist or not
def validate_id(id: int, session: Session) -> Product:
    product = session.exec(select(Product).where(Product.id == id)).one_or_none()
    if not product:
        return None  
    return product


# Validate Product by id