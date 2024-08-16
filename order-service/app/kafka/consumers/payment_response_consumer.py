import logging
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError, KafkaError
from fastapi import HTTPException
from app.deps import get_session
from app.models.order_model import OrderModel
from app.crud.order_crud import update_order, get_order_by_id
from app.protobuf.payment_proto import payment_pb2
from app.kafka.producers.notification_producer import produce_message_to_notification
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_RETRIES = 5
RETRY_INTERVAL = 10  # seconds

async def process_payment_response(protobuf_response, status):
    logger.info(f"Processing payment response for order: {protobuf_response}")

    try:
        with next(get_session()) as session:
            order = get_order_by_id(protobuf_response.order_id, session)
        if order:
            if status == "paid":
                with next(get_session()) as session:
                    order_update = OrderModel(status="paid")
                    db_update_order = update_order(order.id, order_update, session=session)
                    logger.info(f"Order status updated to Paid: {db_update_order}")

                logger.info(f"Payment for Order ID {protobuf_response.order_id} is {status}")
                logger.info(f"Producing message to Notification Service for Order ID {protobuf_response.order_id}")
                await produce_message_to_notification(db_update_order, "order-paid")
            else:
                logger.info(f"Payment for Order ID {protobuf_response.order_id} is {status}")
        else:
            logger.error(f"Order ID {protobuf_response.order_id} not found")

    except HTTPException as e:
        logger.error(f"HTTPException: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def consume_payment_response(topic, bootstrap_servers, group_id):
    retries = 0

    while retries < MAX_RETRIES:
        try:
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                auto_offset_reset='earliest',
            )

            logger.info("Payment Response Consumer created, attempting to start...")
            await consumer.start()
            logger.info("Payment Response Consumer started successfully")
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

            protobuf_response = payment_pb2.Payment()
            protobuf_response.ParseFromString(msg.value)

            status = msg.key.decode('utf-8')  # Decode the status key
            logger.info(f"Payment Status: {status}")

            logger.info(f"Consumed Payment Response Data: {protobuf_response}")

            await process_payment_response(protobuf_response, status)

    except KafkaError as e:
        logger.error(f"Error while consuming message: {e}")
    finally:
        logger.info("Stopping consumer")
        await consumer.stop()
