import logging
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError, KafkaError
from app.models.payment_model import Payment
from app.crud.payment_crud import create_payment, update_payment,get_payment_by_order_id
from app.deps import get_session
from app.protobuf.order_proto import order_pb2
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_RETRIES = 5
RETRY_INTERVAL = 10  # seconds

async def process_payment_request(protobuf_order):
    logger.info(f"Processing payment request for order: {protobuf_order}")

    try:
        with next(get_session()) as session:  # Use async with context manager
            payment = Payment(
                order_id=protobuf_order.id,
                user_id=protobuf_order.user_id,
                amount=protobuf_order.total_amount,
                status=protobuf_order.status
            )

            if protobuf_order.status == "cancelled":
                payment.status = "cancelled"
                db_payment = get_payment_by_order_id(protobuf_order.id, session)
                logger.info(f"Payment Id {db_payment.id} marked as cancelled, cancelling payment")
                db_cancel_payment = update_payment(payment_id=db_payment.id, payment_data=Payment(**payment.dict()), session=session)
                logger.info(f"DB Cancelled Payment: {db_cancel_payment}")
            else:
                db_insert_payment = create_payment(payment, session)
                logger.info(f"DB Inserted Payment: {db_insert_payment}")

    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        raise

async def consume_payment_requests(topic, bootstrap_servers, group_id):
    logger.info("Starting Payment Request Consumer...")
    retries = 0

    while retries < MAX_RETRIES:
        try:
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                auto_offset_reset='earliest',
            )
            logger.info(f"topic = {topic}, bootstrap_servers = {bootstrap_servers}, group_id = {group_id}")
            logger.info("Payment Request Consumer created, attempting to start...")
            await consumer.start()
            logger.info("Payment Request Consumer started successfully")
            break
        except KafkaConnectionError as e:
            retries += 1
            logger.error(f"Kafka connection error: {e}")
            logger.info(f"Retrying {retries}/{MAX_RETRIES}...")
            await asyncio.sleep(RETRY_INTERVAL)
    else:
        logger.error("Failed to connect to Kafka broker after several retries")
        return

    logger.info("Starting to consume messages...")
    try:
        async for msg in consumer:
            logger.info("Consuming message...")
            logger.info(f"Received message on topic: {msg.topic}")
            logger.info(f"Message Value: {msg.value}")

            protobuf_order = order_pb2.OrderModel()
            protobuf_order.ParseFromString(msg.value)

            logger.info(f"Consumed Order Data: {protobuf_order}")

            await process_payment_request(protobuf_order)
    

    except KafkaError as e:
        logger.error(f"Error while consuming messsge: {e}")
    finally:
        logger.info("Stopping consumer")
        await consumer.stop()
