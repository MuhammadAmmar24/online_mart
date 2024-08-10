import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, SQLModel
from typing import Annotated, AsyncGenerator
from aiokafka import AIOKafkaProducer
import asyncio

from app import settings
from app.db_engine import engine
from app.deps import get_session, kafka_producer
from app.models.user_model import UserModel, UserUpdate
from app.crud.user_crud import get_all_users, get_user_by_id, validate_id
from app.kafka.producers.user_producer import produce_message
from app.kafka.consumers.user_consumer import consume_users

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables created successfully")

@asynccontextmanager
async def lifespan(app: FastAPI)-> AsyncGenerator[None, None]:
    logger.info("User Service Starting...")
    create_db_and_tables()
    task = asyncio.create_task(consume_users(
        settings.KAFKA_USER_TOPIC, 
        settings.BOOTSTRAP_SERVER, 
        settings.KAFKA_CONSUMER_GROUP_ID_FOR_USER
        ))
 

    yield
    logger.info("User Service Closing...")

app = FastAPI(
    lifespan=lifespan,
    title="User Service",
    version="0.0.1",
)

@app.get('/')
def start():
    return {"message": "User Service"}

@app.post('/user', response_model=UserModel)
async def call_add_user(
    user: UserModel, 
    session: Annotated[Session, Depends(get_session)], 
    producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]):

    existing_user = validate_id(user.user_id, session)

    if existing_user:
        raise HTTPException(status_code=400, detail=f"User with ID {user.user_id} already exists")
    
    await produce_message(user, producer, "create")

    return user

@app.get('/user/all', response_model=list[UserModel])
def call_get_all_users(session: Annotated[Session, Depends(get_session)]):
    return get_all_users(session)

@app.get('/user/{id}', response_model=UserModel)
def call_get_user_by_id(id: int, session: Annotated[Session, Depends(get_session)]):
    return get_user_by_id(id=id, session=session)

@app.patch('/user/{id}', response_model=UserModel)
async def call_update_user(id: int, user: UserUpdate, session: Annotated[Session, Depends(get_session)],producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]):

    call_get_user_by_id(id, session)
    updated_user = UserModel(id=id, **user.dict())
    await produce_message(updated_user, producer, "update")
    
    return updated_user

@app.delete('/user/{id}', response_model=dict)
async def call_delete_user_by_id(id: int, session: Annotated[Session, Depends(get_session)],producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]):

    call_get_user_by_id(id, session)
    await produce_message(UserModel(id=id), producer, "delete")

    return {"deleted_id": id}