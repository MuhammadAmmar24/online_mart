import logging
from aiokafka import AIOKafkaProducer
from app.protobuf.order_proto import order_pb2
from app.models.order_model import OrderModel
from app import settings

logger = logging.getLogger(__name__)

async def produce_message_to_inventory(order, producer: AIOKafkaProducer):
    
    logger.info(f"Producing inventory check message for order: {order}")
    try:
        request = order_pb2.OrderModel(
            id=order.id,
            user_id=order.user_id,
            product_id=order.product_id,
            quantity=order.quantity,
            status=order.status
        )
        serialized_request = request.SerializeToString()
        await producer.send_and_wait(
            topic=settings.KAFKA_INVENTORY_REQUEST_TOPIC, 
            value=serialized_request, 
            key=b'check_inventory'
        )
        logger.info(f"Inventory check message produced for order: {order}")
    except Exception as e:
        logger.error(f"Failed to produce inventory check message: {str(e)}")
        raise RuntimeError(f"Failed to produce inventory check message: {str(e)}")
