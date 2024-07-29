from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from typing import Annotated, AsyncGenerator
from sqlmodel import Session, SQLModel
import asyncio
import json

from app import settings
from app.db_engine import engine
from app.deps import get_session
from app.models.product_model import Product, ProductUpdate
from app.crud.product_crud import add_product, get_all_products, get_product_by_id, delete_product_by_id, update_product
from app.kafka.producers.producer import kafka_producer
from app.kafka.consumers.product_consumer import consume_products
from app.protobuf import product_pb2



def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:

    task = asyncio.create_task(consume_products(
        settings.KAFKA_PRODUCT_TOPIC, settings.BOOTSTRAP_SERVER, settings.KAFKA_CONSUMER_GROUP_ID_FOR_PRODUCT))
    
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
async def call_add_product( 
    product: Product, 
    session: Annotated[Session, Depends(get_session)], producer: Annotated[kafka_producer, Depends(kafka_producer)]):

    protobuf_product = product_pb2.Product(
        id=product.id,
        title=product.title,
        description=product.description,
        category=product.category,
        price=product.price,
        discount=product.discount,
        quantity=product.quantity,
        brand=product.brand,
        weight=product.weight,
        expiry=product.expiry,      
        sku=product.sku
    )
    print(f"Prodduct protobuf: {protobuf_product}")

    serialized_product = protobuf_product.SerializeToString()
    print(f"Serialized Product: {serialized_product}")

    await producer.send_and_wait(settings.KAFKA_PRODUCT_TOPIC, serialized_product)
    print("Message produced")

    # new_product = add_product(product, session)
    return product



@app.get('/product/all', response_model=list[Product])
def call_get_all_product(session: Annotated[Session, Depends(get_session)]):
    return  get_all_products(session)


@app.get('/product/{id}', response_model=Product)
def call_get_product_by_id(id: int, 
                             session: Annotated[Session, Depends(get_session)]):
    try:
        return  get_product_by_id(id=id, session=session)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


@app.delete('/product/{id}', response_model=dict)
def call_delete_product_by_id(id: int, 
                             session: Annotated[Session, Depends(get_session)]):
    try:
        return  delete_product_by_id(id=id, session=session)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.patch('/product/{id}', response_model=Product)
def call_update_product(id: int,
                              product: ProductUpdate,
                             session: Annotated[Session, Depends(get_session)]):
    try:
        return  update_product(id=id, to_update_product_data=product, session=session)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      