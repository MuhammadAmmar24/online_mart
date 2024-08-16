import logging
from aiokafka import AIOKafkaProducer
from app.protobuf.order_proto import order_pb2
from app.models.order_model import OrderModel
from app import settings

logger = logging.getLogger(__name__)

async def produce_message_to_user(order: OrderModel, producer: AIOKafkaProducer):
    
    logger.info(f"Producing user validation message for order: {order}")

    try:
        request = order_pb2.OrderModel(
            id=order.id,
            user_id=order.user_id,
            user_email=order.user_email,
            user_full_name=order.user_full_name,
            user_address=order.user_address,
            product_id=order.product_id,
            quantity=order.quantity,
            total_amount=order.total_amount,
            product_title=order.product_title,
            product_description=order.product_description,
            product_category=order.product_category,
            product_brand=order.product_brand,
            status=order.status
        )
        serialized_request = request.SerializeToString()
        await producer.send_and_wait(
            topic=settings.KAFKA_USER_REQUEST_TOPIC, 
            value=serialized_request, 
            key=b'validate_user'
        )
        logger.info(f"User validation message produced for order: {order}")
    except Exception as e:
        logger.error(f"Failed to produce user validation message: {str(e)}")
        raise RuntimeError(f"Failed to produce user validation message: {str(e)}")
