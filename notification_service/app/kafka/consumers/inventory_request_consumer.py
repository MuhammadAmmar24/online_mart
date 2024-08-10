import logging
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError, KafkaError
from fastapi import HTTPException
from app.kafka.producers.inventory_response_producer import produce_message_to_inventory_response
from app.crud.inventory_crud import get_inventory_item_by_product_id, update_quantity
from app.protobuf.order_proto import order_pb2
from app.deps import get_session
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_RETRIES = 5
RETRY_INTERVAL = 10  # seconds

async def validate_and_calculate(product_id: int, quantity: int):
    logger.info(f"Validating product ID: {product_id} and quantity: {quantity}")
    
    try:
        with next(get_session()) as session:
            product =  get_inventory_item_by_product_id(product_id, session)
            logger.info(f"Queried Product: {product}")
            
            if not product:
                logger.error(f"Invalid product ID: {product_id}")
                return None, "Invalid product ID"

            if product.quantity < quantity:
                logger.error(f"Insufficient stock for product ID: {product_id}")
                return None, "Insufficient stock"

            # Calculate total amount and decrease inventory quantity
            total_amount = product.unit_price * quantity

            logger.info('Updating Invnetory Quantity')
            update_quantity(product_id, quantity, session, increase=False)

            logger.info(f"Total amount calculated: {total_amount}")
            logger.info(f"Decreased inventory quantity by {quantity}, new quantity: {product.quantity}")

            return total_amount, None
    except Exception as e:
        logger.error(f"Error during validation and calculation: {e}")
        return None, str(e)


async def cancel_order(protobuf_order):
    try:
        with next(get_session()) as session:
            update_quantity(protobuf_order.product_id, protobuf_order.quantity, session, increase=True)
            logger.info(f"Reallocated {protobuf_order.quantity} units back to inventory for product ID: {protobuf_order.product_id}")
    except Exception as e:
        logger.error(f"Error while canceling order: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    




async def process_order_request(protobuf_order):
    logger.info(f"Processing order request for order: {protobuf_order}")

    try:
        if protobuf_order.status == "cancelled":
            await cancel_order(protobuf_order)
        else:
            total_amount, error_message = await validate_and_calculate(protobuf_order.product_id, protobuf_order.quantity)
            if error_message:
                protobuf_order.status = f"{error_message} for product ID: {protobuf_order.product_id}"
                await produce_message_to_inventory_response(protobuf_order, 'invalid')
                return

            protobuf_order.total_amount = total_amount
            protobuf_order.status = "Order processed successfully"
            await produce_message_to_inventory_response(protobuf_order, 'validated')
    except HTTPException as e:
        logger.error(f"HTTPException: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def consume_inventory_request(topic, bootstrap_servers, group_id):
    retries = 0

    while retries < MAX_RETRIES:
        try:
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                auto_offset_reset='earliest',
            )

            logger.info("Inventory Request Consumer created, attempting to start...")
            await consumer.start()
            logger.info("Inventory Request Consumer started successfully")
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

            await process_order_request(protobuf_order)
    except KafkaError as e:
        logger.error(f"Error while consuming inventory request message: {e}")
    finally:
        logger.info("Stopping inventory request consumer")
        await consumer.stop()
