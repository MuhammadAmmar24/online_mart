import logging
from aiokafka import AIOKafkaProducer
from app.protobuf.order_proto import order_pb2
from app import settings

logger = logging.getLogger(__name__)

async def produce_message_to_inventory_response(order, validation: str):

    logger.info(f"Producing inventory response message for order: {order}")
    producer = AIOKafkaProducer(bootstrap_servers=settings.BOOTSTRAP_SERVER)
    await producer.start()

    try:
        response = order_pb2.OrderModel(
            id=order.id,
            user_id=order.user_id,
            product_id=order.product_id,
            quantity=order.quantity,
            total_amount=order.total_amount,
            status=order.status,
        )
        serialized_response = response.SerializeToString()

        logger.info(f"Producing inventory response message for order serialized response: {serialized_response}")
        await producer.send_and_wait(
            topic=settings.KAFKA_INVENTORY_RESPONSE_TOPIC, 
            value=serialized_response, 
            key=validation.encode('utf-8'),
        )
        logger.info(f"Inventory response message produced for order: {order.id}")
    except Exception as e:
        logger.error(f"Failed to produce inventory response message: {str(e)}")
        raise RuntimeError(f"Failed to produce inventory response message: {str(e)}")
    finally:
        await producer.stop()
