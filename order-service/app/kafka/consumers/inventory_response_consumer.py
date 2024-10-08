import logging
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError, KafkaError
from fastapi import HTTPException
from app.deps import get_session, kafka_producer
from app.models.order_model import OrderModel
from app.crud.order_crud import add_order, update_order, get_order_by_id
from app.kafka.producers.payment_request_producer import produce_message_to_payment
from app.kafka.producers.notification_producer import produce_message_to_notification
from app.protobuf.order_proto import order_pb2
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_RETRIES = 5
RETRY_INTERVAL = 10  # seconds

async def process_inventory_response(protobuf_response, validation):
    logger.info(f"Processing inventory response for order: {protobuf_response}")

    try:
        if validation == 'validated':
            order = OrderModel(
            id=protobuf_response.id,
            user_id=protobuf_response.user_id,
            user_email=protobuf_response.user_email,
            user_full_name=protobuf_response.user_full_name,
            user_address=protobuf_response.user_address,
            product_id=protobuf_response.product_id,
            quantity=protobuf_response.quantity,
            total_amount=protobuf_response.total_amount,
            product_title=protobuf_response.product_title,
            product_description=protobuf_response.product_description,
            product_category=protobuf_response.product_category,
            product_brand=protobuf_response.product_brand,
            status='Pending'
            )
            with next(get_session()) as session:
                existing_order = get_order_by_id(order.id, session)
            if existing_order is None:
                with next(get_session()) as session:
                    db_insert_order = add_order(order, session=session)
                    logger.info(f"DB Inserted Order: {db_insert_order}")

                await produce_message_to_payment(order)
                await produce_message_to_notification(order, 'order-create')

            else:
                with next(get_session()) as session:
                    db_update_order = update_order(order.id, order, session=session)
                    logger.info(f"DB Updated Order: {db_update_order}")
                await produce_message_to_notification(order, 'order-update')
        else:
            logger.info(f"Order ID {protobuf_response.id} marked as invalid: {validation}")

    except HTTPException as e:
        logger.error(f"HTTPException: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def consume_inventory_response(topic, bootstrap_servers, group_id):
    retries = 0

    while retries < MAX_RETRIES:
        try:
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                auto_offset_reset='earliest',
            )

            logger.info("Inventory Response Consumer created, attempting to start...")
            await consumer.start()
            logger.info("Inventory Response Consumer started successfully")
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
            logger.info(f"Message Key: {msg.key}")

            protobuf_response = order_pb2.OrderModel()
            protobuf_response.ParseFromString(msg.value)

            validation = msg.key.decode('utf-8')  # Decode the validation key
            logger.info(f"Validation: {validation}")

            logger.info(f"Consumed Inventory Response Data: {protobuf_response}")

            await process_inventory_response(protobuf_response, validation)

    except KafkaError as e:
        logger.error(f"Error while consuming message: {e}")
    finally:
        logger.info("Stopping consumer")
        await consumer.stop()
