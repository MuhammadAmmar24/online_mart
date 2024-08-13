import logging
from aiokafka import AIOKafkaProducer
from app.protobuf import user_pb2
from app.models.user_model import UserModel

from app import settings

logger = logging.getLogger(__name__)

async def produce_message_to_notification(user_email, user_full_name, key: str):

    logger.info(f"Producing notification message for notification: {user_full_name} email: {user_email}")

    producer = AIOKafkaProducer(bootstrap_servers=settings.BOOTSTRAP_SERVER)
    await producer.start()
    try:
        protobuf_user = user_pb2.UserModel(
            email=user_email,
            full_name=user_full_name,
        )

        serialized_protobuf_user = protobuf_user.SerializeToString()
        
        await producer.send_and_wait(
            topic=settings.KAFKA_NOTIFICATION_TOPIC,
            value=serialized_protobuf_user,
            key=key.encode('utf-8'),
        )
        logger.info(f"Notification message produced successfully")
    except Exception as e:
        logger.error(f"Failed to produce notification message: {str(e)}")
        raise RuntimeError(f"Failed to produce notification message: {str(e)}")
    finally:
        await producer.stop()