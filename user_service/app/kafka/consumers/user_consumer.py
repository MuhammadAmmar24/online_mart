import logging
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError, KafkaError
from fastapi import HTTPException
import asyncio
from app.deps import get_session
from app.models.user_model import UserModel, UserUpdate
from app.crud.user_crud import add_user, update_user, delete_user_by_id, get_user_by_id
from app.kafka.producers.notification_producer import produce_message_to_notification
from app.protobuf import user_pb2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_RETRIES = 5
RETRY_INTERVAL = 10  # seconds

async def process_message(protobuf_user: user_pb2.UserModel, operation: str):
    try:
        sqlmodel_user = UserModel(
            user_id=protobuf_user.user_id,
            email=protobuf_user.email,
            password=protobuf_user.password,
            full_name=protobuf_user.full_name,
            address=protobuf_user.address,
        )

        logger.info(f"Converted SQLModel User Data: {sqlmodel_user}")

        if operation == "create":
            with next(get_session()) as session:
                db_insert_user = add_user(sqlmodel_user, session=session)
                logger.info(f"DB Inserted User: {db_insert_user}")

            await produce_message_to_notification(sqlmodel_user.email,sqlmodel_user.full_name, 'user-create')
            logger.info(f"Notification message produced for User: {db_insert_user}")

        elif operation == "update":
            with next(get_session()) as session:
                db_update_user = update_user(
                sqlmodel_user.user_id, UserUpdate(**sqlmodel_user.dict()), session=session)
                logger.info(f"DB Updated User: {db_update_user}")
            
            await produce_message_to_notification(sqlmodel_user.email,sqlmodel_user.full_name, 'user-update')
            logger.info(f"Notification message produced for User: {db_update_user}")

        elif operation == "delete":
            with next(get_session()) as session:
                db_delete_user = delete_user_by_id(sqlmodel_user.user_id, session=session)
                logger.info(f"DB Deleted User: {db_delete_user}")
        
            await produce_message_to_notification(sqlmodel_user.email,sqlmodel_user.full_name, 'user-delete')
            logger.info(f"Notification message produced for User: {db_delete_user}")


    except HTTPException as e:
        logger.error(f"HTTPException: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def consume_users(topic, bootstrap_servers, group_id):
    retries = 0

    while retries < MAX_RETRIES:
        try:
            consumer = AIOKafkaConsumer(
                topic, 
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                auto_offset_reset='earliest',
            )

            logger.info("Consumer created, attempting to start...")
            await consumer.start()
            logger.info("Consumer started successfully")
            break
        except KafkaConnectionError as e:
            retries += 1
            logger.error(f"Kafka connection error: {e}")
            logger.info(f"Retrying {retries}/{MAX_RETRIES}...")
            await asyncio.sleep(RETRY_INTERVAL)
        except KafkaError as e:
            retries += 1
            logger.error(f"Kafka error: {e}")
            logger.info(f"Retrying {retries}/{MAX_RETRIES}...")
            await asyncio.sleep(RETRY_INTERVAL)

    if retries == MAX_RETRIES:
        logger.error(f"Max retries ({MAX_RETRIES}) reached. Consumer failed to start.")
        return

    try:
        logger.info("Starting user consumption loop")
        async for message in consumer:
            protobuf_user = user_pb2.UserModel()
            protobuf_user.ParseFromString(message.value)
            logger.info(f"Received User Message from Kafka: {protobuf_user}")
            logger.info(f"Received User Operation Key from Kafka: {message.key}")

            operation = message.key.decode('utf-8')
            logger.info(f"User operation: {operation}")

            await process_message(protobuf_user, operation)
            await consumer.commit()

    except Exception as e:
        logger.error(f"Failed during consumption: {str(e)}")
        raise RuntimeError(f"Failed during consumption: {str(e)}")
    finally:
        try:
            await consumer.stop()
        except Exception as e:
            logger.error(f"Failed to stop consumer: {str(e)}")