from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from typing import Annotated, AsyncGenerator
from sqlmodel import Session, SQLModel

from app import settings
from app.db_engine import engine
from app.deps import get_session
from app.models.product_model import Product, ProductUpdate
from app.crud.product_crud import add_product, get_all_products, get_product_by_id, delete_product_by_id, update_product

def create_db_and_tables() -> None:
    print(f"In create_db function...   engine is {engine}")
    SQLModel.metadata.create_all(engine)
    print("Completed create_db function...")
    


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    print("Product Service Starting...")
    create_db_and_tables()
    print("DB done Successfully!")
    yield
    print("Product Service Closing...")


app = FastAPI(
    lifespan=lifespan,
    title="Product Service",
    version="0.0.1",
)



@app.get('/')
def start():
    return {"message": "Product Service"}

@app.post('/product', response_model=Product)
def call_add_product( 
    product: Product, 
    session: Annotated[Session, Depends(get_session)]):
    new_product = add_product(product, session)
    return new_product



@app.get('/product/all', response_model=list[Product])
def call_get_all_product(session: Annotated[Session, Depends(get_session)]):
    return  get_all_products(session)


@app.get('/product/{product_id}', response_model=Product)
def call_get_product_by_id(product_id: int, 
                             session: Annotated[Session, Depends(get_session)]):
    try:
        return  get_product_by_id(product_id=product_id, session=session)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


@app.delete('/product/{product_id}', response_model=dict)
def call_delete_product_by_id(product_id: int, 
                             session: Annotated[Session, Depends(get_session)]):
    try:
        return  delete_product_by_id(product_id=product_id, session=session)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.patch('/product/{product_id}', response_model=Product)
def call_update_product(product_id: int,
                              product: ProductUpdate,
                             session: Annotated[Session, Depends(get_session)]):
    try:
        return  update_product(product_id=product_id, to_update_product_data=product, session=session)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      