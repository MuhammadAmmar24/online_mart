import logging
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError, KafkaError
from fastapi import HTTPException
from app.models.inventory_model import Product, ProductUpdate
from app.crud.inventory_crud import add_product, update_product, delete_product_by_id
from app.deps import get_session
from app.protobuf import product_pb2
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_RETRIES = 5
RETRY_INTERVAL = 10  # seconds

async def process_message(protobuf_product: product_pb2.Product, operation: str):
    try:
        sqlmodel_product = Product(
            id=protobuf_product.id,
            title=protobuf_product.title,
            description=protobuf_product.description,
            category=protobuf_product.category,
            price=protobuf_product.price,
            discount=protobuf_product.discount,
            quantity=protobuf_product.quantity,
            brand=protobuf_product.brand,
            weight=protobuf_product.weight,
            expiry=protobuf_product.expiry,
        )

        logger.info(f"Converted SQLModel Product Data: {sqlmodel_product}")

        with next(get_session()) as session:
            if operation == "create":
                db_insert_product = add_product(sqlmodel_product, session=session)
                logger.info(f"DB Inserted Product: {db_insert_product}")

            elif operation == "update":
                db_update_product = update_product(
                    sqlmodel_product.id, ProductUpdate(**sqlmodel_product.dict()), session=session)
                logger.info(f"DB Updated Product: {db_update_product}")

            elif operation == "delete":
                db_delete_product = delete_product_by_id(sqlmodel_product.id, session=session)
                logger.info(f"DB Deleted Product: {db_delete_product}")

    except HTTPException as e:
        logger.error(f"HTTPException: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def consume_inventory_items(topic, bootstrap_servers, group_id):
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

            protobuf_product = product_pb2.Product()
            protobuf_product.ParseFromString(msg.value)
            logger.info(f"Consumed Product Data: {protobuf_product}")

            operation = msg.key.decode('utf-8')  # Decode the operation key
            logger.info(f"Operation: {operation}")

            await process_message(protobuf_product, operation)
    except KafkaError as e:
        logger.error(f"Error while consuming message: {e}")
    finally:
        logger.info("Stopping consumer")
        await consumer.stop()
