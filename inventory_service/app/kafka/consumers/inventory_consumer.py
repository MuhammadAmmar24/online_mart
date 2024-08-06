import logging
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError, KafkaError
from fastapi import HTTPException
from app.models.inventory_model import InventoryItem, InventoryItemUpdate, InventoryStatus
from app.crud.inventory_crud import add_inventory_item, update_inventory_item, delete_inventory_item_by_id, get_inventory_item_by_product_id
from app.deps import get_session
from app.protobuf import product_pb2
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_RETRIES = 5
RETRY_INTERVAL = 10  # seconds

async def process_message(protobuf_product_item: product_pb2.Product, operation: str):
    
    try:
        with next(get_session()) as session:

            inventory_item = get_inventory_item_by_product_id(protobuf_product_item.id, session)

            if operation == "create":
                if inventory_item:
                    logger.info(f"Inventory item already exists for product_id {protobuf_product_item.id}")
                else:
                    new_inventory_item = InventoryItem(
                        product_id=protobuf_product_item.id,
                        quantity=protobuf_product_item.quantity,
                        status=InventoryStatus.IN_STOCK if protobuf_product_item.quantity > 0 else InventoryStatus.OUT_OF_STOCK
                    )
                    db_insert_inventory_item = add_inventory_item(new_inventory_item, session=session)
                    logger.info(f"DB Inserted Inventory Item: {db_insert_inventory_item}")

            elif operation == "update":
                if inventory_item:
                    update_data = InventoryItemUpdate(
                        quantity=protobuf_product_item.quantity,
                        status=InventoryStatus.IN_STOCK if protobuf_product_item.quantity > 0 else InventoryStatus.OUT_OF_STOCK
                    )
                    db_update_inventory_item = update_inventory_item(
                        inventory_item.id, update_data, session=session
                    )
                    logger.info(f"DB Updated Inventory Item: {db_update_inventory_item}")
                else:
                    logger.error(f"Inventory item not found for product_id {protobuf_product_item.id}")

            elif operation == "delete":
                if inventory_item:
                    db_delete_inventory_item = delete_inventory_item_by_id(inventory_item.id, session=session)
                    logger.info(f"DB Deleted Inventory Item: {db_delete_inventory_item}")
                else:
                    logger.error(f"Inventory item not found for product_id {protobuf_product_item.id}")

    except HTTPException as e:
        logger.error(f"HTTPException: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def consume_product_updates(topic, bootstrap_servers, group_id):
    retries = 0

    while retries < MAX_RETRIES:
        try:
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                auto_offset_reset='earliest',
            )

            logger.info("Inventory Consumer created, attempting to start...")
            await consumer.start()
            logger.info("Inventory Consumer started successfully")
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

            protobuf_product_item = product_pb2.Product()
            protobuf_product_item.ParseFromString(msg.value)
            logger.info(f"Consumed Product Data: {protobuf_product_item}")

            operation = msg.key.decode('utf-8')  # Decode the operation key
            logger.info(f"Operation: {operation}")

            await process_message(protobuf_product_item, operation)
    except KafkaError as e:
        logger.error(f"Error while consuming message: {e}")
    finally:
        logger.info("Stopping Inventory Consumer")
        await consumer.stop()
