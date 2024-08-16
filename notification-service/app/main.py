import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from sqlmodel import Session, SQLModel
from typing import Annotated, AsyncGenerator
import asyncio


from app import settings
from app.db_engine import engine
from app.deps import get_session, kafka_producer
from app.models.notification_model import Notification
from app.crud.notification_crud import get_all_notifications, get_notification_by_id
from app.kafka.consumers.notification_consumer import consume_notification


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables created successfully")

@asynccontextmanager
async def lifespan(app: FastAPI)-> AsyncGenerator[None, None]:
    logger.info("Notification Service Starting...")
    create_db_and_tables()

    task = asyncio.create_task(consume_notification(
        settings.KAFKA_NOTIFICATION_TOPIC,
        settings.BOOTSTRAP_SERVER, 
        settings.KAFKA_CONSUMER_GROUP_ID_FOR_NOTIFICATION
        ))

    yield
    logger.info("Notification Service Closing...")

app = FastAPI(
    lifespan=lifespan,
    title="Notification Service",
    version="0.0.1",
)

@app.get('/')
def start():
    return {"message": "Notification Service"}

@app.get('/notifications/all', response_model=list[Notification])
def call_get_all_notifications(session: Annotated[Session, Depends(get_session)]):
    return get_all_notifications(session)

@app.get('/inventory/{id}', response_model=Notification)
def call_get_notification_by_id(id: int, session: Annotated[Session, Depends(get_session)]):
    return get_notification_by_id(id=id, session=session)

