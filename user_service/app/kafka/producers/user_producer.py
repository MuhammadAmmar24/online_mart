import logging
from app.protobuf import user_pb2
from aiokafka import AIOKafkaProducer
from app import settings

logger = logging.getLogger(__name__)

async def produce_message(user, producer: AIOKafkaProducer, operation: str):
    try:
        protobuf_user = user_pb2.UserModel(
            user_id=user.user_id,
            email=user.email,
            password=user.password,
            full_name=user.full_name,
            address=user.address,
        )

        serialized_user = protobuf_user.SerializeToString()
        
        operation_bytes = operation.encode('utf-8')  # Convert operation to bytes
        logger.info(f"operation_bytes: {operation_bytes}")

        await producer.send_and_wait(topic=settings.KAFKA_USER_TOPIC, value=serialized_user, key=operation_bytes)
        logger.info(f"Message produced successfully: {protobuf_user}")
    except Exception as e:
        logger.error(f"Failed to produce message: {str(e)}")
        raise RuntimeError(f"Failed to produce message: {str(e)}")
