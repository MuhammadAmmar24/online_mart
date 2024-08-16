import logging
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError, KafkaError
from fastapi import HTTPException
from app.deps import get_session
import asyncio
from app.crud.user_crud import validate_id
from app.protobuf.order_proto import order_pb2
from app.kafka.producers.user_response_producer import produce_message_to_user_response

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_RETRIES = 5
RETRY_INTERVAL = 10  # seconds

async def process_order_request(protobuf_order):
    logger.info(f"Processing order request for order: {protobuf_order}")

    try:
        with next(get_session()) as session:
            user = validate_id(protobuf_order.user_id, session=session)
        if user is None:
            logger.error(f"User with ID {protobuf_order.user_id} not found")
            await produce_message_to_user_response(protobuf_order, validation="invalid")
        else:
            logger.info(f"User found: {user}")

            protobuf_order.user_id = user.user_id
            protobuf_order.user_email = user.email
            protobuf_order.user_full_name = user.full_name
            protobuf_order.user_address = user.address

                # Send the user object to the `produce_message_to_user_response` topic
            await produce_message_to_user_response(protobuf_order, validation="validated")
            logger.info(f"Produced message to user_response topic for user ID {user.user_id}")

    except HTTPException as e:
        logger.error(f"HTTPException: {e.detail}")
        raise
    except KafkaError as e:
        logger.error(f"KafkaError while producing message: {str(e)}")
        raise HTTPException(status_code=500, detail="Kafka Error occurred")
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def consume_user_request(topic, bootstrap_servers, group_id):
    retries = 0

    while retries < MAX_RETRIES:
        try:
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                auto_offset_reset='earliest',
            )

            logger.info("User Request Consumer created, attempting to start...")
            await consumer.start()
            logger.info("User Request Consumer started successfully")
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
        logger.error(f"Error while consuming user request message: {e}")
    finally:
        logger.info("Stopping user request consumer")
        await consumer.stop()
