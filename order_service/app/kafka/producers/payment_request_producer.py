import logging
from aiokafka import AIOKafkaProducer
from app.protobuf.order_proto import order_pb2
from app.models.order_model import OrderModel
from app import settings

logger = logging.getLogger(__name__)

async def produce_message_to_payment(order):
    logger.info(f"Producing payment message for order: {order}")
    producer = AIOKafkaProducer(bootstrap_servers=settings.BOOTSTRAP_SERVER)
    await producer.start()
    try:
        request = order_pb2.OrderModel(
            id=order.id,
            user_id=order.user_id,
            product_id=order.product_id,
            quantity=order.quantity,
            total_amount=order.total_amount,
            status=order.status
        )
        serialized_request = request.SerializeToString()
        await producer.send_and_wait(
            topic=settings.KAFKA_PAYMENT_REQUEST_TOPIC, 
            value=serialized_request, 
            key=b'payment reque st'
        )
        logger.info(f"Payment request message produced for order: {order}")
    except Exception as e:
        logger.error(f"Failed to produce payment request message: {str(e)}")
        raise RuntimeError(f"Failed to produce payment request message: {str(e)}")
    finally:
        await producer.stop()
