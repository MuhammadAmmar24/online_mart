import logging
from app.protobuf import product_pb2
from aiokafka import AIOKafkaProducer

from app import settings

logger = logging.getLogger(__name__)

async def produce_message(product, operation_type, producer: AIOKafkaProducer):
    try:
        protobuf_product = product_pb2.Product(
            id=product.id,
            title=product.title,
            description=product.description,
            category=product.category,
            price=product.price,
            discount=product.discount,
            quantity=product.quantity,
            brand=product.brand,
            weight=product.weight,
            expiry=product.expiry,
            operation=operation_type
        )

        serialized_product = protobuf_product.SerializeToString()
        await producer.send_and_wait(settings.KAFKA_PRODUCT_TOPIC, serialized_product)
        logger.info(f"Message produced successfully: {protobuf_product}")
    except Exception as e:
        logger.error(f"Failed to produce message: {str(e)}")
        raise
