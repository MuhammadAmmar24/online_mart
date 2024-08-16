import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, SQLModel
from typing import Annotated, AsyncGenerator
from aiokafka import AIOKafkaProducer
import asyncio

from app import settings
from app.db_engine import engine
from app.deps import get_session
from app.models.payment_model import Payment
from app.crud.payment_crud import get_all_payments, get_payment_by_id, get_payment_by_order_id, update_payment
from app.kafka.producers.payment_response_producer import produce_message_to_order
from app.kafka.consumers.payment_request_consumer import consume_payment_requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables created successfully")

@asynccontextmanager
async def lifespan(app: FastAPI)-> AsyncGenerator[None, None]:
    logger.info("Payment Service Starting...")
    create_db_and_tables()
    task = asyncio.create_task(consume_payment_requests(
        settings.KAFKA_PAYMENT_REQUEST_TOPIC, 
        settings.BOOTSTRAP_SERVER, 
        settings.KAFKA_CONSUMER_GROUP_ID_FOR_PAYMENT_REQUEST
        ))
    yield
    logger.info("Payment Service Closing...")

app = FastAPI(
    lifespan=lifespan,
    title="Payment Service",
    version="0.0.1",
)

@app.get('/')
def start():
    return {"message": "Payment Service"}



@app.post('/pay/{order_id}')
async def pay_order(
    order_id: int,
    session: Annotated[Session, Depends(get_session)]
):
    payment = get_payment_by_order_id(order_id, session)

    if payment:
        if payment.status in ["paid", "cancelled"]:
            raise HTTPException(status_code=400, detail=f"Payment is {payment.status}, cannot process payment.")
        
        # Mark the payment as "paid"
        payment_update = Payment(status="paid")
        updated_payment = update_payment(payment.id, payment_update, session)
        
        # Send a message back to the order service that payment is completed
        await produce_message_to_order(updated_payment)

        return {"message": "Payment successful"}
    else:
        raise HTTPException(status_code=404, detail="Payment not found")



@app.get('/payment/all', response_model=list[Payment])
def call_get_all_payments(session: Annotated[Session, Depends(get_session)]):
    return get_all_payments(session)



@app.get('/payment/{id}', response_model=Payment)
def call_get_payment_by_id(id: int, session: Annotated[Session, Depends(get_session)]):
    return get_payment_by_id(id, session)
