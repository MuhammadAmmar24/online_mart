import logging
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError, KafkaError
from fastapi import HTTPException
from payment_service.app.models.payment_model import Payment
from payment_service.app.crud.payment_crud import add_payment, update_payment, delete_payment_by_id
from app.deps import get_session
from app.protobuf.payment_proto import payment_pb2
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_RETRIES = 5
RETRY_INTERVAL = 10  # seconds

async def process_message(protobuf_payment: payment_pb2.Payment, operation: str):
    try:
        sqlmodel_payment = Payment(
            id=protobuf_payment.id,
            order_id=protobuf_payment.order_id,
            user_id=protobuf_payment.user_id,
            amount=protobuf_payment.amount,
            status=protobuf_payment.status,
        )

        with next(get_session()) as session:
            if operation == "create":
                db_insert_payment = add_payment(sqlmodel_payment, session=session)
                logger.info(f"DB Inserted Payment: {db_insert_payment}")

            elif operation == "update":
                db_update_payment = update_payment(
                    sqlmodel_payment.id, Payment(**sqlmodel_payment.dict()), session=session)
                logger.info(f"DB Updated Payment: {db_update_payment}")

            elif operation == "delete":
                db_delete_payment = delete_payment_by_id(sqlmodel_payment.id, session=session)
                logger.info(f"DB Deleted Payment: {db_delete_payment}")

    except HTTPException as e:
        logger.error(f"HTTPException: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def consume_payments(topic, bootstrap_servers, group_id):
    retries = 0

    while retries < MAX_RETRIES:
        try:
            
            consumer = AIOKafkaConsumer(
                topic, 
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                auto_offset_reset='earliest',
            )

            await consumer.start()
            break
        except KafkaConnectionError as e:
            retries += 1
            await asyncio.sleep(RETRY_INTERVAL)
    else:
        return

    try:
        logger.info(f"Consuming messages from topic: {topic}")
        async for msg in consumer:
        
            protobuf_payment = payment_pb2.Payment()
            protobuf_payment.ParseFromString(msg.value)

            operation = msg.key.decode('utf-8')

            await process_message(protobuf_payment, operation)
    except KafkaError as e:
        logger.error(f"Error while consuming message: {e}")
    finally:
        await consumer.stop()
