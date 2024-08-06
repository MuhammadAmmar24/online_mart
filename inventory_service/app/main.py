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
from app.models.inventory_model import InventoryItem, InventoryItemUpdate
from app.crud.inventory_crud import get_all_inventory_items, get_inventory_item_by_id,get_inventory_item_by_product_id, validate_id
from app.kafka.producers.inventory_producer import produce_message
from app.kafka.consumers.inventory_consumer import consume_product_updates

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables created successfully")

@asynccontextmanager
async def lifespan(app: FastAPI)-> AsyncGenerator[None, None]:
    logger.info("Inventory Service Starting...")
    create_db_and_tables()
    task = asyncio.create_task(consume_product_updates(
        settings.KAFKA_PRODUCT_TOPIC, settings.BOOTSTRAP_SERVER, settings.KAFKA_CONSUMER_GROUP_ID_FOR_INVENTORY))
    yield
    logger.info("Inventory Service Closing...")


app = FastAPI(
    lifespan=lifespan,
    title="Inventory Service",
    version="0.0.1",
)


@app.get('/')
def start():
    return {"message": "Inventory Service"}

# @app.post('/inventory', response_model=InventoryItem)
# async def call_add_inventory_item(
#     inventory_item: InventoryItem, 
#     session: Annotated[Session, Depends(get_session)], 
#     producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]):

#     existing_inventory_item = validate_id(inventory_item.id, session)

#     if existing_inventory_item:
#         raise HTTPException(status_code=400, detail=f"Inventory Item with ID {inventory_item.id} already exists")
#     # await produce_message(inventory_item, producer, "create")
#     logger.info(f"Produced message: {inventory_item}")
    
#     return inventory_item



@app.get('/inventory/all', response_model=list[InventoryItem])
def call_get_all_inventory_items(session: Annotated[Session, Depends(get_session)]):
    return get_all_inventory_items(session)



@app.get('/inventory/{id}', response_model=InventoryItem)
def call_get_inventory_item_by_id(id: int, session: Annotated[Session, Depends(get_session)]):
    return get_inventory_item_by_id(id=id, session=session)



# @app.patch('/inventory/{id}', response_model=InventoryItem)
# async def call_update_inventory_item(id: int, inventory_item: InventoryItemUpdate, session: Annotated[Session, Depends(get_session)],producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]):

#     call_get_inventory_item_by_id(id, session)
#     updated_inventory_item = InventoryItem(id=id, **inventory_item.dict())
#     await produce_message(updated_inventory_item, producer, "update")
    
#     return updated_inventory_item



# @app.delete('/inventory/{id}', response_model=dict)
# async def call_delete_inventory_item_by_id(id: int, session: Annotated[Session, Depends(get_session)],producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]):

#     call_get_inventory_item_by_id(id, session)
#     await produce_message(InventoryItem(id=id), producer, "delete")

#     return {"deleted_id": id}


