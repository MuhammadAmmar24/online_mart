import logging
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError, KafkaError
import asyncio
from app.deps import get_session
from app import settings
from app.models.notification_model import Notification
from app.crud.notification_crud import add_notification, update_notification_status
from app.protobuf.user_proto import user_pb2
from app.protobuf.order_proto import order_pb2
from app.models.user_model import UserModel
from app.email.email_sender.email_sender import send_email
from app.email.templates.user_email_templates import account_creation_email, account_update_email, account_deletion_email


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_RETRIES = 5
RETRY_INTERVAL = 10  # seconds


async def process_user_notification_request(protobuf_user, message_type):
    logger.info(f"Processing notification request: {protobuf_user}")

    try:
        sqlmodel_user = UserModel(
            email=protobuf_user.email,
            full_name=protobuf_user.full_name,
        )

        logger.info(f"Converted SQLModel User Data: {sqlmodel_user}")
        
        with next(get_session()) as session:
            if message_type == "user-create":
                subject, message = account_creation_email(sqlmodel_user.full_name)
            elif message_type == "user-update":
                subject, message = account_update_email(sqlmodel_user.full_name)
            elif message_type == "user-delete":
                subject, message = account_deletion_email(sqlmodel_user.full_name)
            else:
                return  # In case of unknown message_type

            notification = Notification(
                email=sqlmodel_user.email,
                subject=subject,
                message=message,
                status="Pending"
            )

            db_notification = add_notification(notification, session=session)
            email_sent = send_email(notification.email, notification.subject, notification.message)
            3
            new_status = "Sent" if email_sent else "Failed"
            update_notification_status(db_notification.id, new_status, session=session)
                
    except Exception as e:
        logger.error(f"Exception while processing notification: {str(e)}")
        raise



async def process_order_notification_request(protobuf_message, message_type):
    logger.info(f"Processing notification request: {protobuf_message} of type {message_type}")

    


    # try:
    #     with next(get_session()) as session:
    #         notification = Notification(
    #             email=protobuf_message.email,
    #             subject=protobuf_message.subject,
    #             message=protobuf_message.message,
    #             status="Pending"
    #         )
    #         db_notification = add_notification(notification, session=session)
    #         email_sent = send_email(notification.email, notification.subject, notification.message)
            
    #         new_status = "Sent" if email_sent else "Failed"
    #         update_notification_status(db_notification.id, new_status, session=session)
    # except Exception as e:
    #     logger.error(f"Exception while processing notification: {str(e)}")
    #     raise



async def consume_notification(topic, bootstrap_servers, group_id):
    retries = 0

    while retries < MAX_RETRIES:
        try:
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                auto_offset_reset='earliest',
            )

            logger.info("Notification Request Consumer created, attempting to start...")
            await consumer.start()
            logger.info("Notification Request Consumer started successfully")
            break
        except KafkaConnectionError as e:
            retries += 1
            logger.error(f"Kafka connection error: {e}")
            logger.info(f"Retrying {retries}/{MAX_RETRIES}...")
            await asyncio.sleep(RETRY_INTERVAL)
    else:
        logger.error("Failed to connect to Kafka broker after several retries")
        return

    try:
        async for msg in consumer:
            logger.info(f"Received message on topic: {msg.topic}")
            logger.info(f"Message Value: {msg.value}")
            logger.info(f"Message Key: {msg.key}")

            message_type = msg.key.decode('utf-8')  
            logger.info(f"Message Type: {message_type}")

            if message_type in ['user-create', 'user-update', 'user-delete']:

                protobuf_user = user_pb2.UserModel()
                protobuf_user.ParseFromString(msg.value)
                logger.info(f"Received User Message from Kafka: {protobuf_user}")

                logger.info(f"Consumed User Notification Request Data: {protobuf_user}")
                await process_user_notification_request(protobuf_user, message_type)
            
            if message_type  in ['order-create', 'order-update', 'order-cancelled']:
                protobuf_order = order_pb2.OrderModel()
                protobuf_order.ParseFromString(msg.value)
                logger.info(f"Received User Message from Kafka: {protobuf_order}")

                logger.info(f"Consumed User Notification Request Data: {protobuf_order}")
                await process_order_notification_request(protobuf_order, message_type)

    except KafkaError as e:
        logger.error(f"Error while consuming message: {e}")
    finally:
        logger.info("Stopping consumer")
        await consumer.stop()