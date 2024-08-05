import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from app.protobuf import product_pb2
from sqlmodel import Session, SQLModel
from typing import Annotated, AsyncGenerator
from aiokafka import AIOKafkaProducer
import asyncio

from app import settings
from app.db_engine import engine
from app.deps import get_session, kafka_producer
from app.models.product_model import Product, ProductUpdate
from app.crud.product_crud import get_all_products, get_product_by_id, validate_id
from app.kafka.producers.product_producer import produce_message
from app.kafka.consumers.product_consumer import consume_products

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables created successfully")

@asynccontextmanager
async def lifespan(app: FastAPI)-> AsyncGenerator[None, None]:
    logger.info("Product Service Starting...")
    create_db_and_tables()
    task = asyncio.create_task(consume_products(
        settings.KAFKA_PRODUCT_TOPIC, settings.BOOTSTRAP_SERVER, settings.KAFKA_CONSUMER_GROUP_ID_FOR_PRODUCT))
    yield
    logger.info("Product Service Closing...")

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
    session: Annotated[Session, Depends(get_session)], 
    producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]):
    existing_product = validate_id(product.id, session)

    if existing_product:
        raise HTTPException(status_code=400, detail=f"Product with ID {product.id} already exists")
    await produce_message(product, producer, "create")
    logger.info(f"Produced message: {product}")
    return product




@app.get('/product/all', response_model=list[Product])
def call_get_all_product(session: Annotated[Session, Depends(get_session)]):

    return get_all_products(session)




@app.get('/product/{id}', response_model=Product)
def call_get_product_by_id(id: int, session: Annotated[Session, Depends(get_session)]):
    
    return get_product_by_id(id=id, session=session)




@app.patch('/product/{id}', response_model=Product)
async def call_update_product(id: int, product: ProductUpdate, session: Annotated[Session, Depends(get_session)],producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]):

    call_get_product_by_id(id, session)
    updated_product = Product(id=id, **product.dict())
    await produce_message(updated_product, producer, "update")
    
    return updated_product



@app.delete('/product/{id}', response_model=dict)
async def call_delete_product_by_id(id: int, session: Annotated[Session, Depends(get_session)],producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]):

    call_get_product_by_id(id, session)
    await produce_message(Product(id=id), producer, "delete")

    return {"deleted_id": id}




