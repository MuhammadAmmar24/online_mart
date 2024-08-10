import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, SQLModel
from typing import Annotated, List, AsyncGenerator
from aiokafka import AIOKafkaProducer
import asyncio
from app import settings
from app.db_engine import engine
from app.deps import get_session, kafka_producer
from app.models.order_model import OrderModel, OrderUpdate, OrderCreate
from app.crud.order_crud import get_all_orders, get_order_by_id, update_order, validate_order_id
from app.kafka.producers.inventory_request_producer import produce_message_to_inventory
from app.kafka.producers.payment_request_producer import produce_message_to_payment
from app.kafka.consumers.inventory_response_consumer import consume_inventory_response
from app.kafka.consumers.payment_response_consumer import consume_payment_response


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables created successfully")

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Order Service Starting...")
    create_db_and_tables()
    task = asyncio.create_task(consume_inventory_response(
        settings.KAFKA_INVENTORY_RESPONSE_TOPIC, 
        settings.BOOTSTRAP_SERVER, 
        settings.KAFKA_CONSUMER_GROUP_ID_FOR_INVENTORY_RESPONSE
        ))
    asyncio.create_task(consume_payment_response(
        settings.KAFKA_PAYMENT_RESPONSE_TOPIC, 
        settings.BOOTSTRAP_SERVER, 
        settings.KAFKA_CONSUMER_GROUP_ID_FOR_PAYMENT_RESPONSE
        ))
    
    yield
    logger.info("Order Service Closing...")

app = FastAPI(
    lifespan=lifespan,
    title="Order Service",
    version="0.0.1",
)

@app.get('/')
def start():
    return {"message": "Order Service"}

@app.post('/order', response_model=OrderModel)
async def call_add_order(
    order: OrderCreate,
    session: Annotated[Session, Depends(get_session)],
    producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]
):
    existing_order = validate_order_id(order.id, session)

    if existing_order:
        raise HTTPException(status_code=400, detail=f"Order with ID {order.id} already exists")
    
    await produce_message_to_inventory(order, producer)

     # Return the response
    return {
            "id": order.id,
            "status":order.status,
            "message": "Your order is being processed. You will receive a notification once the processing is complete."
        }




@app.get('/order/all', response_model=List[OrderModel])
def call_get_all_orders(session: Annotated[Session, Depends(get_session)]):
    return get_all_orders(session)



@app.get('/order/{id}', response_model=OrderModel)
def call_get_order_by_id(id: int, session: Annotated[Session, Depends(get_session)]):
    return get_order_by_id(id=id, session=session)



@app.patch('/order/{id}', response_model=OrderModel)
async def call_update_order(
    id: int,
    order: OrderUpdate,
    session: Annotated[Session, Depends(get_session)],
    producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]
):
    
    existing_order = get_order_by_id(id, session)

    if existing_order.status in ['shipped', 'paid', 'delivered', 'cancelled']:
        raise HTTPException(status_code=400, detail=f"Order {id} cannot be updated as it is already {existing_order.status}")

    existing_order.quantity = order.quantity
    existing_order.total_amount = 0.0
    await produce_message_to_inventory(existing_order, producer)
    return {
            "id": existing_order.id,
            "status":existing_order.status,
            "message": "Your order is being processed. You will receive a notification once the processing is complete."
        }




@app.delete('/order/{id}', response_model=dict)
async def call_delete_order_by_id(
    id: int,
    session: Annotated[Session, Depends(get_session)],
    producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]
):
    order = call_get_order_by_id(id, session)

    if order.status not in ['shipped', 'paid', 'delivered', 'cancelled']:
        order_update = OrderUpdate(status="cancelled")
        order = update_order(id, order_update, session)

        logger.info(f"Order {id} cancelled, sending message to release inventory: {order}")
        await produce_message_to_inventory(order, producer)
        await produce_message_to_payment(order)

        
        return {"status": "cancelled", 
                "message": f"Order {id} has been cancelled and inventory released."
                }
    else:
        raise HTTPException(status_code=400, detail=f"Order {id} cannot be cancelled as it is already {order.status}")





# @app.post('/order/{id}/status', response_model=OrderModel)
# async def call_update_order_status(
#     id: int,
#     status: OrderStatus,
#     session: Annotated[Session, Depends(get_session)],
#     producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]
# ):
#     updated_order = update_order_status(id, status, session)
#     updated_order.updated_at = datetime.now(timezone.utc)
#     await produce_message(updated_order, producer, "update_status")
#     return updated_order
