import logging
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError, KafkaError
from fastapi import HTTPException
from app.models.order_model import OrderModel, OrderUpdate, OrderStatus
from app.crud.order_crud import add_order, update_order, delete_order_by_id, add_order_item, update_order_status
from app.deps import get_session
from app.protobuf import order_pb2
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_RETRIES = 5
RETRY_INTERVAL = 10  # seconds

async def process_message(protobuf_order: order_pb2.OrderModel, operation: str):
    try:
        sqlmodel_order = OrderModel(
            id=protobuf_order.id,
            user_id=protobuf_order.user_id,
            product_id=protobuf_order.product_id,
            quantity=protobuf_order.quantity,
            total_amount=protobuf_order.total_amount,
            # status=OrderStatus(protobuf_order.status)
        )
        logger.info(f"Converted SQLModel Order Data: {sqlmodel_order}")

        with next(get_session()) as session:
            if operation == "create":
                db_insert_order = add_order(sqlmodel_order, session=session)
                logger.info(f"DB Inserted Order: {db_insert_order}")
            elif operation == "update":
                order_update_data = OrderUpdate(
                    user_id=sqlmodel_order.user_id,
                    status=sqlmodel_order.status,
                    total_amount=sqlmodel_order.total_amount
                )
                db_update_order = update_order(sqlmodel_order.id, order_update_data, session=session)
                logger.info(f"DB Updated Order: {db_update_order}")
            elif operation == "delete":
                db_delete_order = delete_order_by_id(sqlmodel_order.id, session=session)
                logger.info(f"DB Deleted Order: {db_delete_order}")
            elif operation == "update_status":
                db_update_status = update_order_status(sqlmodel_order.id, sqlmodel_order.status, session=session)
                logger.info(f"DB Updated Order Status: {db_update_status}")

    except HTTPException as e:
        logger.error(f"HTTPException: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def consume_orders(topic, bootstrap_servers, group_id):
    retries = 0
    while retries < MAX_RETRIES:
        try:
            consumer = AIOKafkaConsumer(
                topic, 
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                auto_offset_reset='earliest',
            )
            logger.info("Consumer created, attempting to start...")
            await consumer.start()
            logger.info("Consumer started successfully")
            break
        except KafkaConnectionError as e:
            retries += 1
            logger.error(f"Kafka connection error: {e}")
            logger.info(f"Retrying {retries}/{MAX_RETRIES}...")
            await asyncio.sleep(RETRY_INTERVAL)
    else:
        logger.error("Failed to connect to Kafka broker after several retries")
        return

    try:
        async for msg in consumer:
            logger.info(f"Received message on topic: {msg.topic}")
            logger.info(f"Message Value: {msg.value}")
            logger.info(f"Message key: {msg.key}")

            protobuf_order = order_pb2.OrderModel()
            protobuf_order.ParseFromString(msg.value)
            logger.info(f"Consumed Order Data: {protobuf_order}")

            operation = msg.key.decode('utf-8')
            logger.info(f"Operation: {operation}")

            await process_message(protobuf_order, operation)
    except KafkaError as e:
        logger.error(f"Error while consuming message: {e}")
    finally:
        logger.info("Stopping consumer")
        await consumer.stop()
