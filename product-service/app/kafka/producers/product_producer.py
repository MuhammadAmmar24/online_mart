import logging
from app.protobuf.product_proto import product_pb2
from aiokafka import AIOKafkaProducer
from app import settings

logger = logging.getLogger(__name__)

async def produce_message(product, producer: AIOKafkaProducer, operation: str):
    
    try:
        protobuf_product = product_pb2.Product(
            id=product.id,
            title=product.title,
            description=product.description,
            category=product.category,
            price=product.price,
            quantity=product.quantity,
            brand=product.brand,
        )

        serialized_product = protobuf_product.SerializeToString()
        
        operation_bytes = operation.encode('utf-8')  # Convert operation to bytes
        logger.info(f"operation_bytes: {operation_bytes}")

        await producer.send_and_wait(topic=settings.KAFKA_PRODUCT_TOPIC, value=serialized_product, key=operation_bytes)
        logger.info(f"Message produced successfully: {protobuf_product}")
    except Exception as e:
        logger.error(f"Failed to produce message: {str(e)}")
        raise RuntimeError(f"Failed to produce message: {str(e)}")
