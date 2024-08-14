import logging
from aiokafka import AIOKafkaProducer
from app.protobuf.order_proto import order_pb2
from app import settings

logger = logging.getLogger(__name__)

async def produce_message_to_product_response(order, validation: str):

    logger.info(f"Producing product response message for order: {order}")
    producer = AIOKafkaProducer(bootstrap_servers=settings.BOOTSTRAP_SERVER)
    await producer.start()

    try:

        response = order_pb2.OrderModel(
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

        serialized_order = response.SerializeToString()

        logger.info(f"Producing product response message for order serialized response: {serialized_order}")
        await producer.send_and_wait(
            topic=settings.KAFKA_PRODUCT_RESPONSE_TOPIC, 
            value=serialized_order, 
            key=validation.encode('utf-8'),
        )
        logger.info(f"Product response message produced for order: {order.id}")
    except Exception as e:
        logger.error(f"Failed to produce product response message: {str(e)}")
        raise RuntimeError(f"Failed to produce product response message: {str(e)}")
    finally:
        await producer.stop()
