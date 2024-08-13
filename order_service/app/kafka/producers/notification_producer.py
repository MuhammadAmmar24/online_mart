import logging
from aiokafka import AIOKafkaProducer
from app.models.order_model import OrderModel
from app.protobuf.order_proto import order_pb2

from app import settings

logger = logging.getLogger(__name__)

async def produce_message_to_notification(order: OrderModel, key: str):

    logger.info(f"Producing notification message for order: {order} ")

    producer = AIOKafkaProducer(bootstrap_servers=settings.BOOTSTRAP_SERVER)
    await producer.start()
    try:
        protobuf_order = order_pb2.OrderModel(
        id=order.id,
        user_id=order.user_id,
        product_id=order.product_id,
        quantity=order.quantity,
        total_amount=order.total_amount,
        status=order.status
    )
        serialized_order = protobuf_order.SerializeToString()
        
        await producer.send_and_wait(
            topic=settings.KAFKA_NOTIFICATION_TOPIC,
            value=serialized_order,
            key=key.encode('utf-8'),
        )

        logger.info(f"Notification message produced successfully")
    except Exception as e:
        logger.error(f"Failed to produce notification message: {str(e)}")
        raise RuntimeError(f"Failed to produce notification message: {str(e)}")
    finally:
        await producer.stop()